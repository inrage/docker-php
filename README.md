## Environment Variables

### PHP configuration

| Variable                              | Default                                  |
| ------------------------------------- | ---------------------------------------- | --------- | ------- | ------------ | -------------- | --------------- | ----------------- | -------------------- |
| `PHP_MEMORY_LIMIT`                    | `512M`                                   |
| `PHP_UPLOAD_MAX_FILESIZE`             | `64M`                                    |
| `PHP_POST_MAX_SIZE`                   | `64M`                                    |
| `PHP_MAX_EXECUTION_TIME`              | `600`                                    |
| `PHP_DEFAULT_SOCKET_TIMEOUT`          | `60`                                     |
| `PHP_SENDMAIL_PATH`                   | `/usr/bin/msmtp -t --read-envelope-from` |
| `PHP_ERROR_REPORTING`                 | `E_ERROR                                 | E_WARNING | E_PARSE | E_CORE_ERROR | E_CORE_WARNING | E_COMPILE_ERROR | E_COMPILE_WARNING | E_RECOVERABLE_ERROR` |
| `PHP_DISPLAY_ERRORS`                  | `Off`                                    |
| `PHP_DISPLAY_STARTUP_ERRORS`          | `Off`                                    |
| `PHP_LOG_ERRORS`                      | `On`                                     |
| `PHP_ERROR_LOG`                       | `/dev/stderr`                            |
| `PHP_LOG_ERRORS_MAX_LEN`              | `1024`                                   |
| `PHP_IGNORE_REPEATED_ERRORS`          | `On`                                     |
| `PHP_IGNORE_REPEATED_SOURCE`          | `Off`                                    |
| `PHP_HTML_ERRORS`                     | `Off`                                    |
| `PHP_OPCACHE_MEMORY_CONSUMPTION`      | `128`                                    |
| `PHP_OPCACHE_INTERNED_STRINGS_BUFFER` | `8`                                      |
| `PHP_OPCACHE_MAX_ACCELERATED_FILES`   | `4000`                                   |
| `PHP_OPCACHE_REVALIDATE_FREQ`         | `2`                                      |

### MSMTP configuration

| Variable                           | Default           |
| ---------------------------------- | ----------------- |
| `INR_SMTP_PORT`                    | `25`              |
| `INR_SMTP_TLS`                     | `off`             |
| `INR_SMTP_LOG`                     |                   |
| `INR_SMTP_LOGFILE`                 | `/proc/self/fd/2` |
| `INR_SMTP_AUTH`                    | `off`             |
| `INR_SMTP_HOST`                    | `relay.mailhub`   |
| `INR_SMTP_ADD_MISSING_DATE_HEADER` | `on`              |

defaults
port {{ getenv "INR_SMTP_PORT" "25" }}
tls {{ getenv "INR_SMTP_TLS" "off" }}
{{- if getenv "INR_SMTP_LOG" }}
logfile {{ getenv "INR_SMTP_LOGFILE" "/proc/self/fd/2" }}
{{- end }}

account default
auth {{ getenv "INR_SMTP_AUTH" "off" }}
host {{ getenv "INR_SMTP_HOST" "relay.mailhub" }}
add_missing_date_header {{ getenv "INR_SMTP_ADD_MISSING_DATE_HEADER" "on" }}
