# ros2 raspberry pi
## Why
Rebuilds ros2 ubuntu images images on raspberry pi using qemu static.
## Setup
### Setup build environment using qemu and systemd-nspawn
* Download the [raspios 64 bit image](https://downloads.raspberrypi.org/raspios_lite_arm64/images/)
* Follow the instructions [here](https://wiki.debian.org/RaspberryPi/qemu-user-static) to expand and mount the image
* Expand the image about 2GB to allow room to update and install tools
### Installs script and build
* Copy the installer script `ros_rpi_installer.py` to the image
* Make a folder on the host to store images and build artifacts.
  * The image can be expanded larger, but it would need to be enough to store all source and binaries. The external directory can allow use with multiple images.
* Run `sudo systemd-nspawn --bind=<path to host folder>:/var/cache/ros_repo -D <image root> ros_rpi_installer.py`
## What happening
* Downloads the source from each build and install dependency.
* Builds modules as the raspberry pi os release
* Installs debs in a local repo 