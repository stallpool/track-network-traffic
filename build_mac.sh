#!/bin/bash

ROOT_DIR=`dirname $0`
PUBLISH_DIR=${ROOT_DIR}/publish

echo building version mac-`cat ${ROOT_DIR}/bin/version/mac`

mkdir -p ${PUBLISH_DIR}
mkdir -p ${ROOT_DIR}/.tnt

if [ ! -f ${ROOT_DIR}/template-mac.tar.gz ]; then
   echo there is no template-mac.tar.gz found
   exit 1
fi

tar -zxf ${ROOT_DIR}/template-mac.tar.gz -C ${ROOT_DIR}/.tnt
cp -r ${ROOT_DIR}/bin/* ${ROOT_DIR}/.tnt/bin
tar -zcf ${PUBLISH_DIR}/tnt-mac.tar.gz -C ${ROOT_DIR}/.tnt bin lib
rm -rf ${ROOT_DIR}/.tnt
