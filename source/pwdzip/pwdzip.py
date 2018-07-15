"""Main implementation of password protected zip file."""

import os
import shutil
import subprocess
import uuid
import zipfile

from . import pwdzip_reader

_7Z_BIN_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), 'bin', '7z'))
_7Z_EXE = os.path.join(_7Z_BIN_DIR, '7za.exe')


def _run_7z(command, switches, args):
    cmd = [_7Z_EXE] + [command] + switches + args
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    if p.returncode > 1:
        _, err = p.communicate()
        raise RuntimeError(err)


class ZipFile(pwdzip_reader.ZipFileReader):
    SUPPORTED_MODES = ('r', 'w', 'a')

    def __init__(self, filename, mode='r', compression=zipfile.ZIP_STORED, allowZip64=False, pwd=None):
        super(ZipFile, self).__init__(filename, mode, compression, allowZip64, pwd=pwd)

        if self.mode == 'a' and self._payload:
            raise RuntimeError('Cannot append item into password protected archive.')

        self._side_files = []

    def _extract_payload(self, destination_dir):
        return _run_7z(
            command='e',
            switches=[
                '-y',
                '-r',
                '-p%s' % self.pwd,
                '-o%s' % destination_dir,
            ],
            args=[self.filename, self._payload_name]
        )

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
