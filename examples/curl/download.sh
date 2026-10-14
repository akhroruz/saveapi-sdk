#!/usr/bin/env sh
# The API without any client: one GET, JSON back.
#   SAVEAPI_KEY=sk_live_... ./download.sh "https://www.tiktok.com/@zachking/video/6768504823336815877"
set -eu

curl -sG "https://api.saveapi.org/v1/download" \
  -H "Authorization: Bearer ${SAVEAPI_KEY}" \
  --data-urlencode "url=$1"
