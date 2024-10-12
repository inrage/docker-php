ARG PHP_VER
ARG PHP_TYPE

FROM php:{{ env.phpVersion }}-{{ env.variant }}

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
	{{ if env.phpVersion != "7.2" and env.phpVersion != "7.3" then ( -}}
	docker-php-ext-configure gd \
		--with-freetype \
		--with-jpeg \
		--with-webp \
	; \
    {{ ) else ( -}}
   docker-php-ext-configure gd \
        --with-freetype-dir=/usr \
        --with-jpeg-dir=/usr \
        --with-png-dir=/usr \
    ; \
    {{ ) end -}}
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
  # https://pecl.php.net/package/imagick
  {{ if true then ( -}}
  # https://github.com/Imagick/imagick/commit/5ae2ecf20a1157073bad0170106ad0cf74e01cb6 (causes a lot of build failures, but strangely only intermittent ones 🤔)
  # see also https://github.com/Imagick/imagick/pull/641
  # this is "pecl install imagick-3.7.0", but by hand so we can apply a small hack / part of the above commit
    curl -fL -o imagick.tgz 'https://pecl.php.net/get/imagick-3.7.0.tgz'; \
    echo '5a364354109029d224bcbb2e82e15b248be9b641227f45e63425c06531792d3e *imagick.tgz' | sha256sum -c -; \
    tar --extract --directory /tmp --file imagick.tgz imagick-3.7.0; \
    grep '^//#endif$' /tmp/imagick-3.7.0/Imagick.stub.php; \
    test "$(grep -c '^//#endif$' /tmp/imagick-3.7.0/Imagick.stub.php)" = '1'; \
    sed -i -e 's!^//#endif$!#endif!' /tmp/imagick-3.7.0/Imagick.stub.php; \
    grep '^//#endif$' /tmp/imagick-3.7.0/Imagick.stub.php && exit 1 || :; \
    docker-php-ext-install /tmp/imagick-3.7.0; \
    rm -rf imagick.tgz /tmp/imagick-3.7.0; \
  {{ # TODO when imagick has another release, we should ditch this whole block and just update instead -}}
  {{ ) else ( -}}
    pecl install imagick-3.7.0; \
    docker-php-ext-enable imagick; \
    rm -r /tmp/pear; \
  {{ ) end -}}
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
	! { ldd "$extDir"/*.so | grep 'not found'; }; \
    # check for output like "PHP Warning:  PHP Startup: Unable to load dynamic library 'foo' (tried: ...)
	err="$(php --version 3>&1 1>&2 2>&3)"; \
	[ -z "$err" ]

# use production php.ini
RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini"

{{ if env.variant != "cli" then ( -}}
RUN set -eux; \
	docker-php-ext-enable opcache;
{{ ) else "" end -}}

{{ if env.variant == "apache" then ( -}}
RUN set -eux; \
	a2enmod rewrite expires headers remoteip; \
	find /etc/apache2 -type f -name '*.conf' -exec sed -ri 's/([[:space:]]*LogFormat[[:space:]]+"[^"]*)%h([^"]*")/\1%a\2/g' '{}' +
{{ ) else "" end -}}

ARG TARGETPLATFORM

RUN set -eux; \
    \
    chmod 755 ${APP_ROOT}; \
    chown ${INRAGE_USER_ID}:${INRAGE_GROUP_ID} ${APP_ROOT}; \
    touch /etc/msmtprc; \
    chown -R ${INRAGE_USER_ID}:${INRAGE_GROUP_ID} \
      "${PHP_INI_DIR}/conf.d" \
      /etc/apache2/sites-available/000-default.conf \
      /etc/apache2/conf-available \
      /etc/msmtprc; \
    # Download helper scripts.
    dockerplatform=${TARGETPLATFORM:-linux/amd64}; \
    dockerplatform=$(echo $dockerplatform | tr '/' '-'); \
    gotpl_url="https://github.com/wodby/gotpl/releases/download/0.3.3/gotpl-${dockerplatform}.tar.gz"; \
    wget -qO- "${gotpl_url}" | tar xz --no-same-owner -C /usr/local/bin;

COPY cron-entrypoint.sh /cron-entrypoint.sh
COPY templates /etc/gotpl/
COPY docker-entrypoint.sh /

USER inr
WORKDIR ${APP_ROOT}

ENTRYPOINT ["/docker-entrypoint.sh"]

{{ if env.variant != "cli" then ( -}}
CMD ["apache2-foreground"]
{{ ) else ( -}}
CMD ["php"]
{{ ) end -}}
