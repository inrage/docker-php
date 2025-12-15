# Docker PHP

Optimized PHP Docker images with Apache Event MPM and PHP-FPM for high-performance web applications.

## Features

- **Apache Event MPM + PHP-FPM**: High-performance architecture with threaded Apache and FastCGI process manager
- **Supervisor**: Process orchestration for Apache and PHP-FPM
- **PHP Extensions**: gd (avif, freetype, jpeg, webp), imagick, intl, mysqli, opcache, pdo_mysql, zip, bcmath, exif, soap
- **Tools**: Composer path, msmtp for mail, NewRelic agent
- **Security**: Non-root `inr` user (UID/GID 1000) for PHP-FPM processes
- **Runtime Configuration**: Environment-based configuration via gotpl templates

## Supported PHP Versions

| PHP Version | Tag |
|-------------|-----|
| PHP 8.4 | `inrage/docker-php:8.4` |
| PHP 8.3 | `inrage/docker-php:8.3` |
| PHP 8.2 | `inrage/docker-php:8.2` |
| PHP 8.1 | `inrage/docker-php:8.1` |

## Architecture

```
Container
    |
    +-- Supervisor (root)
            |
            +-- PHP-FPM (priority 10)
            |       |
            |       +-- Pool [www] (user: inr)
            |       +-- Socket: /var/run/php/php-fpm.sock
            |
            +-- Apache Event MPM (priority 20)
                    |
                    +-- proxy_fcgi -> PHP-FPM socket
```

## Quick Start

```bash
docker run -d -p 80:80 -v $(pwd):/var/www/html inrage/docker-php:8.4
```

## Environment Variables

### Apache Event MPM

| Variable | Default | Description |
|----------|---------|-------------|
| `APACHE_EVENT_START_SERVERS` | `2` | Number of server processes to start |
| `APACHE_EVENT_MIN_SPARE_THREADS` | `25` | Minimum number of idle threads |
| `APACHE_EVENT_MAX_SPARE_THREADS` | `75` | Maximum number of idle threads |
| `APACHE_EVENT_THREADS_PER_CHILD` | `25` | Number of threads per child process |
| `APACHE_EVENT_THREAD_LIMIT` | `64` | Maximum threads per child |
| `APACHE_EVENT_MAX_REQUEST_WORKERS` | `150` | Maximum simultaneous requests |
| `APACHE_EVENT_MAX_CONNECTIONS_PER_CHILD` | `2000` | Connections before child respawn |
| `APACHE_KEEPALIVE` | `On` | Enable HTTP KeepAlive |
| `APACHE_MAX_KEEPALIVE_REQUESTS` | `100` | Max requests per connection |
| `APACHE_KEEPALIVE_TIMEOUT` | `2` | KeepAlive timeout in seconds |
| `APACHE_SERVER_NAME` | `localhost` | Server name |
| `APACHE_VHOST_DIR` | `/var/www/html` | Document root |

### PHP-FPM Pool

| Variable | Default | Description |
|----------|---------|-------------|
| `PHP_FPM_PM` | `dynamic` | Process manager mode (static, dynamic, ondemand) |
| `PHP_FPM_PM_MAX_CHILDREN` | `20` | Maximum number of child processes |
| `PHP_FPM_PM_START_SERVERS` | `4` | Number of children at startup |
| `PHP_FPM_PM_MIN_SPARE_SERVERS` | `2` | Minimum idle children |
| `PHP_FPM_PM_MAX_SPARE_SERVERS` | `6` | Maximum idle children |
| `PHP_FPM_PM_MAX_REQUESTS` | `500` | Requests before child respawn |

### PHP Configuration

| Variable | Default |
|----------|---------|
| `PHP_MEMORY_LIMIT` | `512M` |
| `PHP_UPLOAD_MAX_FILESIZE` | `64M` |
| `PHP_POST_MAX_SIZE` | `64M` |
| `PHP_MAX_EXECUTION_TIME` | `600` |
| `PHP_DEFAULT_SOCKET_TIMEOUT` | `60` |
| `PHP_SENDMAIL_PATH` | `/usr/bin/msmtp -t --read-envelope-from` |
| `PHP_ERROR_REPORTING` | |
| `PHP_DISPLAY_ERRORS` | `Off` |
| `PHP_DISPLAY_STARTUP_ERRORS` | `Off` |
| `PHP_LOG_ERRORS` | `On` |
| `PHP_ERROR_LOG` | `/dev/stderr` |
| `PHP_LOG_ERRORS_MAX_LEN` | `1024` |
| `PHP_IGNORE_REPEATED_ERRORS` | `On` |
| `PHP_IGNORE_REPEATED_SOURCE` | `Off` |
| `PHP_HTML_ERRORS` | `Off` |

### OPcache

| Variable | Default |
|----------|---------|
| `PHP_OPCACHE_MEMORY_CONSUMPTION` | `128` |
| `PHP_OPCACHE_INTERNED_STRINGS_BUFFER` | `8` |
| `PHP_OPCACHE_MAX_ACCELERATED_FILES` | `4000` |
| `PHP_OPCACHE_REVALIDATE_FREQ` | `2` |

### MSMTP (Mail)

| Variable | Default |
|----------|---------|
| `INR_SMTP_HOST` | `relay.mailhub` |
| `INR_SMTP_PORT` | `25` |
| `INR_SMTP_TLS` | `off` |
| `INR_SMTP_AUTH` | `off` |
| `INR_SMTP_LOG` | |
| `INR_SMTP_LOGFILE` | `/proc/self/fd/2` |
| `INR_SMTP_ADD_MISSING_DATE_HEADER` | `on` |

### NewRelic

| Variable | Default | Description |
|----------|---------|-------------|
| `NEWRELIC_ENABLED` | `false` | Enable NewRelic agent |
| `NEWRELIC_LICENSE` | | NewRelic license key |
| `NEWRELIC_APPNAME` | `PHP Application` | Application name in NewRelic |

## Custom Init Scripts

Place shell scripts in `/docker-entrypoint-init.d/` to execute them at container startup. Scripts are executed as the `inr` user.

```dockerfile
COPY my-init.sh /docker-entrypoint-init.d/
```

## Build Locally

```bash
# Generate all Dockerfiles from templates
./apply-templates.sh

# Build a specific image
docker build -t inrage/docker-php:8.4 latest/php8.4/apache/
```

## License

MIT
