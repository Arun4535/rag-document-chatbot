#!/bin/sh
set -eu

if [ -n "${BACKEND_UPSTREAM:-}" ]; then
  envsubst '${BACKEND_UPSTREAM}' < /etc/nginx/templates/nginx.render.template > /etc/nginx/conf.d/default.conf
fi

exec nginx -g 'daemon off;'
