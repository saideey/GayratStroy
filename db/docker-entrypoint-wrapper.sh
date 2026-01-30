#!/bin/bash
set -e

# Password sync ni background da ishga tushirish
/usr/local/bin/sync-password.sh &

# Original PostgreSQL entrypoint ni chaqirish
exec docker-entrypoint.sh "$@"
