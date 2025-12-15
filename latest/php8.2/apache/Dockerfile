#
# NOTE: THIS DOCKERFILE IS GENERATED VIA "apply-templates.sh"
#
# PLEASE DO NOT EDIT IT DIRECTLY.
#

ARG PHP_VER
ARG PHP_TYPE

FROM php:8.2.29-fpm AS builder

RUN set -ex; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
  libavif-dev \
  libfreetype6-dev \
  libicu-dev \
  libjpeg-dev \
  libmagickwand-dev \
  libpng-dev \
  libwebp-dev \
  libzip-dev \
  wget \
  ; \
  \
  docker-php-ext-configure gd \
  --with-avif \
  --with-freetype \
  --with-jpeg \
  --with-webp \
  ; \
  docker-php-ext-install -j "$(nproc)" \
  bcmath \
  exif \
  gd \
  intl \
  mysqli \
  zip \
  $(test "${PHP_VERSION:0:3}" != "8.5" && echo 'opcache') \
  soap \
  pdo \
  pdo_mysql \
  ; \
  pecl install imagick-3.8.0; \
  docker-php-ext-enable imagick; \
  rm -r /tmp/pear; \
  \
  newrelic_url="http://download.newrelic.com/php_agent/release"; \
  arch=$(uname -m); \
  case "$arch" in \
  x86_64) nr_file=$(wget -qO- "${newrelic_url}/" | grep -oE 'newrelic-php5-[0-9.]+-linux\.tar\.gz' | head -1) ;; \
  aarch64) nr_file=$(wget -qO- "${newrelic_url}/" | grep -oE 'newrelic-php5-[0-9.]+-linux-aarch64\.tar\.gz' | head -1) ;; \
  esac; \
  if [ -n "$nr_file" ]; then \
  mkdir -p /tmp/newrelic; \
  wget -qO /tmp/newrelic/newrelic.tar.gz "${newrelic_url}/${nr_file}"; \
  tar -xzf /tmp/newrelic/newrelic.tar.gz --strip=1 -C /tmp/newrelic; \
  export NR_INSTALL_SILENT=true; \
  export NR_INSTALL_USE_CP_NOT_LN=true; \
  bash /tmp/newrelic/newrelic-install install; \
  rm -f /usr/local/etc/php/conf.d/newrelic.ini; \
  else \
  echo "NewRelic agent not available for architecture: $arch"; \
  touch /usr/bin/newrelic-daemon; \
  fi

FROM php:8.2.29-fpm AS runtime

ARG INRAGE_USER_ID=1000
ARG INRAGE_GROUP_ID=1000
ARG TARGETPLATFORM

ENV APP_ROOT="/var/www/html"
ENV PATH="${PATH}:/home/inr/.composer/vendor/bin:${APP_ROOT}/vendor/bin:${APP_ROOT}/bin"
ENV APACHE_HTTP_PORT=8080
ENV APACHE_HTTPS_PORT=8443

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

COPY --from=builder /usr/local/lib/php/extensions/ /usr/local/lib/php/extensions/
COPY --from=builder /usr/local/etc/php/conf.d/ /usr/local/etc/php/conf.d/
COPY --from=builder /usr/bin/newrelic-daemon /usr/bin/newrelic-daemon

RUN set -ex; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
  libavif16 \
  libicu76 \
  libmagickwand-7.q16-10 \
  libzip5 \
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
  [ -z "$err" ]; \
  \
  mkdir -p /var/log/newrelic/; \
  chown -R www-data:www-data /var/log/newrelic/; \
  chmod -R 775 /var/log/newrelic/

RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini"

RUN set -eux; \
  docker-php-ext-enable opcache;

RUN set -eux; \
  a2dismod mpm_prefork || true; \
  a2enmod mpm_event; \
  a2enmod rewrite expires headers remoteip; \
  a2enmod proxy proxy_fcgi setenvif; \
  find /etc/apache2 -type f -name '*.conf' -exec sed -ri 's/([[:space:]]*LogFormat[[:space:]]+"[^"]*)%h([^"]*")/\1%a\2/g' '{}' +; \
  sed -i 's/Listen 80/Listen 8080/' /etc/apache2/ports.conf; \
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
