#!/bin/sh
set -e

# Replace environment variables in runtime-config.js
if [ -n "$API_URL" ]; then
  sed -i "s|\${API_URL}|$API_URL|g" /usr/share/nginx/html/runtime-config.js
fi

# Execute the CMD
exec "$@"
