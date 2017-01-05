# coding: utf-8

import os
import time
from stat import S_ISDIR, S_ISREG

from web.helper import init_logger, timeformat
import pyftp

try:
    # pysftp is an optional module due to the ftp type is using.
    # if using sftp, the pysftp module is needed.
    import pysftp
except Exception as e:
    pysftp = None
    pass


class FtpClient:
    '''ftp client wrapper'''
    PORT_MAP = {'ftp': 21, 'sftp': 22}

    @classmethod
    def protocol(clz, host, port=None):
        _port, _prot, _addr = 21, 'ftp', 'host'
        npos = host.find('://')
        if npos != -1:
            _prot = host[:npos]
            _addr = host[npos + 3:]
            _port = clz.PORT_MAP.get(_prot.lower(), 21) if not port else port
        return _port, _prot, _addr

    def __init__(self, ftpinfo=None):
        self._sync = False
        self._host = ftpinfo.get('server')
        self._port = ftpinfo.get('port')
        self._user = ftpinfo.get('username')
        self._pswd = ftpinfo.get('password')
        self._root = ftpinfo.get('rootpath', '/')
        self._ftpc = None
        self._lpath = ftpinfo.get('localpath', os.environ['temp'])
        self._port, self._prot, self._host = self.protocol(self._host, self._port)
        self.log = init_logger()

    @property
    def host(self):
        return '{0}://{1}:{2}'.format(self._prot, self._host, self._port)

    @property
    def issftp(self):
        '''is using sftp or ftp protocol'''
        return self._prot == 'sftp'

    def connect(self):
        if not self._host:
            raise ValueError('ftp host is empty.')
        if not self._user or not self._pswd:
            raise ValueError('username or password is empty')

        try:
            if self._prot == 'sftp':
                if pysftp is None:
                    raise RuntimeError('pysftp module is not installed yet.')
                cnopts = pysftp.CnOpts()
                cnopts.hostkeys = None
                self._ftpc = pysftp.Connection(self._host, username=self._user, password=self._pswd, port=self._port, cnopts=cnopts)
            else:
                self._ftpc = pyftp.PyFTP(self._host, username=self._user, password=self._pswd, port=self._port)
                self._ftpc.connect()

        except Exception as e:
            errMsg = 'failed to connect %s://%s:%s' % (self._prot, self._host, self._port)
            self.log.error(errMsg)
            raise Exception(errMsg)
    
    def close(self):
        try:
            if self._ftpc:
                self._ftpc.close()
                self._ftpc = None
        except Exception as e:
            self.log.warn('failed to close ftp connection : %s', e)

    def download_d(self):
        '''Download ftp files to local path'''
        if self._ftpc is None:
            raise ValueError('FTP %s is not connected yet.' % self._host)

        self._ftpc.get_r(self._root, localdir=self._lpath, preserve_mtime=True)
        self._sync = True
        
    def download(self, remotepath, localpath=None):
        '''download single file from ftp server
        :param str remotepath:
            relative path on ftp server
        :param str|None localpath:
            local file full path, if None, will generate one
        :return str
            return the downloaded file local full path
        '''
        if self._ftpc is None:
            raise ValueError('FTP %s is not connected yet.' % self._host)
        
        if remotepath[0] in ('\\', '/'):
            remotepath = remotepath[1:]
            remotepath = os.path.join(self._root, remotepath).replace('\\', '/')
        
        if not localpath:
            localpath = os.path.join(os.environ['TEMP'], os.path.basename(remotepath))
        
        try:
            if os.path.exists(localpath):
                os.remove(localpath)
            self._ftpc.get(remotepath, localpath)
        except Exception:
            pass
        
        if os.path.exists(localpath):
            return localpath
        else:
            return None


    def upload_file(self, filepath, subpath=None):
        ''' Upload file to ftp server

        :param str filepath: 
            local file path
        :param str | None subpath:
            path on ftp server default to root path
        '''
        if self._ftpc is None:
            raise ValueError('FTP %s is not connected yet.' % self._host)
        
        if not filepath or not os.path.exists(filepath):
            raise ValueError('Upload file path is not valid')

        if not subpath:
            subpath = self._root
        else:
            if subpath[0] in ('\\', '/'):
                subpath = subpath[1:]
            subpath = os.path.join(self._root, subpath)
            subpath = subpath.replace('\\', '/')
        
        dirname = os.path.dirname(subpath)
        if not self._ftpc.exists(dirname):
            self.log.info('make dirs : %s', dirname)
            self._ftpc.makedirs(dirname)
        self._ftpc.put(filepath, remotepath=subpath, preserve_mtime=True)


    def upload_dir(self, dirpath, subpath=None, recursive=False):
        ''' Upload directory to ftp server

        :param str dirpath: 
            local directory path
        :param str | None subpath:
            path on ftp server default to root path
        :param bool recursive:
            upload directory recursively
        '''
        if self._ftpc is None:
            raise ValueError('FTP %s is not connected yet.' % self._host)
        if not dirpath or not os.path.exists(dirpath):
            raise ValueError('Upload file path is not valid')

        if not subpath:
            subpath = self._root
        else:
            if subpath[0] in ('\\', '/'):
                subpath = subpath[1:]
            subpath = os.path.join(self._root, subpath).replace('\\', '/')

        if recursive:
            if not self._ftpc.exists(subpath):
                self._ftpc.makedirs(subpath)
            self._ftpc.put_r(dirpath, remotepath=subpath, preserve_mtime=True)
        else:
            self._ftpc.put_d(dirpath, remotepath=subpath, preserve_mtime=True)


    def listdir(self, subpath=None):
        ''' Retrieve the file list of input path on ftp server

        :param str|None subpath:
            path on ftp server default to root path 
        '''

        if self._ftpc is None:
            raise ValueError('FTP %s is not connected yet.' % self._host)

        if not subpath:
            curpath = self._root
        else:
            if subpath[0] in ('\\', '/'):
                subpath = subpath[1:]
            curpath = os.path.join(self._root, subpath).replace('\\', '/')

        files, dirs = [], []
        for entry in self._ftpc.listdir(curpath):
            if self.issftp:
                fpath = os.path.join(curpath, entry).replace('\\', '/')
                stats = self._ftpc.stat(fpath)
                name = entry
            else:
                fpath = entry.st_path
                stats = entry
                name = entry.st_name

            isfile = S_ISREG(stats.st_mode)
            if isfile and os.path.splitext(name)[1] in ('.sig', '.log'):
                continue

            item = { 
                'name': name, 
                'size': stats.st_size if isfile else 0,
                'folder' : not isfile,
                'modified' : timeformat(stats.st_mtime),
                'fullpath' : fpath, # ftp full path 
                'relative' : os.path.join(subpath, name).replace('\\', '/') if subpath else name
            }
            if isfile:
                files.append(item)
            else:
                dirs.append(item)

        # dir first, file next
        dirs.extend(files)
        return dirs


def _UT():
    
    ftp = FtpClient('10.57.19.43', username='admin', password='admin')
    ftp.connect()

    for v in ftp.listdir('/uploadtest'):
        print v

    ftp.upload_dir(r'H:\ARCserve\RedirectFiles', ftppath='/doc', recursive=True)
    for v in ftp.listdir('doc/arcserveudp'):
        print v

    ftp.close()
    

if __name__ == '__main__':
    _UT()