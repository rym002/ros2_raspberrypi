#!/bin/bash

# launches the image to install

if [[ $# -lt 2 ]]
then
    echo "Usage: $(basename $0) <image path> <host repo path> ...<optional install args>"
    exit 1
fi

IMAGE_PATH=$1
HOST_REPO_PATH=$2
shift 2
if [[ ! -f ${HOST_REPO_PATH} ]]
then
    mkdir -p ${HOST_REPO_PATH}
fi

SCRIPT_PATH=`dirname $(realpath $0)`
SCRIPT_DIR=/`basename ${SCRIPT_PATH}`
IMAGE_REPO_PATH=/var/cache/ros_repo

sudo cp $(which qemu-aarch64) ${IMAGE_PATH}/usr/bin
sudo systemd-nspawn --bind=${HOST_REPO_PATH}:${IMAGE_REPO_PATH} --bind=${SCRIPT_PATH}:${SCRIPT_DIR} -D ${IMAGE_PATH}  ${SCRIPT_DIR}/ros_rpi_builder.py $@