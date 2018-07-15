"""Purely Python and stdlib password protected zip reader,
compatible with pwdzip module."""

import StringIO
import os
import shutil
import tempfile
import uuid
import zipfile


class ZipFileReader(zipfile.ZipFile):
    SUPPORTED_MODES = ('r',)

    def __init__(self, filename, mode='r', compression=zipfile.ZIP_STORED, allowZip64=False, pwd=None):
        if mode not in self.SUPPORTED_MODES:
            raise ValueError('Unsupported mode %s. Allowed modes are %s.' % (mode, ', '.join(self.SUPPORTED_MODES)))

        super(ZipFileReader, self).__init__(filename, mode, compression, allowZip64)
        self.setpassword(pwd)

        self._payload_name = None
        self._payload = None
        self._get_payload()

    def _extract_payload(self, destination_dir):
        return self.extractall(destination_dir)

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

        self._extract_payload(temp_dir)

        temp_zip_file_path = os.path.join(temp_dir, self._payload_name)
        payload_buffer = StringIO.StringIO()
        with open(temp_zip_file_path, 'rb') as f:
            payload_buffer.write(f.read())

        try:
            shutil.rmtree(temp_dir)
        except OSError:
            shutil.rmtree(temp_dir)

        self._payload = zipfile.ZipFile(payload_buffer)

    ###############################################################################
    # redirect methods into internal archive
    #
    def _call_orig(self, func, *args, **kwargs):
        func_name = func.__name__
        return getattr(super(ZipFileReader, self), func_name)(*args, **kwargs)

    def _call_payload(self, func, *args, **kwargs):
        func_name = func.__name__
        if self._payload:
            return getattr(self._payload, func_name)(*args, **kwargs)
        return getattr(super(ZipFileReader, self), func_name)(*args, **kwargs)

    def namelist(self):
        return self._call_payload(self.namelist)

    def printdir(self):
        return self._call_payload(self.printdir)

    def testzip(self):
        return self._call_payload(self.testzip)

    def infolist(self):
        return self._call_payload(self.infolist)

    def getinfo(self, name):
        return self._call_payload(self.getinfo, name)

    def read(self, name, pwd=None):
        return self._call_payload(self.read, name, pwd)

    def extract(self, member, path=None, pwd=None):
        return self._call_payload(self.extract, member, path, pwd)

    def extractall(self, path=None, members=None, pwd=None):
        return self._call_payload(self.extractall, path, members, pwd)
