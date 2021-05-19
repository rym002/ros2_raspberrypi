#!/bin/python3

import subprocess
import os
from os import path
import shutil
import argparse

ROS_PACKAGE = "ros-foxy-ros-base"

class EnvironmentManager:
    LOCAL_GPG='/usr/share/keyrings/ros-archive-keyring.gpg'
    SOURCE_PATH='/etc/apt/sources.list.d/'
    LOCAL_REPO_BASE='/var/cache/ros_repo/'
    BUILD_DIR=LOCAL_REPO_BASE + 'build'
    LOCAL_REPO_DIR=LOCAL_REPO_BASE + 'repository'

    def __init__(self, parsed_args):
        process = subprocess.run(['lsb_release', '-c', '-s'],
            stdout=subprocess.PIPE, universal_newlines=True,check=True)
        self.release=process.stdout.split('\n')[0]
        self.ros_modules = dict()
        self.parsed_args = parsed_args

    def find_or_create_module(self,name):
        if self.ros_modules.__contains__(name):
            ros_module = self.ros_modules[name]
        else:
            ros_module = RosModule(name)
            self.ros_modules[name]=ros_module
        return ros_module
    def download_ros_key(self):
        if not(path.exists(EnvironmentManager.LOCAL_GPG)):
            process = subprocess.run(['wget',self.parsed_args.gpg_key_url,'-O',
                EnvironmentManager.LOCAL_GPG],check=True,stderr=subprocess.DEVNULL,stdout=subprocess.DEVNULL)
        else:
            print('Key already exists {}'.format(EnvironmentManager.LOCAL_GPG))

    def create_sources_list(self, name, type, distro):
            url = "{type} [signed-by={gpg}] {repo_url} {distro} {component}\n".format(type=type,gpg=EnvironmentManager.LOCAL_GPG,
                repo_url=self.parsed_args.repo_url,distro=distro, component=self.parsed_args.component)
            return self.write_sources_list(name,url)

    def write_sources_list(self,name, url):
        list_file = EnvironmentManager.SOURCE_PATH + name
        if not path.exists(list_file):
            file = open(list_file,'w',encoding='utf-8')
            file.write(url)
            file.close()
            return True
        else:
            print('Source list exists, skipping create', list_file)
            return False

    def delete_sources_list(self,name):
        list_file = EnvironmentManager.SOURCE_PATH + name
        if path.exists(list_file):
            os.remove(list_file)
        else:
            print('Source list doesnt exists, skipping delete', list_file)
    
    def create_ros_deb_src(self):
        self.create_sources_list('ros2_src.list','deb-src',self.parsed_args.src_distro)

    def create_ros_deb_release(self):
        self.create_sources_list('ros2.list','deb',self.release)

    def prepare_env(self):
        self.download_ros_key()
        upd = self.create_ros_deb_src()
        upd = self.create_ros_deb_release() or upd
        upd = self.create_local_repo() or upd
        if upd:
            print('running apt update')
            self.run_apt_get('update')
        # libssl-dev needed by ros-foxy-fastrtps
        self.run_apt_get('install', ['devscripts', 'apt-src', 'libssl-dev'])
        self.download_misc_debs()

    def run_apt_get(self, command, packages=None):
        apt_args = {
            'check':True,
            'stdout':subprocess.PIPE,
            'stderr':subprocess.PIPE,
            'universal_newlines':True,
            'cwd':EnvironmentManager.BUILD_DIR
        }
        if packages==None:
            process = subprocess.run(['apt-get',command], **apt_args)
        else:
            process = subprocess.run(['apt-get','--yes',command] + packages, **apt_args)
        return process
    
    def create_local_repo(self):
        os.makedirs(EnvironmentManager.BUILD_DIR,exist_ok=True)
        os.makedirs(EnvironmentManager.LOCAL_REPO_DIR,exist_ok=True)
        self.scan_packages()
        repo_url = 'deb [trusted=yes] file://{} ./'.format(EnvironmentManager.LOCAL_REPO_DIR)
        return self.write_sources_list('ros2_local.list',repo_url)
    
    def scan_packages(self):
        with open(EnvironmentManager.LOCAL_REPO_DIR + '/Packages','w') as packages:
            subprocess.run(['dpkg-scanpackages', '.'], 
                stdout=packages, check=True, stderr=subprocess.DEVNULL, cwd=EnvironmentManager.LOCAL_REPO_DIR)    
                
    def download_misc_debs(self):
        if not(path.exists(EnvironmentManager.LOCAL_REPO_DIR +'/rti-connext-dds-5.3.1_0.0.0-0_arm64.deb')):
            subprocess.run(['wget','http://packages.ros.org/ros2/ubuntu/pool/main/r/rti-connext-dds-5.3.1/rti-connext-dds-5.3.1_0.0.0-0_arm64.deb'],
                check=True, cwd=EnvironmentManager.LOCAL_REPO_DIR,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        else:
            print('rti-connext-dds-5.3.1_0.0.0-0_arm64.deb already downloaded')

envManager = None

class RosModule:
    def __init__(self,name):
        super().__init__()
        self.name = name
        self.install = set()
        self.build = set()
        self.built = False
        self.src_dir = None
        self.verson = None
        self.deb_file = None

    dots = 0

    def __eq__(self, value):
        return self.name == value.name

    def __hash__(self):
        return hash(self.name)
    
    def all_modules_built(self, dep_modules):
        ret = True
        for dep in dep_modules:
            ret &= dep.built
            if ret==False:
                print(dep.name)
                break
        return ret

    def can_install_ros_module(self):
        return self.all_modules_built(self.install)

    def can_build_ros_module(self):
        return self.all_modules_built(self.build)

    def log(self, message):
        print('{:.>{dots}} {}: {}'.format('', self.name, message, dots=RosModule.dots))

    def install_build_deps(self):
        self.log('Install build deps module')
        process = envManager.run_apt_get('build-dep',[self.name])

    def retrieve_module_source(self):
        self.log('Downloading module source')
        self.run_apt_src('install')
        loc_proc = self.run_apt_src('location')
        self.src_dir = envManager.BUILD_DIR + loc_proc.stdout.split('\n')[0][1:]

    def update_deb_changelog(self):
        patches = {
            envManager.parsed_args.src_distro : envManager.release
        }
        self.patch_debian_file('changelog',patches)

    def build_deb_pkg(self):
        self.log('Building deb package')
        self.run_apt_src('build')
        ver_proc = self.run_apt_src('version')
        self.verson = ver_proc.stdout.split('\n')[0]
        self.deb_file = self.name + '_' + self.verson + '_arm64.deb'
    
    def move_deb_pkg(self):
        deb_location = EnvironmentManager.BUILD_DIR + path.sep + self.deb_file
        if path.exists(deb_location):
            shutil.move(deb_location,
                EnvironmentManager.LOCAL_REPO_DIR)
        else:
            raise RuntimeError('Cannot find deb ' + self.deb_file)

    def scan_packages(self):
        envManager.scan_packages()

    def package_ros_module(self):    
        self.log('Start Building module')
        if self.can_build_ros_module():   
            self.install_build_deps()
            self.retrieve_module_source()
            self.patch_control()
            self.patch_rules()
            self.update_deb_changelog()
            self.build_deb_pkg()
            self.move_deb_pkg()
            self.scan_packages()
            self.run_apt_src('remove')
            self.built = True
        else:
            print(self.build)
            raise RuntimeError('Unable to build module {}'.format(self.name))
        self.log('Complete Building module')

    def apt_install_ros_module(self):
        self.prepare_ros_module()
        self.log('Installing module')
        envManager.run_apt_get('install',[self.name])

    def prepare_build_deps(self):
        self.parse_dependencies(True)
        self.log('Checking build deps')
        for build_dep in self.build:
            if not(build_dep.built):
                build_dep.prepare_ros_module()


    def prepare_install_deps(self):
        self.parse_dependencies(False)
        self.log('Checking install deps')
        for install_dep in self.install:
            if not(install_dep.built):
                install_dep.prepare_ros_module()

        if not self.can_install_ros_module():   
            raise RuntimeError('Unsatisified install dependency for module {}'.format(self.name))

    def prepare_ros_module(self):
        RosModule.dots += 1
        if not(self.check_built()):
            self.prepare_build_deps()
            self.package_ros_module()
        else:
            self.built=True
            self.log('Already built')
        self.prepare_install_deps()
        RosModule.dots -= 1

    def check_built(self):
        try:
            process = subprocess.run(['apt-cache', 'show', self.name],
                check=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,universal_newlines=True)
            return process.stdout.startswith('Package:')
        except:
            return False
    
    def run_apt_src(self, command):
        return subprocess.run(['apt-src',command,self.name],
            stdout=subprocess.PIPE,stderr=subprocess.DEVNULL, check=True,cwd=envManager.BUILD_DIR, universal_newlines=True)
    
    def run_apt(self,command):
        return subprocess.run(['apt',command,self.name],
            stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=True,cwd=envManager.BUILD_DIR, universal_newlines=True)
    
    def parse_dependencies(self, parse_build_deps = False):
        command = 'showsrc' if parse_build_deps else 'show'
        process = self.run_apt(command)
        output = process.stdout
        dependency_type = 'Build-Depends' if parse_build_deps else 'Depends'
        module_type = 'build' if parse_build_deps else 'install'
        for line in output.split('\n'):
            if (line.startswith(dependency_type)):
                dependencies_line = line.split(': ')[1]
                depdependencies = dependencies_line.split(', ')
                for dependency in depdependencies:
                    dependency = dependency.split(' ')[0]
                    if dependency.startswith('ros-'):
                        depModule = envManager.find_or_create_module(dependency)
                        getattr(self,module_type).add(depModule)
                break

    def patch_control(self):
        patches = {
            'python3-lark,' : 'python3-lark-parser,'
        }
        file_name = 'control'
        self.patch_debian_file(file_name,patches)

    def patch_rules(self):
        patches = {
            'python3.8' : 'python3.7'
        }
        file_name = 'rules'
        self.patch_debian_file(file_name,patches)
    def patch_debian_file(self,file_name,patches):
        file_path = self.src_dir + path.sep + 'debian' + path.sep + file_name
        has_patch = False
        with open(file_path,'r') as rfile:
            file_info = rfile.read()

            for search, replace in patches.items():
                has_cur_patch = file_info.__contains__(search)
                if has_cur_patch:
                    has_patch=True
                    updated_file=file_info.replace(search,replace)
        if has_patch:
            self.log('Patching ' + file_name)
            with open(file_path,'w') as wfile:
                wfile.writelines(updated_file)

def handle_args():
    ap=argparse.ArgumentParser()
    ap.add_argument('--package',required=False,default='ros-foxy-ros-base',help='package to install')
    ap.add_argument('--src-distro',required=False,default='focal',help='debian distro name')
    ap.add_argument('--component',required=False,default='main',help='debian components e.g. main')
    ap.add_argument('--repo-url',required=False,default='http://packages.ros.org/ros2/ubuntu',help='url of ros repo')
    ap.add_argument('--gpg-key-url',required=False,default='https://raw.githubusercontent.com/ros/rosdistro/master/ros.key',
        help='url of th gpg key')
    return ap.parse_args()

def build_and_install(parsed_args):
    global envManager
    envManager = EnvironmentManager(parsed_args)
    envManager.prepare_env()
    ros_module = envManager.find_or_create_module(parsed_args.package)
    ros_module.apt_install_ros_module()


def main():
    parsed_args = handle_args()
    print('args:',parsed_args)
    build_and_install(parsed_args)

if __name__ =="__main__":
    main()