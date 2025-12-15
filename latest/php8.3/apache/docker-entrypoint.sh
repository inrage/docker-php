#!/usr/bin/env bash

set -eo pipefail

if [[ -n "${DEBUG}" ]]; then
  set -x
fi

_gotpl() {
  if [[ -f "/etc/gotpl/$1" ]]; then
    gotpl "/etc/gotpl/$1" >"$2"
  fi
}

exec_init_scripts() {
  shopt -s nullglob
  for f in /docker-entrypoint-init.d/*; do
    su -s /bin/bash inr -c ". $f"
  done
  shopt -u nullglob
}

process_templates() {
  _gotpl "docker-php-base.ini.tmpl" "${PHP_INI_DIR}/conf.d/zzz-custom-php.ini"
  _gotpl "docker-php-error.ini.tmpl" "${PHP_INI_DIR}/conf.d/docker-php-error.ini"
  _gotpl "docker-php-ext-opcache.ini.tmpl" "${PHP_INI_DIR}/conf.d/docker-php-ext-opcache.ini"
  _gotpl "docker-php-ext-newrelic.ini.tmpl" "${PHP_INI_DIR}/conf.d/docker-php-ext-newrelic.ini"

  if [[ -f "/usr/local/etc/php-fpm.d/www.conf" ]]; then
    _gotpl "docker-php-fpm-pool.conf.tmpl" "/usr/local/etc/php-fpm.d/zz-inrage-pool.conf"
  fi

  if [[ -d "/etc/apache2" ]]; then
    _gotpl "docker-apache-servername.conf.tmpl" "/etc/apache2/conf-enabled/servername.conf"
    _gotpl "docker-apache-vhost.conf.tmpl" "/etc/apache2/sites-available/000-default.conf"
    _gotpl "docker-apache-remoteip.conf.tmpl" "/etc/apache2/conf-enabled/remoteip.conf"
    _gotpl "docker-apache-event.conf.tmpl" "/etc/apache2/mpm-overrides/mpm_event.conf"
  fi

  _gotpl "msmtprc.tmpl" "/etc/msmtprc"
}

process_templates

exec_init_scripts

if [[ "${1}" == "make" ]]; then
  exec "${@}" -f /usr/local/bin/actions.mk
else
  exec /usr/local/bin/docker-php-entrypoint "${@}"
fi
