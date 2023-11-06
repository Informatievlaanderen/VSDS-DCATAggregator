#!/bin/bash -ex
VERSION=`curl https://dlcdn.apache.org/jena/binaries/ 2>/dev/null| sed -n "s/^.*<a href=\"apache-jena-\([[:digit:]]*.[[:digit:]]*.[[:digit:]]*\).zip\">.*$/\1/p"`
rm -rf apache-jena apache-jena-*
wget https://dlcdn.apache.org/jena/binaries/apache-jena-${VERSION}.zip -O apache-jena.zip
unzip apache-jena.zip
rm apache-jena.zip
ln -s apache-jena-* apache-jena
