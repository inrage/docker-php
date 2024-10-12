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

process_templates() {
  _gotpl "msmtprc.tmpl" "/etc/msmtprc"
}

process_templates

exec "$@"
