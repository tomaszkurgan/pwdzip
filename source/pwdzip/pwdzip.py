"""Minimal implementation of zip with password"""

import StringIO
import os
import shutil
import subprocess
import tempfile
import uuid
import zipfile

_7Z_BIN_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), 'bin', '7z'))
_7Z_EXE = os.path.join(_7Z_BIN_DIR, '7za.exe')


def _run_7z(command, switches, args):
    cmd = [_7Z_EXE] + [command] + switches + args
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    if p.returncode > 1:
        _, err = p.communicate()
        raise RuntimeError(err)


class ZipFile(zipfile.ZipFile):
    def __init__(self, filename, mode='r', compression=zipfile.ZIP_STORED, allowZip64=False, pwd=None):
        super(ZipFile, self).__init__(filename, mode, compression, allowZip64)
        self.setpassword(pwd)

        self._payload_name = None
        self._payload = None
        self._get_payload()

        if self.mode == 'a' and self._payload:
            raise RuntimeError('Cannot append item into password protected archive.')

        self._side_files = []

    def _get_payload(self):
        if self.mode != 'r':
            return None

        zip_files = [f for f in self.namelist() if os.path.splitext(f)[1] == '.zip']
        if len(zip_files) != 1:
            return None

        self._payload_name = zip_files[0]
        payload_info = self.getinfo(self._payload_name)
        is_encrypted = payload_info.flag_bits & 0x1
        if not is_encrypted:
            return None

        zip_dir_name = uuid.uuid4().hex.upper()[:16]
        temp_dir = os.path.join(tempfile.gettempdir(), zip_dir_name)

        _run_7z(
            command='e',
            switches=[
                '-y',
                '-r',
                '-p%s' % self.pwd,
                '-o%s' % temp_dir,
            ],
            args=[self.filename, self._payload_name]
        )

        temp_zip_file_path = os.path.join(temp_dir, self._payload_name)
        payload_buffer = StringIO.StringIO()
        with open(temp_zip_file_path, 'rb') as f:
            payload_buffer.write(f.read())

        try:
            shutil.rmtree(temp_dir)
        except OSError:
            shutil.rmtree(temp_dir)

        self._payload = zipfile.ZipFile(payload_buffer)

    def _wrap_with_password(self):
        # See: https://sevenzip.osdn.jp/chm/cmdline/
        orig_path = self.filename
        orig_basename, _ = os.path.splitext(os.path.basename(orig_path))

        hash_suffix = uuid.uuid4().hex.upper()[:8]
        temp_archive_name = '{basename}_{hash}.zip'.format(basename=orig_basename, hash=hash_suffix)

        temp_archive_path = os.path.join(os.path.dirname(os.path.dirname(self.filename)), temp_archive_name)

        _run_7z(
            command='a',
            switches=[
                '-y',  # Assume Yes on all queries
                '-mx=0',  # Set compression Method: Sets level of compression to 0 (copy mode - no compression)
                # '-sdel', # Delete files after including to archive
                '-p%s' % self.pwd,  # Password
            ],
            args=[temp_archive_path, orig_path] + self._side_files
        )

        shutil.move(temp_archive_path, orig_path)

    def side_name_list(self):
        name_list = super(ZipFile, self).namelist()
        name_list.remove(self._payload_name)
        return name_list

    def write_side_file(self, filename):
        self._side_files.append(filename)

    def write(self, filename, arcname=None, compress_type=None):
        super(ZipFile, self).write(filename, arcname, compress_type)
        if not os.path.isdir(filename):
            return

        for i, (root, dirs, files) in enumerate(os.walk(filename)):
            # skip first root (equals to filename), because it's already written
            items = [root] + files if i else files

            for item in items:
                item_path = os.path.join(root, item)
                item_arcname = os.path.join(arcname, os.path.relpath(item_path, filename))
                super(ZipFile, self).write(item_path, item_arcname, compress_type)

    def close(self):
        if self.fp is None:
            return

        super(ZipFile, self).close()

        if self.pwd and self.mode == 'w':
            self._wrap_with_password()

    ###############################################################################
    # redirect methods into internal archive
    #

    def _redirect_to_payload(self, func, *args, **kwargs):
        func_name = func.__name__
        if self._payload:
            return getattr(self._payload, func_name)(*args, **kwargs)
        return getattr(super(ZipFile, self), func_name)(*args, **kwargs)

    def namelist(self):
        return self._redirect_to_payload(self.namelist)

    def printdir(self):
        return self._redirect_to_payload(self.printdir)

    def testzip(self):
        return self._redirect_to_payload(self.testzip)

    def infolist(self):
        return self._redirect_to_payload(self.infolist)

    def getinfo(self, name):
        return self._redirect_to_payload(self.getinfo, name)

    def read(self, name, pwd=None):
        return self._redirect_to_payload(self.read, name, pwd)

    def extract(self, member, path=None, pwd=None):
        return self._redirect_to_payload(self.extract, member, path, pwd)

    def extractall(self, path=None, members=None, pwd=None):
        return self._redirect_to_payload(self.extractall, path, members, pwd)
