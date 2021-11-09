#!/bin/bash

ROOT_DIR=`dirname $0`
PUBLISH_DIR=${ROOT_DIR}/publish

echo building version lin-`cat ${ROOT_DIR}/bin/version/lin`

mkdir -p ${PUBLISH_DIR}
mkdir -p ${ROOT_DIR}/.tnt

if [ ! -f ${ROOT_DIR}/template.tar.gz ]; then
   echo there is no template.tar.gz found
   exit 1
fi

tar -zxf ${ROOT_DIR}/template.tar.gz -C ${ROOT_DIR}/.tnt
cp -r ${ROOT_DIR}/bin/* ${ROOT_DIR}/.tnt/bin/

tar -zcf ${PUBLISH_DIR}/tnt-lin.tar.gz -C ${ROOT_DIR}/.tnt bin lib

rm -rf ${ROOT_DIR}/.tnt
