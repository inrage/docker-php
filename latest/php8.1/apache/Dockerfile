#
# NOTE: THIS DOCKERFILE IS GENERATED VIA "apply-templates.sh"
#
# PLEASE DO NOT EDIT IT DIRECTLY.
#

ARG PHP_VER
ARG PHP_TYPE

FROM debian:trixie-slim AS runtime

ENV PHP_VERSION=8.1.34
ENV PHP_INI_DIR=/usr/local/etc/php

RUN set -eux; \
  apt-get update; \
  apt-get install -y --no-install-recommends ca-certificates curl gnupg wget; \
  curl -fsSL https://packages.sury.org/php/apt.gpg | gpg --dearmor -o /usr/share/keyrings/sury-php.gpg; \
  echo "deb [signed-by=/usr/share/keyrings/sury-php.gpg] https://packages.sury.org/php/ trixie main" > /etc/apt/sources.list.d/sury-php.list; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
  php8.1-bcmath=8.1.34-9+0~20261021.82+debian13~1.gbp4e430a \
  php8.1-cli=8.1.34-9+0~20261021.82+debian13~1.gbp4e430a \
  php8.1-common=8.1.34-9+0~20261021.82+debian13~1.gbp4e430a \
  php8.1-curl=8.1.34-9+0~20261021.82+debian13~1.gbp4e430a \
  php8.1-fpm=8.1.34-9+0~20261021.82+debian13~1.gbp4e430a \
  php8.1-gd=8.1.34-9+0~20261021.82+debian13~1.gbp4e430a \
  php8.1-intl=8.1.34-9+0~20261021.82+debian13~1.gbp4e430a \
  php8.1-mbstring=8.1.34-9+0~20261021.82+debian13~1.gbp4e430a \
  php8.1-mysql=8.1.34-9+0~20261021.82+debian13~1.gbp4e430a \
  php8.1-opcache=8.1.34-9+0~20261021.82+debian13~1.gbp4e430a \
  php8.1-readline=8.1.34-9+0~20261021.82+debian13~1.gbp4e430a \
  php8.1-soap=8.1.34-9+0~20261021.82+debian13~1.gbp4e430a \
  php8.1-sqlite3=8.1.34-9+0~20261021.82+debian13~1.gbp4e430a \
  php8.1-xml=8.1.34-9+0~20261021.82+debian13~1.gbp4e430a \
  php8.1-zip=8.1.34-9+0~20261021.82+debian13~1.gbp4e430a \
  php8.1-imagick \
    ; \
  apt-get purge -y --auto-remove gnupg; \
  rm -rf /var/lib/apt/lists/*; \
  [ "$(dpkg-query -W -f='${Version}' php8.1-cli)" = "8.1.34-9+0~20261021.82+debian13~1.gbp4e430a" ]

RUN set -eux; \
  v=8.1; \
  mkdir -p "$PHP_INI_DIR/conf.d" /usr/local/etc/php-fpm.d /usr/local/sbin /var/run/php /var/www/html; \
  cp -a "/etc/php/$v/fpm/conf.d/." "$PHP_INI_DIR/conf.d/"; \
  cp "/usr/lib/php/$v/php.ini-production" "$PHP_INI_DIR/php.ini"; \
  cp "/usr/lib/php/$v/php.ini-production" "/usr/lib/php/$v/php.ini-development" "$PHP_INI_DIR/"; \
  for sapi in cli fpm; do \
  rm -rf "/etc/php/$v/$sapi/conf.d" "/etc/php/$v/$sapi/php.ini"; \
  ln -s "$PHP_INI_DIR/conf.d" "/etc/php/$v/$sapi/conf.d"; \
  ln -s "$PHP_INI_DIR/php.ini" "/etc/php/$v/$sapi/php.ini"; \
  done; \
  sed -e 's/^listen\.owner/;listen.owner/' -e 's/^listen\.group/;listen.group/' "/etc/php/$v/fpm/pool.d/www.conf" > /usr/local/etc/php-fpm.d/www.conf; \
  rm -rf "/etc/php/$v/fpm/pool.d"; \
  ln -s /usr/local/etc/php-fpm.d "/etc/php/$v/fpm/pool.d"; \
  sed -i -e 's/^error_log = /;error_log = /' -e 's#^pid = .*#pid = /var/run/php/php-fpm.pid#' "/etc/php/$v/fpm/php-fpm.conf"; \
  printf '[global]\nerror_log = /proc/self/fd/2\nlog_limit = 8192\n\n[www]\naccess.log = /proc/self/fd/2\nclear_env = no\ncatch_workers_output = yes\ndecorate_workers_output = no\n' > /usr/local/etc/php-fpm.d/docker.conf; \
  printf '[global]\ndaemonize = no\n\n[www]\nlisten = 9000\n' > /usr/local/etc/php-fpm.d/zz-docker.conf; \
  printf 'fastcgi.logging = Off\n' > "$PHP_INI_DIR/conf.d/docker-fpm.ini"; \
  rm "$PHP_INI_DIR/conf.d/10-opcache.ini"; \
  printf 'zend_extension=opcache\n' > "$PHP_INI_DIR/conf.d/docker-php-ext-opcache.ini"; \
  ln -s "/usr/sbin/php-fpm$v" /usr/local/sbin/php-fpm

ARG INRAGE_USER_ID=1000
ARG INRAGE_GROUP_ID=1000
ARG TARGETPLATFORM

ENV APP_ROOT="/var/www/html"
ENV PATH="${PATH}:/home/inr/.composer/vendor/bin:${APP_ROOT}/vendor/bin:${APP_ROOT}/bin"
ENV APACHE_HTTP_PORT=8080
ENV APACHE_HTTPS_PORT=8443
ENV S6_KEEP_ENV=1

RUN set -xe; \
  groupadd -g $INRAGE_GROUP_ID inr; \
  useradd -u $INRAGE_USER_ID -g $INRAGE_GROUP_ID -m -s /bin/bash -g inr inr; \
  adduser inr www-data; \
  sed -i '/^inr/s/!/*/' /etc/shadow;

RUN set -xe; \
  {\
  echo 'export PS1="\[\e[1;34m\]\u\[\e[0m\]\[\e[0;36m\]@\[\e[0;33m\]${INR_APP_NAME:-php}\[\e[0;35m\].${INR_ENVIRONMENT_NAME:-prod}\[\e[0m\]:\w $ "'; \
  echo "export PATH=${PATH}"; \
  echo "alias l='ls -lah'"; \
  echo "alias ls='ls -F --color'"; \
  echo "alias ll='ls -lF --color'"; \
  echo "alias l='ls -lhaF --color'"; \
  echo "alias l.='ls -daF --color .*'"; \
  } | tee /home/inr/.shrc; \
  \
  cp /home/inr/.shrc /home/inr/.bashrc; \
  cp /home/inr/.shrc /home/inr/.bash_profile;

RUN set -eux; \
  chmod 755 /var/www/html; \
  chown ${INRAGE_USER_ID}:${INRAGE_GROUP_ID} /var/www/html;

ADD https://github.com/just-containers/s6-overlay/releases/download/v3.2.0.2/s6-overlay-noarch.tar.xz /tmp
ADD https://github.com/just-containers/s6-overlay/releases/download/v3.2.0.2/s6-overlay-x86_64.tar.xz /tmp
ADD https://github.com/just-containers/s6-overlay/releases/download/v3.2.0.2/s6-overlay-aarch64.tar.xz /tmp

RUN set -eux; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
    apache2 \
  apache2-utils \
  xz-utils \
    ghostscript \
  less \
  msmtp \
  msmtp-mta \
  cron \
  wget \
  ; \
  rm -rf /var/lib/apt/lists/*


RUN set -ex; \
  extDir="$(php -r 'echo ini_get("extension_dir");')"; \
  [ -d "$extDir" ]; \
  \
  for f in "$extDir"/*.so; do \
  if ldd "$f" | grep 'not found'; then \
  echo "Missing shared library dependencies in PHP extensions ($f)"; \
  exit 1; \
  fi; \
  done; \
  \
  out="$(php -r 'exit(0);')"; \
  [ -z "$out" ]; \
  err="$(php -r 'exit(0);' 3>&1 1>&2 2>&3)"; \
  [ -z "$err" ]; \
  err="$(php --version 3>&1 1>&2 2>&3)"; \
  [ -z "$err" ]



RUN set -eux; \
  a2dismod mpm_prefork || true; \
  a2enmod mpm_event; \
  a2enmod rewrite expires headers remoteip; \
  a2enmod proxy proxy_fcgi setenvif; \
  find /etc/apache2 -type f -name '*.conf' -exec sed -ri 's/([[:space:]]*LogFormat[[:space:]]+"[^"]*)%h([^"]*")/\1%a\2/g' '{}' +; \
  sed -i 's/^Listen 80$/Listen ${APACHE_HTTP_PORT}/' /etc/apache2/ports.conf; \
  sed -i 's/Listen 443/Listen 8443/' /etc/apache2/ports.conf; \
  sed -i 's/APACHE_RUN_USER=www-data/APACHE_RUN_USER=inr/' /etc/apache2/envvars; \
  sed -i 's/APACHE_RUN_GROUP=www-data/APACHE_RUN_GROUP=inr/' /etc/apache2/envvars; \
  tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz; \
  arch=$(uname -m); \
  case "$arch" in \
    x86_64) tar -C / -Jxpf /tmp/s6-overlay-x86_64.tar.xz ;; \
    aarch64) tar -C / -Jxpf /tmp/s6-overlay-aarch64.tar.xz ;; \
  esac; \
  rm -f /tmp/s6-overlay-*.tar.xz

RUN set -eux; \
  \
  rm -f ${APP_ROOT}/index.html; \
  chmod 755 ${APP_ROOT}; \
  chown ${INRAGE_USER_ID}:${INRAGE_GROUP_ID} ${APP_ROOT}; \
  touch /etc/msmtprc; \
    mkdir -p /etc/apache2/sites-available; \
  touch /etc/apache2/sites-available/000-default.conf; \
  mkdir -p /etc/apache2/conf-enabled; \
  mkdir -p /etc/apache2/mpm-overrides; \
  mkdir -p /var/run/php; \
  mkdir -p /var/run/apache2; \
  mkdir -p /var/lock/apache2; \
  mkdir -p /var/log/apache2; \
  sed -i 's/^user = .*/;user = www-data/' /usr/local/etc/php-fpm.d/www.conf; \
  sed -i 's/^group = .*/;group = www-data/' /usr/local/etc/php-fpm.d/www.conf; \
  chown -R ${INRAGE_USER_ID}:${INRAGE_GROUP_ID} \
  "${PHP_INI_DIR}/conf.d" \
  /usr/local/etc/php-fpm.d \
  /etc/apache2/sites-available/000-default.conf \
  /etc/apache2/conf-enabled \
  /etc/apache2/mpm-overrides \
  /etc/msmtprc \
  /var/run/php \
  /var/run/apache2 \
  /var/lock/apache2 \
  /var/log/apache2; \
  echo 'IncludeOptional /etc/apache2/mpm-overrides/mpm_event.conf' > /etc/apache2/conf-enabled/mpm-overrides.conf; \
    dockerplatform="${TARGETPLATFORM:-linux/amd64}"; \
  dockerplatform=$(printf '%s' "$dockerplatform" | tr '/' '-'); \
  gotpl_url="https://github.com/inrage/gotpl/releases/download/1.0.1/gotpl-${dockerplatform}.tar.gz"; \
  wget -qO- "${gotpl_url}" | tar xz --no-same-owner -C /usr/local/bin;

COPY s6-overlay/s6-rc.d/ /etc/s6-overlay/s6-rc.d/
COPY s6-overlay/scripts/ /etc/s6-overlay/scripts/
RUN chmod +x /etc/s6-overlay/scripts/* && \
    find /etc/s6-overlay/s6-rc.d -name run -exec chmod +x {} \; && \
    chmod -R a+rX /etc/s6-overlay/s6-rc.d /etc/s6-overlay/scripts
COPY cron-entrypoint.sh /cron-entrypoint.sh
COPY templates /etc/gotpl/
COPY bin /usr/local/bin/

USER inr
WORKDIR ${APP_ROOT}

EXPOSE 8080 8443
ENTRYPOINT ["/init"]
