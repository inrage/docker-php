#!/usr/bin/env bash

set -eo pipefail

if [[ -n "${DEBUG}" ]]; then
    set -x
fi

_gotpl() {
    if [[ -f "/etc/gotpl/$1" ]]; then
        gotpl "/etc/gotpl/$1" > "$2"
    fi
}

exec_init_scripts() {
    shopt -s nullglob
    for f in /docker-entrypoint-init.d/*; do
        . "$f"
    done
    shopt -u nullglob
}


process_templates() {
  _gotpl "docker-php-base.ini.tmpl" "${PHP_INI_DIR}/conf.d/zzz-custom-php.ini"
  _gotpl "docker-php-error.ini.tmpl" "${PHP_INI_DIR}/conf.d/docker-php-error.ini"
  _gotpl "docker-php-ext-opcache.ini.tmpl" "${PHP_INI_DIR}/conf.d/docker-php-ext-opcache.ini"

  _gotpl "docker-apache-vhost.conf.tmpl" "/etc/apache2/sites-available/000-default.conf"
  _gotpl "docker-apache-remoteip.conf.tmpl" "/etc/apache2/conf-available/remoteip.conf"


  _gotpl "msmtprc.tmpl" "/etc/msmtprc"
}

process_templates

exec_init_scripts


exec /usr/local/bin/docker-php-entrypoint "${@}"
