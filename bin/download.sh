#!/bin/bash -ex
filename=${1%}
filename=${filename##*/}
catalog_url=$(echo "$filename" | perl -pe 's/\%(\w\w)/chr hex $1/ge')
path="workspace/dcat/$filename/original"
#curl -L -s -o "$path" -z "$path" "$catalog_url"
curl --insecure -L -s -o "$path" "$catalog_url"
