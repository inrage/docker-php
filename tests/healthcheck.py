import os
from pathlib import Path
import subprocess
import tempfile
import time
import uuid

root = Path(__file__).resolve().parent.parent
image = "inrage-health-test:" + uuid.uuid4().hex[:12]
base = os.environ.get("APACHE_TEST_IMAGE", "inrage/docker-php:8.3")
containers = []


def docker(*args, **kwargs):
    return subprocess.run(["docker", *args], text=True, capture_output=True, **kwargs)


def probe(cid):
    return docker("exec", cid, "healthcheck")


def start(*args):
    result = docker("run", "-d", "--platform", "linux/amd64", *args, image, check=True)
    cid = result.stdout.strip()
    containers.append(cid)
    return cid


def ready(cid):
    for _ in range(40):
        if probe(cid).returncode == 0:
            return
        time.sleep(0.25)
    raise AssertionError(docker("logs", cid).stderr)


try:
    build = docker("build", "--platform", "linux/amd64", "-t", image, "-f", "-", str(root), input=f"""FROM {base}
USER root
COPY templates /etc/gotpl/
COPY s6-overlay/scripts/init-templates /etc/s6-overlay/scripts/init-templates
COPY s6-overlay/s6-rc.d/apache/run /etc/s6-overlay/s6-rc.d/apache/run
COPY bin/healthcheck /usr/local/bin/healthcheck
RUN chmod a+rx /usr/local/bin/healthcheck /etc/s6-overlay/scripts/init-templates /etc/s6-overlay/s6-rc.d/apache/run
USER inr
""")
    assert build.returncode == 0, build.stderr
    cid = start()
    ready(cid)
    assert docker("exec", cid, "cat", "/proc/1/comm", check=True).stdout.strip() == "s6-svscan"
    assert docker("exec", cid, "curl", "-fsS", "http://127.0.0.1:9001/ping", check=True).stdout == "pong"
    print("PASS Apache and PHP-FPM respond without an application")

    docker("exec", cid, "/command/s6-svc", "-d", "/run/service/php-fpm", check=True)
    for _ in range(40):
        if probe(cid).returncode != 0:
            break
        time.sleep(0.1)
    else:
        raise AssertionError("Healthcheck accepted a stopped PHP-FPM service")
    tcp = '$s=@fsockopen("127.0.0.1",(int)getenv("APACHE_HTTP_PORT"));exit($s?0:1);'
    assert docker("exec", cid, "php", "-r", tcp).returncode == 0
    print("PASS PHP-FPM failure is detected while Apache still listens")

    docker("exec", cid, "/command/s6-svc", "-u", "/run/service/php-fpm", check=True)
    ready(cid)
    docker("exec", cid, "/command/s6-svc", "-d", "/run/service/apache", check=True)
    for _ in range(40):
        if probe(cid).returncode != 0:
            break
        time.sleep(0.1)
    else:
        raise AssertionError("Healthcheck accepted a stopped Apache service")
    print("PASS Apache failure is detected")

    cid = start("--env", "INRAGE_HEALTH_PORT=9002")
    ready(cid)
    assert docker("exec", cid, "curl", "-fsS", "http://127.0.0.1:9002/ping", check=True).stdout == "pong"
    sockets = docker("exec", cid, "cat", "/proc/net/tcp", check=True).stdout
    assert "0100007F:232A" in sockets and "00000000:232A" not in sockets
    print("PASS configurable listener is restricted to loopback")

    with tempfile.TemporaryDirectory(prefix="inrage-health-init-") as directory:
        hook = Path(directory) / "99-fail.sh"
        hook.write_text("exit 42\n")
        hook.parent.chmod(0o755)
        hook.chmod(0o644)
        cid = start("--volume", f"{hook}:/docker-entrypoint-init.d/99-fail.sh:ro")
        for _ in range(40):
            if "exited 42" in docker("logs", cid).stderr:
                break
            time.sleep(0.1)
        assert probe(cid).returncode != 0
        print("PASS initialization failure is not reported healthy")

    assert docker("run", "--rm", "--platform", "linux/amd64", "--entrypoint", "/bin/sh", image, "-c", "touch /tmp/inrage-command-mode; healthcheck").returncode == 0
    print("PASS command containers do not require a web server")
finally:
    for cid in containers:
        docker("rm", "--force", cid)
    docker("image", "rm", image)
