"""Purely Python and stdlib password protected zip reader,
compatible with pwdzip module."""

import StringIO
import inspect
import os
import shutil
import tempfile
import uuid
import zipfile


class ZipFileReader(zipfile.ZipFile):
    SUPPORTED_MODES = ('r',)

    def __init__(self, filename, mode='r', compression=zipfile.ZIP_STORED, allowZip64=False, pwd=None):
        if mode not in self.SUPPORTED_MODES:
            raise ValueError('Unsupported mode %s. Supported modes are %s.' % (mode, ', '.join(self.SUPPORTED_MODES)))

        super(ZipFileReader, self).__init__(filename, mode, compression, allowZip64)
        self.setpassword(pwd)

        self._payload_name = self._find_payload()
        self._payload_archive = None

    @property
    def _payload(self):
        if not self._payload_archive and self._payload_name:
            self._payload_archive = self._load_payload()
        return self._payload_archive

    def _find_payload(self):
        if self.mode != 'r':
            return None

        zip_files = [f for f in self.namelist() if os.path.splitext(f)[1] == '.zip']
        if len(zip_files) != 1:
            return None

        payload_candidate = zip_files[0]
        payload_info = self.getinfo(payload_candidate)
        is_encrypted = payload_info.flag_bits & 0x1
        if not is_encrypted:
            return None

        return payload_candidate

    def _extract_payload(self, destination_dir):
        return self.extractall(destination_dir)

    def _load_payload(self):
        if not self._payload_name:
            return

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

        return zipfile.ZipFile(payload_buffer)

    def side_name_list(self):
        name_list = self.namelist()
        try:
            name_list.remove(self._payload_name)
        except ValueError:
            pass
        return name_list

    def read_side(self, name):
        return self.read(name)

    def extract_side(self, name, path):
        return self.extract(name, path)

    ###############################################################################
    # redirect methods into internal archive
    #

    # noinspection PyMethodParameters
    def get_dispatcher(func_name):
        """
        Args:
            func_name (str):
        """
        def dispatcher(self, *args, **kwargs):
            outer_self = inspect.stack()[1][0].f_locals.get('self')
            if outer_self and isinstance(outer_self, ZipFileReader):
                return getattr(super(ZipFileReader, self), func_name)(*args, **kwargs)

            if self._payload:
                return getattr(self._payload, func_name)(*args, **kwargs)

            return getattr(super(ZipFileReader, self), func_name)(*args, **kwargs)

        return dispatcher

    for name in ('namelist', 'printdir', 'testzip', 'infolist', 'getinfo',
                 'read', 'extract', 'extractall'):
        # noinspection PyArgumentList
        locals()[name] = get_dispatcher(name)
    del locals()['get_dispatcher']
