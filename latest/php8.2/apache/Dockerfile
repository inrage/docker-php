#
# NOTE: THIS DOCKERFILE IS GENERATED VIA "apply-templates.sh"
#
# PLEASE DO NOT EDIT IT DIRECTLY.
#

ARG PHP_VER
ARG PHP_TYPE

FROM php:8.2.29-apache

ARG INRAGE_USER_ID=1000
ARG INRAGE_GROUP_ID=1000

ENV APP_ROOT="/var/www/html"

ENV PATH="${PATH}:/home/inr/.composer/vendor/bin:${APP_ROOT}/vendor/bin:${APP_ROOT}/bin"

RUN set -xe; \
  groupadd -g $INRAGE_GROUP_ID inr; \
  useradd -u $INRAGE_USER_ID -g $INRAGE_GROUP_ID -m -s /bin/bash -g inr inr; \
  adduser inr www-data; \
  sed -i '/^inr/s/!/*/' /etc/shadow;

RUN set -xe; \
  {\
  echo 'export PS1="\[\e[1;34m\]\u\[\e[0m\]\[\e[0;36m\]@\[\e[0;33m\]${INR_APP_NAME:-php}\[\e[0;35m\].${INR_ENVIRONMENT_NAME:-prod}\[\e[0m\]:\w $ "'; \
  # Make sure PATH is the same for ssh sessions.
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

RUN set -eux; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
  ghostscript \
  less \
  mariadb-client \
  msmtp \
  msmtp-mta \
  cron \
  wget \
  vim \
  ; \
  rm -rf /var/lib/apt/lists/*

RUN set -ex; \
  \
  savedAptMark="$(apt-mark showmanual)"; \
  \
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
  soap \
  pdo \
  pdo_mysql \
  ; \
  # NewRelic extension and agent. \
  newrelic_url="http://download.newrelic.com/php_agent/release/"; \
  wget -r -nd --no-parent -P /tmp/newrelic -Alinux.tar.gz "${newrelic_url}" >/dev/null 2>&1; \
  tar -xzf /tmp/newrelic/newrelic-php*.tar.gz --strip=1 -C /tmp/newrelic; \
  export NR_INSTALL_SILENT=true; \
  export NR_INSTALL_USE_CP_NOT_LN=true; \
  bash /tmp/newrelic/newrelic-install install; \
  rm -f /usr/local/etc/php/conf.d/newrelic.ini; \
  mkdir -p /var/log/newrelic/; \
  chown -R www-data:www-data /var/log/newrelic/; \
  chmod -R 775 /var/log/newrelic/; \
  \
  # https://pecl.php.net/package/imagick
  pecl install imagick-3.8.0; \
  docker-php-ext-enable imagick; \
  rm -r /tmp/pear; \
  \
  # some misbehaving extensions end up outputting to stdout 🙈 (https://github.com/docker-library/wordpress/issues/669#issuecomment-993945967)
  out="$(php -r 'exit(0);')"; \
  [ -z "$out" ]; \
  err="$(php -r 'exit(0);' 3>&1 1>&2 2>&3)"; \
  [ -z "$err" ]; \
  \
  extDir="$(php -r 'echo ini_get("extension_dir");')"; \
  [ -d "$extDir" ]; \
  # reset apt-mark's "manual" list so that "purge --auto-remove" will remove all build dependencies
  apt-mark auto '.*' > /dev/null; \
  apt-mark manual $savedAptMark; \
  ldd "$extDir"/*.so \
  | awk '/=>/ { so = $(NF-1); if (index(so, "/usr/local/") == 1) { next }; gsub("^/(usr/)?", "", so); printf "*%s\n", so }' \
  | sort -u \
  | xargs -r dpkg-query --search \
  | cut -d: -f1 \
  | sort -u \
  | xargs -rt apt-mark manual; \
  \
  apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false; \
  rm -rf /var/lib/apt/lists/*; \
  \
  for f in "$extDir"/*.so; do \
  if ldd "$f" | grep 'not found'; then \
  echo "Missing shared library dependencies in PHP extensions ($f)"; \
  exit 1; \
  fi; \
  done; \
  # check for output like "PHP Warning:  PHP Startup: Unable to load dynamic library 'foo' (tried: ...)
  err="$(php --version 3>&1 1>&2 2>&3)"; \
  [ -z "$err" ]

# use production php.ini
RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini"

RUN set -eux; \
  docker-php-ext-enable opcache;

RUN set -eux; \
  a2enmod rewrite expires headers remoteip; \
  find /etc/apache2 -type f -name '*.conf' -exec sed -ri 's/([[:space:]]*LogFormat[[:space:]]+"[^"]*)%h([^"]*")/\1%a\2/g' '{}' +

ARG TARGETPLATFORM

RUN set -eux; \
  \
  chmod 755 ${APP_ROOT}; \
  chown ${INRAGE_USER_ID}:${INRAGE_GROUP_ID} ${APP_ROOT}; \
  touch /etc/msmtprc; \
  mkdir -p /etc/apache2/sites-available; \
  touch /etc/apache2/sites-available/000-default.conf; \
  mkdir -p /etc/apache2/conf-enabled; \
  chown -R ${INRAGE_USER_ID}:${INRAGE_GROUP_ID} \
  "${PHP_INI_DIR}/conf.d" \
  /etc/apache2/sites-available/000-default.conf \
  /etc/apache2/conf-enabled \
  /etc/apache2/mods-enabled \
  /etc/msmtprc; \
  # Download helper scripts.
  dockerplatform="${TARGETPLATFORM:-linux/amd64}"; \
  dockerplatform=$(printf '%s' "$dockerplatform" | tr '/' '-'); \
  gotpl_url="https://github.com/inrage/gotpl/releases/download/1.0.0/gotpl-${dockerplatform}.tar.gz"; \
  wget -qO- "${gotpl_url}" | tar xz --no-same-owner -C /usr/local/bin;

COPY cron-entrypoint.sh /cron-entrypoint.sh
COPY templates /etc/gotpl/
COPY docker-entrypoint.sh /
COPY bin /usr/local/bin/

USER inr
WORKDIR ${APP_ROOT}

ENTRYPOINT ["/docker-entrypoint.sh"]

CMD ["apache2-foreground"]
