import os
import zipfile

from pwdzip import pwdzip

from .globals import PASSWORD, IMG_DIR_NAME, ZIP_DIR_NAME


###############################################################################
# tests
#

def test_create(resource_dir, temp_dir):
    zip_file_path = os.path.join(temp_dir, 'temp.zip')

    with pwdzip.ZipFile(zip_file_path, mode='w') as zf:
        zf.setpassword(PASSWORD)
        zf.write(os.path.join(resource_dir, IMG_DIR_NAME, 'img01.jpg'), arcname='img01.jpg')

    assert os.path.exists(zip_file_path)
    assert zipfile.is_zipfile(zip_file_path)


def test_list_content(resource_dir, temp_dir):
    zip_file_path = os.path.join(temp_dir, 'temp.zip')

    with pwdzip.ZipFile(zip_file_path, mode='w') as zf:
        zf.setpassword(PASSWORD)
        zf.write(os.path.join(resource_dir, IMG_DIR_NAME, 'img01.jpg'), arcname='img01.jpg')

    with pwdzip.ZipFile(zip_file_path, pwd=PASSWORD) as zf:
        namelist = zf.namelist()

    assert ['img01.jpg'] == namelist


def test_extract(resource_dir, temp_dir):
    zip_file_path = os.path.join(temp_dir, 'temp.zip')

    with pwdzip.ZipFile(zip_file_path, mode='w') as zf:
        zf.setpassword(PASSWORD)
        zf.write(os.path.join(resource_dir, IMG_DIR_NAME, 'img01.jpg'), arcname='img01.jpg')

    content_dir_path = os.path.join(temp_dir, 'content')

    with pwdzip.ZipFile(zip_file_path, pwd=PASSWORD) as zf:
        zf.extract('img01.jpg', path=content_dir_path)

    assert {'img01.jpg'} == set(os.listdir(content_dir_path))


def test_extract_side_file(resource_dir, temp_dir):
    zip_file_path = os.path.join(temp_dir, 'temp.zip')

    with pwdzip.ZipFile(zip_file_path, mode='w', pwd=PASSWORD) as zf:
        zf.write(os.path.join(resource_dir, IMG_DIR_NAME, 'img01.jpg'), arcname='img01.jpg')
        zf.write_side_file(os.path.join(resource_dir, IMG_DIR_NAME, 'img02.jpg'))

    content_dir_path = os.path.join(temp_dir, 'content')

    with pwdzip.ZipFile(zip_file_path, pwd=PASSWORD) as zf:
        zf.extract_side('img02.jpg', path=content_dir_path)

    assert {'img02.jpg'} == set(os.listdir(content_dir_path))


def test_zip_directory(resource_dir, temp_dir):
    zip_file_path = os.path.join(temp_dir, 'temp.zip')

    with pwdzip.ZipFile(zip_file_path, mode='w', pwd=PASSWORD) as zf:
        zf.write(os.path.join(resource_dir, IMG_DIR_NAME), arcname='imgs')

    content_dir_path = os.path.join(temp_dir, 'content')

    with pwdzip.ZipFile(zip_file_path, pwd=PASSWORD) as zf:
        namelist = zf.namelist()
        zf.extractall(path=content_dir_path)

    assert ['imgs/', 'imgs/img01.jpg', 'imgs/img02.jpg', 'imgs/img03.jpg'] == namelist
    assert {'img01.jpg', 'img02.jpg', 'img03.jpg'} == set(os.listdir(os.path.join(content_dir_path, 'imgs')))


def test_zip_side_files(resource_dir, temp_dir):
    zip_file_path = os.path.join(temp_dir, 'temp.zip')

    with pwdzip.ZipFile(zip_file_path, mode='w') as zf:
        zf.setpassword(PASSWORD)
        zf.write(os.path.join(resource_dir, IMG_DIR_NAME, 'img01.jpg'), arcname='img01.jpg')
        zf.write_side_file(os.path.join(resource_dir, IMG_DIR_NAME, 'img02.jpg'))

    with pwdzip.ZipFile(zip_file_path, pwd=PASSWORD) as zf:
        side_name_list = zf.side_name_list()

    assert {'img02.jpg'} == set(side_name_list)


def test_no_protected_archive_write(resource_dir, temp_dir):
    zip_archive_path = os.path.join(temp_dir, 'temp.zip')
    with pwdzip.ZipFile(zip_archive_path, 'w') as zf:
        for img_name in ['img01.jpg', 'img02.jpg', 'img03.jpg']:
            zf.write(os.path.join(resource_dir, IMG_DIR_NAME, img_name), arcname=img_name)

    assert os.path.exists(zip_archive_path)

    with pwdzip.ZipFile(zip_archive_path, 'r') as zf:
        namelist = zf.namelist()

    assert {'img01.jpg', 'img02.jpg', 'img03.jpg'} == set(namelist)


def test_no_protected_archive_read(resource_dir, temp_dir):
    zip_archive_path = os.path.join(resource_dir, ZIP_DIR_NAME, 'all_imgs_no_password.zip')
    with pwdzip.ZipFile(zip_archive_path, 'r') as zf:
        zf.extractall(path=temp_dir)

    assert {'img01.jpg', 'img02.jpg', 'img03.jpg'} == set(os.listdir(temp_dir))
