#!/bin/bash

# Used to sync the remote repository
# Usage:
# sudo sync_repo.sh <remote user>@<remote host> <remote repo path> <remote image root>

if [[ $# -ne 3 ]]
then
    echo "Usage: $(basename $0) <remote user>@<remote host> <remote repo path> <remote image root>"
    exit 1
fi

echo "Syncing repo"
LOCAL_REPO=/var/cache/ros_repo
mkdir -p ${LOCAL_REPO}
sudo rsync --progress --recursive ${1}:${2}/repository ${LOCAL_REPO}

if [[ $? -ne 0 ]]
then
    echo "Error syncing repo"
fi

SOURCE_LIST_PATH=/etc/apt/sources.list.d/
echo "Syncing sources.list"
sudo rsync --progress --recursive ${1}:${3}${SOURCE_LIST_PATH}ros* ${SOURCE_LIST_PATH}

if [[ $? -ne 0 ]]
then
    echo "Error syncing sources.list"
fi

GPG_FILE=/usr/share/keyrings/ros-archive-keyring.gpg
if [[ ! -f ${GPG_FILE} ]]
then
    sudo wget https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -O ${GPG_FILE}
fi

sudo apt-get update