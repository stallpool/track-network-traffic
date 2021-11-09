#!/bin/bash

ROOT_DIR=$(cd `dirname $0`; pwd)
PUBLISH_DIR=${ROOT_DIR}/publish

echo building version win-`cat ${ROOT_DIR}/bin/version/win`

mkdir -p ${PUBLISH_DIR}
mkdir -p ${ROOT_DIR}/.tnt

if [ ! -f ${ROOT_DIR}/template.zip ]; then
   echo there is no template.zip found
   exit 1
fi

pushd ${ROOT_DIR}/.tnt
unzip ${ROOT_DIR}/template.zip
cp -r ${ROOT_DIR}/bin/* ${ROOT_DIR}/.tnt/bin
zip ${PUBLISH_DIR}/tnt-win.zip -r bin
popd

rm -rf ${ROOT_DIR}/.tnt
