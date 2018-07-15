import os
from pwdzip import pwdzip_reader

from .globals import PASSWORD


###############################################################################
# tests
#

def test_extract(resource_dir, temp_dir):
    zip_file_path = os.path.join(resource_dir, 'all_imgs_with_password.zip')

    content_dir_path = os.path.join(temp_dir, 'content')

    with pwdzip_reader.ZipFileReader(zip_file_path, pwd=PASSWORD) as zf:
        zf.extract('img01.jpg', path=content_dir_path)
        zf.extract('img02.jpg', path=content_dir_path)
        zf.extract('img03.jpg', path=content_dir_path)

        assert {
                   'img01.jpg',
                   'img02.jpg',
                   'img03.jpg',
               } == set(os.listdir(content_dir_path))
