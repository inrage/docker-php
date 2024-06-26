#
# NOTE: THIS DOCKERFILE IS GENERATED VIA "apply-templates.sh"
#
# PLEASE DO NOT EDIT IT DIRECTLY.
#

ARG PHP_VER
ARG PHP_TYPE

FROM php:8.2-fpm

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
    # https://pecl.php.net/package/imagick \
	pecl install imagick-3.6.0; \
	docker-php-ext-enable imagick; \
	rm -r /tmp/pear; \
	\
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
		| awk '/=>/ { so = $(NF-1); if (index(so, "/usr/local/") == 1) { next }; gsub("^/(usr/)?", "", so); print so }' \
		| sort -u \
		| xargs -r dpkg-query --search \
		| cut -d: -f1 \
		| sort -u \
		| xargs -rt apt-mark manual; \
	\
	apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false; \
	rm -rf /var/lib/apt/lists/*; \
	\
	! { ldd "$extDir"/*.so | grep 'not found'; }; \
    # check for output like "PHP Warning:  PHP Startup: Unable to load dynamic library 'foo' (tried: ...)
	err="$(php --version 3>&1 1>&2 2>&3)"; \
	[ -z "$err" ]

RUN set -eux; \
    pecl install redis; \
    docker-php-ext-enable redis;

# use production php.ini
RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini"

# apply custom PHP configuration
COPY php-custom.ini "$PHP_INI_DIR/conf.d/zzz-custom-php.ini"

# set recommended PHP.ini settings
# see https://secure.php.net/manual/en/opcache.installation.php
RUN set -eux; \
	docker-php-ext-enable opcache; \
	{ \
		echo 'opcache.memory_consumption=128'; \
		echo 'opcache.interned_strings_buffer=8'; \
		echo 'opcache.max_accelerated_files=4000'; \
		echo 'opcache.revalidate_freq=2'; \
	} > /usr/local/etc/php/conf.d/opcache-recommended.ini
# https://wordpress.org/support/article/editing-wp-config-php/#configure-error-logging
RUN { \
        # https://www.php.net/manual/en/errorfunc.constants.php
        # https://github.com/docker-library/wordpress/issues/420#issuecomment-517839670
		echo 'error_reporting = E_ERROR | E_WARNING | E_PARSE | E_CORE_ERROR | E_CORE_WARNING | E_COMPILE_ERROR | E_COMPILE_WARNING | E_RECOVERABLE_ERROR'; \
		echo 'display_errors = Off'; \
		echo 'display_startup_errors = Off'; \
		echo 'log_errors = On'; \
		echo 'error_log = /dev/stderr'; \
		echo 'log_errors_max_len = 1024'; \
		echo 'ignore_repeated_errors = On'; \
		echo 'ignore_repeated_source = Off'; \
		echo 'html_errors = Off'; \
	} > /usr/local/etc/php/conf.d/error-logging.ini


## Mailer
RUN echo "sendmail_path=/usr/bin/msmtp -t --read-envelope-from" > /usr/local/etc/php/conf.d/php-sendmail.ini

ARG INR_SMTP_HOST=relay.mailhub
ARG INR_SMTP_PORT=25

ENV INR_SMTP_HOST=$INR_SMTP_HOST
ENV INR_SMTP_PORT=$INR_SMTP_PORT

RUN set -eux; \
    { \
      echo 'account default'; \
      echo "host $INR_SMTP_HOST"; \
      echo "port $INR_SMTP_PORT"; \
    } > /etc/msmtprc

RUN set -eux; \
    chmod 755 ${APP_ROOT}; \
    chown ${INRAGE_USER_ID}:${INRAGE_GROUP_ID} ${APP_ROOT};

COPY vhost.conf /etc/apache2/sites-available/000-default.conf

COPY cron-entrypoint.sh /cron-entrypoint.sh

USER inr
WORKDIR ${APP_ROOT}

CMD ["apache2-foreground"]
