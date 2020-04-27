import os
import platform
import subprocess
from abc import ABCMeta, abstractmethod

import distro


class Architecture(object):
    def __init__(self, arch: str, bit: int, default_install_prefix_path: str):
        self.name_ = arch
        self.bit_ = bit
        self.default_install_prefix_path_ = default_install_prefix_path

    def name(self) -> str:
        return self.name_

    def bit(self) -> int:
        return self.bit_

    def default_install_prefix_path(self) -> str:
        return self.default_install_prefix_path_


class Platform(metaclass=ABCMeta):
    def __init__(self, name: str, architecture: Architecture, package_types: list):
        self.name_ = name
        self.architecture_ = architecture
        self.package_types_ = package_types

    def name(self) -> str:
        return self.name_

    def architecture(self) -> Architecture:
        return self.architecture_

    def package_types(self) -> list:
        return self.package_types_

    @abstractmethod
    def install_package(self, name: str):
        pass

    def env_variables(self) -> dict:
        return {}

    def cmake_specific_flags(self) -> list:
        return []

    def configure_specific_flags(self) -> list:
        return []


class SupportedPlatforms(metaclass=ABCMeta):
    def __init__(self, name: str, architectures: [Architecture], package_types: list):
        self.name_ = name
        self.architectures_ = architectures
        self.package_types_ = package_types

    def name(self) -> str:
        return self.name_

    def architectures(self) -> [Architecture]:
        return self.architectures_

    def package_types(self) -> list:
        return self.package_types_

    def get_architecture_by_arch_name(self, name: str) -> Architecture:
        return next((x for x in self.architectures_ if x.name() == name), None)

    @abstractmethod
    def make_platform_by_arch(self, arch: Architecture, package_types: list) -> Platform:  # factory method
        pass


def linux_get_dist():
    """
    Return the running distribution group
    RHEL: RHEL, CENTOS, FEDORA
    DEBIAN: UBUNTU, DEBIAN, LINUXMINT
    """
    linux_tuple = distro.linux_distribution()
    dist_name = linux_tuple[0]
    dist_name_upper = dist_name.upper()

    if dist_name_upper.startswith(("RHEL", "CENTOS LINUX", "FEDORA", "AMAZON LINUX")):
        return "RHEL"
    elif dist_name_upper.startswith(("DEBIAN", "UBUNTU", "LINUX MINT", "RASPBIAN GNU/LINUX")):
        return "DEBIAN"
    elif dist_name_upper.startswith(("ARCH")):
        return "ARCH"
    raise NotImplemented("Unknown platform '%s'" % dist_name)


# Linux platforms

class DebianPlatform(Platform):
    def __init__(self, arch: Architecture, package_types: list):
        Platform.__init__(self, 'linux', arch, package_types)

    def install_package(self, name: str):
        subprocess.call(['apt-get', '-y', '--no-install-recommends', 'install', name])


class RedHatPlatform(Platform):
    def __init__(self, arch: Architecture, package_types: list):
        Platform.__init__(self, 'linux', arch, package_types)

    def install_package(self, name: str):
        subprocess.call(['yum', '-y', 'install', name])


class ArchPlatform(Platform):
    def __init__(self, arch: Architecture, package_types: list):
        Platform.__init__(self, 'linux', arch, package_types)

    def install_package(self, name: str):
        subprocess.call(['pacman', '-S', '--noconfirm', name])


class LinuxPlatforms(SupportedPlatforms):
    def __init__(self):
        SupportedPlatforms.__init__(self, 'linux', [Architecture('x86_64', 64, '/usr/local'),
                                                    Architecture('i386', 32, '/usr/local'),
                                                    Architecture('i686', 32, '/usr/local'),
                                                    Architecture('aarch64', 64, '/usr/local'),
                                                    Architecture('armv7l', 32, '/usr/local'),
                                                    Architecture('armv6l', 32, '/usr/local')],
                                    ['DEB', 'RPM', 'TGZ'])

    def make_platform_by_arch(self, arch: Architecture, package_types: list) -> Platform:
        distr = linux_get_dist()
        if distr == 'DEBIAN':
            return DebianPlatform(arch, package_types)
        elif distr == 'RHEL':
            return RedHatPlatform(arch, package_types)
        elif distr == 'ARCH':
            return ArchPlatform(arch, package_types)
        raise NotImplemented("Unknown distribution '%s'" % distr)


# Windows platforms
class WindowsMingwPlatform(Platform):
    def __init__(self, arch: Architecture, package_types: list):
        Platform.__init__(self, 'windows', arch, package_types)

    def install_package(self, name: str):
        subprocess.call(['pacman', '-S', '--noconfirm', name])


class WindowsPlatforms(SupportedPlatforms):
    def __init__(self):
        SupportedPlatforms.__init__(self, 'windows',
                                    [Architecture('x86_64', 64, '/mingw64'),
                                     Architecture('AMD64', 64, '/mingw64'),
                                     Architecture('i386', 32, '/mingw32'),
                                     Architecture('i686', 32, '/mingw32')],
                                    ['NSIS', 'ZIP'])

    def make_platform_by_arch(self, arch: Architecture, package_types: list) -> Platform:
        return WindowsMingwPlatform(arch, package_types)


# MacOSX platforms
class MacOSXCommonPlatform(Platform):
    def __init__(self, arch: Architecture, package_types: list):
        Platform.__init__(self, 'macosx', arch, package_types)

    def install_package(self, name: str):
        subprocess.call(['port', '-N', 'install', name])


class MacOSXPlatforms(SupportedPlatforms):
    def __init__(self):
        SupportedPlatforms.__init__(self, 'macosx', [Architecture('x86_64', 64, '/usr/local')], ['DragNDrop', 'ZIP'])

    def make_platform_by_arch(self, arch: Architecture, package_types: list) -> Platform:
        return MacOSXCommonPlatform(arch, package_types)


# FreeBSD platforms
class FreeBSDCommonPlatform(Platform):
    def __init__(self, arch: Architecture, package_types: list):
        Platform.__init__(self, 'freebsd', arch, package_types)

    def install_package(self, name: str):
        subprocess.call(['pkg', 'install', '-y', name])


class FreeBSDPlatforms(SupportedPlatforms):
    def __init__(self):
        SupportedPlatforms.__init__(self, 'freebsd', [Architecture('x86_64', 64, '/usr/local'),
                                                      Architecture('amd64', 64, '/usr/local')], ['TGZ'])

    def make_platform_by_arch(self, arch: Architecture, package_types: list) -> Platform:
        return FreeBSDCommonPlatform(arch, package_types)


# Android platforms
ANDROID_PLATFORM_NUMBER = 16
ANDROID_PLATFORM = 'android-%s' % ANDROID_PLATFORM_NUMBER
ANDROID_NDK = '~/Android/Sdk/ndk-bundle'


class AndroidCommonPlatform(Platform):
    def __init__(self, arch: Architecture, package_types: list):
        Platform.__init__(self, 'android', arch, package_types)

    def install_package(self, name: str):
        raise NotImplementedError('You need to define a install_package method!')

    def env_variables(self) -> dict:
        arch = self.architecture()
        abs_prefix_path = os.path.expanduser(ANDROID_NDK)
        return {
            'CC': '{0}/toolchains/llvm/prebuilt/linux-x86_64/bin/{1}-linux-androideabi{2}-clang'.format(abs_prefix_path,
                                                                                                        arch.name(),
                                                                                                        ANDROID_PLATFORM_NUMBER),
            'CXX': '{0}/toolchains/llvm/prebuilt/linux-x86_64/bin/{1}-linux-androideabi{2}-clang++'.format(
                abs_prefix_path, arch.name(), ANDROID_PLATFORM_NUMBER)}

    def cmake_specific_flags(self) -> list:
        abs_prefix_path = os.path.expanduser(ANDROID_NDK)
        return ['-DCMAKE_TOOLCHAIN_FILE=%s/build/cmake/android.toolchain.cmake' % abs_prefix_path,
                '-DANDROID_PLATFORM=%s' % ANDROID_PLATFORM]

    def configure_specific_flags(self) -> list:
        arch = self.architecture()
        return ['--host=%s-linux-androideabi' % arch.name()]


class AndroidPlatforms(SupportedPlatforms):
    def __init__(self):
        SupportedPlatforms.__init__(self, 'android',
                                    [Architecture('armv7a', 32,
                                                  ANDROID_NDK + '/platforms/' + ANDROID_PLATFORM + '/arch-arm/usr/'),
                                     Architecture('i686', 32,
                                                  ANDROID_NDK + '/platforms/' + ANDROID_PLATFORM + '/arch-x86/usr/'),
                                     Architecture('x86_64', 64,
                                                  ANDROID_NDK + '/platforms/' + ANDROID_PLATFORM + '/arch-x86/usr/'),
                                     Architecture('aarch64', 64,
                                                  ANDROID_NDK + '/platforms/' + ANDROID_PLATFORM + '/arch-x86/usr/')],
                                    ['APK'])

    def make_platform_by_arch(self, arch: Architecture, package_types: list) -> Platform:
        return AndroidCommonPlatform(arch, package_types)


SUPPORTED_PLATFORMS = [LinuxPlatforms(), WindowsPlatforms(), MacOSXPlatforms(), FreeBSDPlatforms(), AndroidPlatforms()]


def get_extension_by_package(package_type) -> str:
    if package_type == 'DEB':
        return 'deb'
    elif package_type == 'RPM':
        return 'rpm'
    elif package_type == 'TGZ':
        return 'tar.gz'
    elif package_type == 'NSIS':
        return 'exe'
    elif package_type == 'ZIP':
        return 'zip'
    elif package_type == 'DragNDrop':
        return 'dmg'
    elif package_type == 'APK':
        return 'apk'
    else:
        return 'unknown'


def get_os() -> str:
    uname_str = platform.system()
    if 'MINGW' in uname_str:
        return 'windows'
    elif 'MSYS' in uname_str:
        return 'windows'
    elif uname_str == 'Windows':
        return 'windows'
    elif uname_str == 'Linux':
        return 'linux'
    elif uname_str == 'Darwin':
        return 'macosx'
    elif uname_str == 'FreeBSD':
        return 'freebsd'
    elif uname_str == 'Android':
        return 'android'
    else:
        return 'unknown'


def get_arch_name() -> str:
    return platform.machine()


def get_supported_platform_by_name(name: str) -> SupportedPlatforms:
    return next((x for x in SUPPORTED_PLATFORMS if x.name() == name), None)


def stable_path(path: str) -> str:
    if get_os() == 'windows':
        return path.replace("\\", "/")

    return path.replace("\\", "/")
