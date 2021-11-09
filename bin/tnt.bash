#!/bin/bash

# TODO: build static-linked busybox to get dirname support
#       even when it is alpine
SELF=$(cd `dirname $0`; pwd)
PYTHON3=`which python3 || echo $SELF/python3`
${PYTHON3} -u ${SELF}/tnt.py "$@"
