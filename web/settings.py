# coding: utf-8

#
# Flask application config
#
class BaseConfig:
    SECRET_KEY	= '\xaeT\xdc\xcd\xb2\xd5J\x06\xf4U\xf4\x998\xea\xde\xb8\xbe\xa3!\x84d\x18\x0e/'
    APP_NAME	= 'apmtor'
    DATABASE 	= 'db/apmtor.db'
    USERNAME	= 'admin'
    PASSWORD	= 'admin'


#
# other environment config
#
ENVIRONS = {
    'udpbin' : "",
    'webstore' : "..\\store",
}

#
# harvest code path info
#
CODEPATH = {
    'i18n' : {},
    'redirect' : {},
}

# abbreviation 
I18N = CODEPATH['i18n']
REDIRECT = CODEPATH['redirect']

#
# basic Harvest info
#
HARVEST = {
    "home" : "",
    "username": "",
    "userfile": ""
}

#
# ftp server lists
#
FTPLIST = {
    "test1": {
        "username": "admin", 
        "password": "admin", 
        "rootpath": "/uploadtest", 
        "server": "ftp://10.57.19.43", 
        "localpath": ""
    }
}


class ConfigLoader(object) :
    '''config file loader and saver'''
    CONFIG_FILE = "webapp.json"
    DEFAULT_CFG_FILE = "webapp.default.json"

    @classmethod
    def load(clz):
        '''load config from configure file'''
        try:
            import os
            import json
            
            opath = os.getcwd()
            os.chdir(os.path.dirname(os.path.abspath(__file__)))

            config_file = clz.CONFIG_FILE
            if not os.path.exists(clz.CONFIG_FILE):
                if not os.path.exists(clz.DEFAULT_CFG_FILE):
                    raise RuntimeError('Default configure file {0} is missing.'.format(clz.DEFAULT_CFG_FILE))
                else:
                    config_file = clz.DEFAULT_CFG_FILE

            with open(config_file, 'r') as fp:
                # json
                js = json.load(fp, encoding='utf-8')
                        
                # harvest checkout related config
                hav = js.get('harvest', None)
                if hav and HARVEST:
                    HARVEST["home"] = os.environ.get('CA_SCM_HOME', "") or hav.get('home', "")
                    HARVEST["username"] = hav.get('username', "")
                    HARVEST["userfile"] = hav.get('userfile', "")
                    
                # environ related config
                env = js.get('environ', None)
                if env and ENVIRONS:
                    ENVIRONS['udpbin'] = os.path.abspath(env.get('udpbin', ""))
                    ENVIRONS['webstore'] = os.path.abspath(env.get('store') or ENVIRONS['webstore'])
                if not ENVIRONS.get('udpbin'):
                    try:
                        import _winreg
                        hkey = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Arcserve\Unified Data Protection\Engine\InstallPath")
                        value, _type = _winreg.QueryValueEx(hkey, "Path")
                        _winreg.CloseKey(hkey)
                        ENVIRONS['udpbin'] = os.path.join(value, 'BIN')
                    except:
                        pass
                
                # ftp list
                ftps = js.get('ftplist', {})
                for name, ftp in ftps.iteritems():
                    FTPLIST[name] = ftp
                
                # redirect files config
                rdt = js.get('redirect', None)
                if rdt:
                    REDIRECT['config'] = os.path.abspath(rdt.get('config', ""))
                    REDIRECT['path'] = os.path.abspath(rdt.get('path', ""))
                    REDIRECT['ftp'] = FTPLIST.get(rdt.get('ftp'))

                # i18n config not using yet
                i18n = js.get('i18n', None)
                if i18n:
                    I18N['config'] = i18n.get('config', "")
                    I18N['path'] = i18n.get('path', "")
                    I18N['ftp'] = FTPLIST.get(i18n.get('ftp'))
                del js
        except Exception as e:
            print("failed to load webapp configuration: {0}".format(clz.CONFIG_FILE))
            raise
        finally:
            os.chdir(opath)

    @classmethod
    def save(clz):
        '''save customer configure information'''
        try:
            import os
            import json
    
            opath = os.getcwd()
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
            tmp_file = clz.CONFIG_FILE + '_tmp'

            with open(tmp_file, 'w+') as fp:
                rdt  = {'ftp' : '', 'path' : REDIRECT['path'], 'config' : REDIRECT['config']}
                i18n = {'ftp' : '', 'path' : I18N['path'], 'config' : I18N['config']}

                # update the redirect/i18n checkout config file
                for obj in [rdt]:
                    old = obj['config']
                    new = obj['config'] + '_tmp'
                    with open(old, 'r') as reader, open(new, 'w+') as writer:
                        for line in reader.xreadlines():
                            if line.find('ClientPath=') != -1:
                                writer.write('ClientPath={0}\n'.format(obj['path']))
                            else:
                                writer.write(line)
                    try:
                        os.remove(old)
                        os.rename(new, old)
                    except:
                        pass
                    
                
                # update ftp server name
                for name, ftp in FTPLIST.iteritems():
                    if ftp['server'] == REDIRECT['ftp']['server']:
                        rdt['ftp'] = name
                    if ftp['server'] == I18N['ftp']['server']:
                        i18n['ftp'] = name
                
                # whole config json object
                config = dict(
                    harvest = HARVEST,
                    environ = ENVIRONS,
                    ftplist = FTPLIST,
                    redirect = rdt,
                    i18n = i18n
                )
                
                # save to file
                json.dump(config, fp, indent=4, ensure_ascii=False)
            
            # rename file
            try:
                os.remove(clz.CONFIG_FILE)
                os.rename(tmp_file, clz.CONFIG_FILE)
            except:
                pass
        except Exception as e:
            print("failed to save webapp configuration: {0}".format(clz.CONFIG_FILE))
            raise
        finally:
            os.chdir(opath)

# auto load config
ConfigLoader.load()