#!/usr/bin/env python3
import gzip
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
        "--volume", f"{root / 'templates/docker-apache-compression.conf'}:/etc/apache2/conf-enabled/inrage-compression.conf:ro",
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


def check(cid, url, path, status, body, php_hits=0, method="GET", headers=None, encoding=None):
    before = hits(cid)
    try:
        response = urlopen(Request(url + path, method=method, headers=headers or {}), timeout=5)
    except HTTPError as error:
        response = error
    received = response.read()
    assert response.headers.get("Content-Encoding") == encoding, (path, response.headers)
    content = gzip.decompress(received).decode() if encoding == "gzip" else received.decode()
    if encoding == "gzip":
        assert "Accept-Encoding" in response.headers.get("Vary", ""), path
        assert len(received) < len(content.encode()), path
    assert response.status == status, (path, response.status, content)
    if body is not None:
        assert content == body, (path, content)
    if status == 404 and php_hits == 0:
        assert "FRONT_CONTROLLER" not in content and "PHP_ERROR_DOCUMENT" not in content, path
        assert "immutable" not in response.headers.get("Cache-Control", ""), path
    after = hits(cid)
    assert after - before == php_hits, (path, before, after)
    results.append({"path": path, "method": method, "status": status, "php_requests": after - before, "encoding": encoding, "bytes_received": len(received), "bytes_decoded": len(content.encode())})


try:
    with tempfile.TemporaryDirectory(prefix="apache-static-assets-") as temporary:
        site = Path(temporary)
        site.chmod(0o755)
        (site / "style.css").write_text("body { color: green; }")
        (site / "app.js").write_text("console.log('static');")
        (site / "photo.webp").write_text("WEBP_CONTENT")
        (site / "font.woff2").write_text("FONT_CONTENT")
        compressed_assets = {
            "compress.css": "body{color:green;background:white;}\n" * 1000,
            "compress.js": "console.log('static');\n" * 1000,
            "image.svg": '<svg xmlns="http://www.w3.org/2000/svg">' + '<circle cx="2" cy="2" r="1" fill="red"/>' * 1000 + '</svg>',
            "data.json": json.dumps([{"name": "Centre auditif", "city": "Lyon", "available": True}] * 1000),
        }
        for name, content in compressed_assets.items():
            (site / name).write_text(content)
        (site / "raw.svg").write_text(compressed_assets["image.svg"])
        (site / "api.php").write_text('<?php header("Content-Type: application/json"); file_put_contents("/tmp/php-hits", "api\\n", FILE_APPEND); readfile(__DIR__ . "/data.json");')
        (site / "index.php").write_text('<?php file_put_contents("/tmp/php-hits", "index\\n", FILE_APPEND); echo "FRONT_CONTROLLER";')
        (site / "generator.php").write_text('<?php file_put_contents("/tmp/php-hits", "generator\\n", FILE_APPEND); echo "GENERATED_CSS";')
        (site / "error.php").write_text('<?php file_put_contents("/tmp/php-hits", "error\\n", FILE_APPEND); http_response_code(404); echo "PHP_ERROR_DOCUMENT";')
        (site / ".htaccess").write_text(
            "ErrorDocument 404 /error.php\n"
            "SetEnvIf Request_URI ^/raw\\.svg$ no-gzip\n"
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
        for name, content in compressed_assets.items():
            check(cid, url, "/" + name, 200, content, headers={"Accept-Encoding": "gzip"}, encoding="gzip")
        check(cid, url, "/image.svg", 200, compressed_assets["image.svg"], headers={"Accept-Encoding": "identity"})
        check(cid, url, "/raw.svg", 200, compressed_assets["image.svg"], headers={"Accept-Encoding": "gzip"})
        check(cid, url, "/photo.webp", 200, "WEBP_CONTENT", headers={"Accept-Encoding": "gzip"})
        check(cid, url, "/api.php", 200, compressed_assets["data.json"], 1, headers={"Accept-Encoding": "gzip"}, encoding="gzip")
        check(cid, url, "/style.css?logging-check=once", 200, "body { color: green; }")
        logs = subprocess.run(["docker", "logs", cid], capture_output=True, text=True, check=True)
        assert logs.stdout.count('GET /style.css?logging-check=once HTTP/') == 1, logs.stdout
        assert 'GET /wp-json/' not in logs.stdout, logs.stdout
        assert not docker("exec", cid, "cat", "/var/log/apache2/access.log")
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
