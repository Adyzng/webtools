# coding: utf-8

'''
#   This module used to sync file from havest.
#   CA Harvest Software must be installed first.
#   
#   Harvest Logon Account:
#      Using $CA_SCM_HOME\svrenv.exe to generate encypted user credential 
#      file `hsvr.dfo` by default under install path.
# 
'''

import os
import subprocess
import ConfigParser


from web.helper import init_logger, timeformat
log = init_logger()


class Harvest:
    '''Operation harvest and local'''

    def __init__(self, iniconfig, userfile=None):
        '''
        :param str iniconfig:
            harvest checkout config
        :param str userfile:
            harvest user credential encrypt file
            default to <CA_SCM_HOME>\hsvr.dfo
        '''
        self._userfile = userfile
        self._iniconfig = iniconfig

        # harvest checkout config file, check exist or not
        if self._iniconfig is None or not os.path.exists(self._iniconfig):
            log.error('Havest checkout config file %s not exist.', self._iniconfig)
            raise ValueError('Havest checkout config file %s not exist.' % self._iniconfig)

        # read config file
        self._option = self.read_ini(self._iniconfig)
        self._localpath = self._option.get('clientpath', None)
    
    @property
    def localpath(self):
        return self._localpath
    

    def read_ini(self, filename):
        '''Read configure information from ini file, return dict
        
        :param str filename:
            ini config file
        :return
            config options dict
        '''
        option = {}
        try:
            ini = ConfigParser.ConfigParser()
            ini.read(filename)

            if ini.has_section('Harvest'):
                option['harvest'] = ini.get('Harvest', 'InstallPath')

            if ini.has_section('CheckOut'):
                option.update(ini.items('CheckOut'))

            if ini.has_section('CodePath'):
                option['codepath'] = '|'.join([v[1] for v in ini.items('CodePath')])

        except Exception as e:
            log.error('read_ini() exception: %s', e)
            
        return option
    
    @staticmethod
    def generate_userfile(path, username, password):
        ''' The encrypted credentials will been saved in a hidden file named: hsvr.dfo within CA_SCM_HOME; 
        which is then utilized by the CA Harvest SCM Server processes when connecting to the Database Server.'''

        try:
            scm_home = path or os.environ.get('CA_SCM_HOME', '')
            if not scm_home or not os.path.exists(scm_home):
                log.error('Harvest is not installed on current machine!')
                raise EnvironmentError('Harvest is not installed on current machine!')

            cmd_line = 'svrenc.exe -usr {0} -pw {1} -s'.format(username, password)
            log.info('Generate harvest user file: %d', len(cmd_line))

            output = subprocess.check_output(
                cmd_line,
                shell=True,
                stderr=subprocess.STDOUT
            )
        except Exception as e:
            log.error('Generate harvest user file exception: %s', e)
            raise


    def checkout(self):
        ''' checkout code file from harvest '''
        try:
            # harvest must be installed on current machine
            scm_home = os.environ.get('CA_SCM_HOME', '')
            if not scm_home or not os.path.exists(scm_home):
                log.error('Harvest is not installed on current machine!')
                raise EnvironmentError('Harvest is not installed on current machine!')

            # user credential encrypted info
            # using svrenc.exe to generate the credential encrypted file under CA_SCM_HOME 
            self._userfile = os.path.join(scm_home, 'hsvr.dfo') if not self._userfile else self._userfile

            # construct log file
            logs_file = os.path.splitext(self._iniconfig)[0] + '.log'
            if os.path.exists(logs_file):
                os.remove(logs_file)
            
            # hco -b cscr501 -en ARCserve -st Development -sy -pn "Check Out for Browse" -vp \ARCserve\D2D\Native\H -s * -cp h:\arcserve\native\h\ -eh user.dfo
            for cp in self._option['codepath'].split('|'):
                subpath, patten, recursive = cp.split(',')
                cmd_line = 'hco.exe -sy -replace all -eh \"%s\" -b %s -en %s -st %s -vp \"%s\" -cp \"%s\" -s %s -oa \"%s\" ' % (
                    self._userfile, 
                    self._option['broker'],
                    self._option['project'],
                    self._option['state'],
                    os.path.join(self._option['viewpath'], subpath),
                    os.path.join(self._option['clientpath'], subpath),
                    patten,
                    logs_file
                )

                log.info('Harvest checkout: %s', cmd_line)
                output = subprocess.call(
                    cmd_line,
                    shell=True,
                    stderr=subprocess.STDOUT
                )

                for root, dirs, files in os.walk(os.path.join(self._option['clientpath'], subpath)):
                    for f in files:
                        fp = os.path.join(root, f)
                        if os.path.splitext(f)[1] in ('.sig', '.log'):
                            try:
                                os.remove(fp)
                            except Exception as e:
                                log.warn('failed to delete file : ', fp)

        except Exception as e:
            log.error('Harvest checkout exception: %s', e)
            raise
    
    def _wrap_item(self, entry, rootpath, isfile=False, subpath=None, scmpath=None):
        '''wrap file or folder to json object'''
        fpath = os.path.join(rootpath, entry)
        stats = os.stat(fpath)

        item = { 
            'name': entry, 
            'size': stats.st_size if isfile else 0,
            'folder' : not isfile,
            'modified' : timeformat(stats.st_mtime),
            'fullpath' : os.path.join(scmpath, entry).replace('\\', '/') if scmpath else entry,    # Harvest full path
            'relative' : os.path.join(subpath, entry).replace('\\', '/') if subpath else entry
        }
        return item
    
    def listdir(self, subpath=None, recursive=False):
        '''Retrieve file list of current code path that has been checkout to local path

        :param str subpath:
            harvest project relative path
        '''
        if not subpath:
            subpath = ''
            dirpath = self._localpath
            scmpath = self._option.get('viewpath', '/')
        else:
            if subpath[0] in ('\\', '/'):
				subpath = subpath[1:]
            dirpath = os.path.normpath(os.path.join(self._localpath, subpath))
            scmpath = os.path.join(self._option['viewpath'], subpath)
        
        if not os.path.exists(dirpath):
            log.warn('listdir(): given path %s not exist.', dirpath)
            return []
        
        dirs, files = [], []
        for entry in os.listdir(dirpath):
            fpath = os.path.join(dirpath, entry)
            stats = os.stat(fpath)

            isfile = os.path.isfile(fpath)
            if isfile and os.path.splitext(entry)[1] in ('.sig', '.log'):
                continue
            
            item = { 
                'name': entry, 
                'size': stats.st_size if isfile else 0,
                'folder' : not isfile,
                'modified' : timeformat(stats.st_mtime),
                'fullpath' : os.path.join(scmpath, entry).replace('\\', '/'),  # Harvest full path
                'relative' : os.path.join(subpath, entry).replace('\\', '/'),  # Relative path
            }

            if isfile:
                files.append(item)
            else:
                dirs.append(item)
            
        # dir first, file second
        dirs.extend(files)
        return dirs
        

def _UT(configfile=None):
    '''unit test'''
    if configfile is None:
        configfile = os.path.abspath('native-sync.ini')
    elif os.path.isabs(configfile):
        configfile = os.path.abspath(configfile)
    
    print 'Harvest checkout config file: %s' % configfile
    harvest_checkout(configfile)


if __name__ == '__main__':
    '''
    Usage: 
      python harvest_checkout.py [config]
	Example:
      python harvest_checkout.py
      python harvest_checkout.py native-sync.ini	  
    '''
    _UT(None if len(sys.argv) == 1 else sys.argv[1])