import contextlib
import errno
import json
import os
import re
import shutil
import ssl
import subprocess
import tarfile
from urllib.request import urlopen

import certifi
from email_validator import validate_email, EmailNotValidError


class CommonError(Exception):
    def __init__(self, value):
        self.value_ = value

    def __str__(self):
        return self.value_


def is_valid_email(email: str) -> bool:
    try:
        validate_email(email)
    except EmailNotValidError as e:
        return False

    validate_url = 'https://open.kickbox.com/v1/disposable/' + email
    context = ssl._create_unverified_context()
    response = urlopen(validate_url, context=context)
    if response.status != 200:
        return False

    data = response.read()
    json_object = json.loads(data.decode("utf-8"))
    is_disposable = json_object['disposable']
    return not is_disposable


def is_role_based_email(email: str) -> bool:
    r = re.compile('([^@]+)@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,12})$')
    match = r.match(email)
    if not match:
        return False

    start = match.group(1)
    for x in ['noreply', 'support', 'admin', 'postmaster']:
        if start == x:
            return True

    return False


def read_file_line_by_line_to_list(file) -> list:
    if not os.path.exists(file):
        raise CommonError('file path: {0} not exists'.format(file))

    file_array = []
    with open(file, "r") as ins:
        for line in ins:
            file_array.append(line.strip())

    return file_array


def read_file_line_by_line_to_set(file) -> set:
    if not os.path.exists(file):
        raise CommonError('file path: {0} not exists'.format(file))

    file_set = set()
    with open(file, "r") as ins:
        for line in ins:
            file_set.add(line.strip())

    return file_set


def download_file(url):
    current_dir = os.getcwd()
    file_name = url.split('/')[-1]
    response = urlopen(url, cafile=certifi.where())
    if response.status != 200:
        raise CommonError(
            "Can't fetch url: {0}, status: {1}, response: {2}".format(url, response.status, response.reason))

    f = open(file_name, 'wb')
    file_size = 0
    header = response.getheader("Content-Length")
    if header:
        file_size = int(header)

    print("Downloading: {0} Bytes: {1}".format(file_name, file_size))

    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = response.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        percent = 0 if not file_size else file_size_dl * 100. / file_size
        status = r"%10d  [%3.2f%%]" % (file_size_dl, percent)
        status += chr(8) * (len(status) + 1)
        print(status, end='\r')

    f.close()
    return os.path.join(current_dir, file_name)


def extract_file(path, remove_after_extract=True):
    current_dir = os.getcwd()
    print("Extracting: {0}".format(path))
    try:
        tar_file = tarfile.open(path)
    except Exception as ex:
        raise ex

    target_path = os.path.commonprefix(tar_file.getnames())
    try:
        tar_file.extractall()
    except Exception as ex:
        raise ex
    finally:
        tar_file.close()
        if remove_after_extract:
            os.remove(path)

    return os.path.join(current_dir, target_path)


def git_clone(url: str, branch=None, remove_dot_git=True):
    current_dir = os.getcwd()
    if branch:
        common_git_clone_line = ['git', 'clone', '--branch', branch, '--single-branch', url]
    else:
        common_git_clone_line = ['git', 'clone', '--depth=1', url]
    cloned_dir_name = os.path.splitext(url.rsplit('/', 1)[-1])[0]
    common_git_clone_line.append(cloned_dir_name)
    subprocess.call(common_git_clone_line)
    os.chdir(cloned_dir_name)

    common_git_clone_init_line = ['git', 'submodule', 'update', '--init', '--recursive']
    subprocess.call(common_git_clone_init_line)
    directory = os.path.join(current_dir, cloned_dir_name)
    if remove_dot_git:
        shutil.rmtree(os.path.join(directory, '.git'))
    os.chdir(current_dir)
    return directory


def symlink_force(target, link_name):
    try:
        os.symlink(target, link_name)
    except OSError as e:
        if e.errno == errno.EEXIST:
            os.remove(link_name)
            os.symlink(target, link_name)
        else:
            raise e


# Search for number in array
def binary_search_impl(number, array, lo, hi):
    if hi < lo:
        return False

    mid = (lo + hi) // 2
    if number == array[mid]:
        return True
    elif number < array[mid]:
        return binary_search_impl(number, array, lo, mid - 1)
    else:
        return binary_search_impl(number, array, mid + 1, hi)


def binary_search_number(anum, array):  # convenience interface to binary_search()
    return binary_search_impl(anum, array, 0, len(array) - 1)


def regenerate_dbus_machine_id():
    with contextlib.suppress(FileNotFoundError):
        os.remove('/var/lib/dbus/machine-id')
    with contextlib.suppress(FileNotFoundError):
        os.remove('/etc/machine-id')
    subprocess.call(['dbus-uuidgen', '--ensure'])
