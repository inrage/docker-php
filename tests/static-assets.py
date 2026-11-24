#!/usr/bin/env python3
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parent.parent
image = os.environ.get("APACHE_TEST_IMAGE", "inrage/docker-php:8.3")
containers = []
results = []


def docker(*args):
    return subprocess.check_output(["docker", *args], text=True).strip()


def start(site, **environment):
    command = [
        "run", "--detach", "--platform", "linux/amd64",
        "--publish", "127.0.0.1::8080",
        "--volume", f"{site}:/var/www/html/public:ro",
        "--volume", f"{root / 'templates/docker-apache-vhost.conf.tmpl'}:/etc/gotpl/docker-apache-vhost.conf.tmpl:ro",
        "--env", "APACHE_VHOST_DIR=/var/www/html/public",
        "--env", "APACHE_HTTP_PORT=8080",
    ]
    for key, value in environment.items():
        command.extend(["--env", f"{key}={value}"])
    cid = docker(*command, image)
    containers.append(cid)
    url = "http://" + docker("port", cid, "8080/tcp")
    for _ in range(60):
        try:
            with urlopen(url + "/style.css", timeout=1) as response:
                if response.status == 200:
                    break
        except (HTTPError, URLError, TimeoutError, ConnectionError):
            time.sleep(0.5)
    else:
        raise AssertionError(docker("logs", cid))
    docker("exec", cid, "apache2ctl", "-t")
    return cid, url


def hits(cid):
    return int(docker("exec", cid, "php", "-r", 'echo is_file("/tmp/php-hits") ? count(file("/tmp/php-hits")) : 0;'))


def check(cid, url, path, status, body, php_hits=0, method="GET"):
    before = hits(cid)
    try:
        response = urlopen(Request(url + path, method=method), timeout=5)
    except HTTPError as error:
        response = error
    content = response.read().decode()
    assert response.status == status, (path, response.status, content)
    if body is not None:
        assert content == body, (path, content)
    if status == 404 and php_hits == 0:
        assert "FRONT_CONTROLLER" not in content and "PHP_ERROR_DOCUMENT" not in content, path
        assert "immutable" not in response.headers.get("Cache-Control", ""), path
    after = hits(cid)
    assert after - before == php_hits, (path, before, after)
    results.append({"path": path, "method": method, "status": status, "php_requests": after - before})


try:
    with tempfile.TemporaryDirectory(prefix="apache-static-assets-") as temporary:
        site = Path(temporary)
        site.chmod(0o755)
        (site / "style.css").write_text("body { color: green; }")
        (site / "app.js").write_text("console.log('static');")
        (site / "photo.webp").write_text("WEBP_CONTENT")
        (site / "font.woff2").write_text("FONT_CONTENT")
        (site / "index.php").write_text('<?php file_put_contents("/tmp/php-hits", "index\\n", FILE_APPEND); echo "FRONT_CONTROLLER";')
        (site / "generator.php").write_text('<?php file_put_contents("/tmp/php-hits", "generator\\n", FILE_APPEND); echo "GENERATED_CSS";')
        (site / "error.php").write_text('<?php file_put_contents("/tmp/php-hits", "error\\n", FILE_APPEND); http_response_code(404); echo "PHP_ERROR_DOCUMENT";')
        (site / ".htaccess").write_text(
            "ErrorDocument 404 /error.php\n"
            "RewriteEngine On\n"
            "RewriteRule ^photo\\.jpg$ photo.webp [L]\n"
            "RewriteRule ^dynamic\\.css$ generator.php [L]\n"
            "RewriteRule ^index\\.php$ - [L]\n"
            "RewriteCond %{REQUEST_FILENAME} !-f\n"
            "RewriteCond %{REQUEST_FILENAME} !-d\n"
            "RewriteRule . /index.php [L]\n"
        )
        (site / "plain").mkdir()
        (site / "plain/.htaccess").write_text("RewriteEngine Off\nErrorDocument 404 /error.php\n")
        cid, url = start(site)
        check(cid, url, "/style.css", 200, "body { color: green; }")
        check(cid, url, "/app.js?ver=1", 200, "console.log('static');")
        check(cid, url, "/font.woff2", 200, "FONT_CONTENT")
        check(cid, url, "/missing.css", 404, None)
        check(cid, url, "/missing.CsS?ver=1", 404, None)
        check(cid, url, "/missing.js", 404, "", method="HEAD")
        check(cid, url, "/sites/default/files/old.jpg", 404, None)
        check(cid, url, "/plain/missing.css", 404, None)
        check(cid, url, "/photo.jpg", 200, "WEBP_CONTENT")
        check(cid, url, "/dynamic.css", 200, "GENERATED_CSS", 1)
        for path in ["/route", "/route?file=missing.css", "/sitemap.xml", "/api.json", "/robots.txt", "/document.pdf", "/favicon.ico", "/wp-json/render/image.png", "/wp-json?file=missing.css"]:
            check(cid, url, path, 200, "FRONT_CONTROLLER", 1)
        check(cid, url, "/missing.css", 200, "FRONT_CONTROLLER", 1, method="POST")
        check(cid, url, "/plain/not-found", 404, "PHP_ERROR_DOCUMENT", 1)
        cid, url = start(site, APACHE_STATIC_404_EXCLUDE="/wp-json(?:/|[? ])|/generated/")
        check(cid, url, "/generated/chart.png", 200, "FRONT_CONTROLLER", 1)
        check(cid, url, "/missing.png", 404, None)
        cid, url = start(site, APACHE_STATIC_404="false")
        check(cid, url, "/missing.css", 200, "FRONT_CONTROLLER", 1)
        check(cid, url, "/plain/missing.css", 404, "PHP_ERROR_DOCUMENT", 1)
    print(json.dumps({"passed": len(results), "results": results}, indent=2))
finally:
    for cid in containers:
        subprocess.run(["docker", "rm", "--force", cid], stdout=subprocess.DEVNULL, check=False)
