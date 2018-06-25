import datetime
import errno
import os
import shutil
import time
import zipfile

import pytest

import pwdzip

SELF_DIR = os.path.dirname(__file__)

PASSWORD = 'mrvuNcHxp25N'

TEMP_DIR = os.path.join(SELF_DIR, 'temp')

RESOURCES_DIR = os.path.join(SELF_DIR, 'resources')
IMG_DIR = os.path.join(RESOURCES_DIR, 'img')
ZIP_DIR = os.path.join(RESOURCES_DIR, 'zip')


###############################################################################
# fixtures
#


@pytest.fixture(scope='function')
def temp_dir(request):
    function_name = request.function.__name__
    temp_dir_path = os.path.join(TEMP_DIR, function_name)

    try:
        shutil.rmtree(temp_dir_path)
    except OSError as e:
        if e.errno == errno.ENOENT:
            pass

    os.makedirs(temp_dir_path)

    yield temp_dir_path

    if request.node.rep_setup.passed:
        if request.node.rep_call.passed:
            try:
                shutil.rmtree(temp_dir_path)
            except OSError:
                time.sleep(.5)
                shutil.rmtree(temp_dir_path)
        else:
            now = datetime.datetime.now().strftime('%y%m%d_%H%M%S')
            shutil.move(temp_dir_path, '%s_%s' % (temp_dir_path, now))


###############################################################################
# tests
#

def test_create(temp_dir):
    zip_file_path = os.path.join(temp_dir, 'temp.zip')

    with pwdzip.ZipFile(zip_file_path, mode='w') as zf:
        zf.setpassword(PASSWORD)
        zf.write(os.path.join(IMG_DIR, 'img01.jpg'), arcname='img01.jpg')

    assert os.path.exists(zip_file_path)
    assert zipfile.is_zipfile(zip_file_path)


def test_list_content(temp_dir):
    zip_file_path = os.path.join(temp_dir, 'temp.zip')

    with pwdzip.ZipFile(zip_file_path, mode='w') as zf:
        zf.setpassword(PASSWORD)
        zf.write(os.path.join(IMG_DIR, 'img01.jpg'), arcname='img01.jpg')

    with pwdzip.ZipFile(zip_file_path, pwd=PASSWORD) as zf:
        namelist = zf.namelist()

    assert ['img01.jpg'] == namelist


def test_extract(temp_dir):
    zip_file_path = os.path.join(temp_dir, 'temp.zip')

    with pwdzip.ZipFile(zip_file_path, mode='w') as zf:
        zf.setpassword(PASSWORD)
        zf.write(os.path.join(IMG_DIR, 'img01.jpg'), arcname='img01.jpg')

    content_dir_path = os.path.join(temp_dir, 'content')

    with pwdzip.ZipFile(zip_file_path, pwd=PASSWORD) as zf:
        zf.extract('img01.jpg', path=content_dir_path)

    assert ['img01.jpg'] == os.listdir(content_dir_path)


def test_zip_directory(temp_dir):
    zip_file_path = os.path.join(temp_dir, 'temp.zip')

    with pwdzip.ZipFile(zip_file_path, mode='w') as zf:
        zf.setpassword(PASSWORD)
        zf.write(IMG_DIR, arcname='imgs')

    content_dir_path = os.path.join(temp_dir, 'content')

    with pwdzip.ZipFile(zip_file_path, pwd=PASSWORD) as zf:
        namelist = zf.namelist()
        zf.extractall(path=content_dir_path)

    assert ['imgs/', 'imgs/img01.jpg', 'imgs/img02.jpg', 'imgs/img03.jpg'] == namelist
    assert {'img01.jpg', 'img02.jpg', 'img03.jpg'} == set(os.listdir(os.path.join(content_dir_path, 'imgs')))


def test_zip_side_files(temp_dir):
    zip_file_path = os.path.join(temp_dir, 'temp.zip')

    with pwdzip.ZipFile(zip_file_path, mode='w') as zf:
        zf.setpassword(PASSWORD)
        zf.write(os.path.join(IMG_DIR, 'img01.jpg'), arcname='img01.jpg')
        zf.write_side_file(os.path.join(IMG_DIR, 'img02.jpg'))

    with pwdzip.ZipFile(zip_file_path, pwd=PASSWORD) as zf:
        side_name_list = zf.side_name_list()

    assert {'img02.jpg'} == set(side_name_list)


def test_no_protected_archive_write(temp_dir):
    zip_archive_path = os.path.join(temp_dir, 'temp.zip')
    with pwdzip.ZipFile(zip_archive_path, 'w') as zf:
        for img_name in ['img01.jpg', 'img02.jpg', 'img03.jpg']:
            zf.write(os.path.join(IMG_DIR, img_name), arcname=img_name)

    assert os.path.exists(zip_archive_path)

    with pwdzip.ZipFile(zip_archive_path, 'r') as zf:
        namelist = zf.namelist()

    assert {'img01.jpg', 'img02.jpg', 'img03.jpg'} == set(namelist)


def test_no_protected_archive_read(temp_dir):
    zip_archive_path = os.path.join(ZIP_DIR, 'all_imgs_no_password.zip')
    with pwdzip.ZipFile(zip_archive_path, 'r') as zf:
        zf.extractall(path=temp_dir)

    assert {'img01.jpg', 'img02.jpg', 'img03.jpg'} == set(os.listdir(temp_dir))
