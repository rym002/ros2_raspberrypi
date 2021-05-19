# ros2 raspberry pi
## Why
Rebuilds ros2 ubuntu images images on raspberry pi using qemu static.
## Setup
### Setup build environment using qemu and systemd-nspawn
* Download the [raspios 64 bit image](https://downloads.raspberrypi.org/raspios_lite_arm64/images/)
* Follow the instructions [here](https://wiki.debian.org/RaspberryPi/qemu-user-static) to expand and mount the image
* Expand the image about 2GB to allow room to update and install tools
### Installs script and build
The build will take time to compile all dependencies.
* mount the loopback partition
* copy the qemu aarch64 static binary to `<image root>/usr/bin`
* `cd <image root>`
* `git clone https://github.com/rym002/ros2_raspberrypi.git`
* `cd ros2_raspberrypi`
* `chmod +x run_image.sh`
* Run the installer in the container 
  * `./run_image.sh <repo path>`
  * The `<repo path>` should be a directory outside the image to store the build and compiled artifacts.
  * The script will create this directory
  * The directory should be the **full path**, not relative
  * This will run systemd-nspawn for the builder script
* Wait ....
#### What happening
* Downloads the source from each build and install dependency.
* Builds modules as the raspberry pi os release
* Installs debs in a local repo
# Installing on raspberry pi
This can be done on an existing or clean raspberry pi. Perform these steps on the raspberry pi
* `sudo apt-get install git`
* `git clone https://github.com/rym002/ros2_raspberrypi.git`
* `cd ros2_raspberrypi`
* `chmod +x sync_repo.sh`
* sync the repo and setup apt
  * `./sync_repo.sh <remote user>@<remote host> <remote repo path> <remote image root>`
    * `remote user` - user on the host system
    * `remote host` - hostname where the build was run
    * `remote repo path` - full path on the remote host used run the build
    * `remote image root` - full path to the root of the raspberry pi image on the remote host
  * enter the password for the remote host (2x)
* `apt-get install ros-foxy-ros-base` or any other ros package
