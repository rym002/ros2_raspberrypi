#!/bin/bash

# launches the image to install

if [[ $# -lt 1 ]]
then
    echo "Usage: $(basename $0) <host repo path> ...<optional install args>"
    exit 1
fi

HOST_REPO_PATH=$1
shift
if [[ ! -f ${HOST_REPO_PATH} ]]
then
    mkdir -p ${HOST_REPO_PATH}
fi

SCRIPT_PATH=`dirname $(realpath $0)`
SCRIPT_DIR=`basename ${SCRIPT_PATH}`
IMAGE_PATH=`dirname ${SCRIPT_PATH}`
IMAGE_REPO_PATH=/var/cache/ros_repo

sudo systemd-nspawn --bind=${HOST_REPO_PATH}:${IMAGE_REPO_PATH} -D ${IMAGE_PATH}  ${SCRIPT_DIR}/ros_rpi_builder.py $@