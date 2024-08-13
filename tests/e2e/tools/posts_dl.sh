#!/usr/bin/env sh
set -e

< ../data/download_out/posts.json jq -r '.[] | .link' > url_list.txt
touch rejected.log
wget --adjust-extension --input-file=url_list.txt \
  --force-directories --rejected-log=rejected.log
rm url_list.txt