#!c:/windows/system32/cmd.exe Python
# coding: utf-8

# using new type class
__metaclass__ = type

import os

from flask_restful import Api
from flask import Flask, render_template ##, url_for , make_response, g, request , session

from web.settings import ENVIRONS, HARVEST, FTPLIST, REDIRECT
from web.model import ModelDB, BranchModel

############################################################################################
# wrapper of Flask app

class WebApp(object):
    # the only instance of Flask  
    _PKG_NAME_ = 'web'
    app = Flask(_PKG_NAME_) 

    def __init__(self, name=None, config=None):
        '''initialize web application'''
        # load default config and override config from an environment variable
        from settings import BaseConfig
        if config is not None: 
            BaseConfig.__dict__.update(dict(config))
        
        self.app.config.from_object(BaseConfig)
        # support for unicode 
        self.app.config['JSON_AS_ASCII'] = False
        #self.app.config['JSON_SORT_KEYS'] = False
        
        # Init logger instance
        from helper import init_logger
        self.log = init_logger(self.app)
        self.log.info('web root : %s', self.app.root_path)
        
        # register toolkit restful api
        self.api = Api(self.app)
        from restful import TimeConvert, MessageEncoder, SyncHarvest, SyncFtp
        for clz in (TimeConvert, MessageEncoder, SyncHarvest, SyncFtp):
            clz.register(self.api)

        # Blueprint RESTful API for patch maker
        from patcher import PatchMaker
        PatchMaker.register(self.app)
        
        # Register RESTful API for setup config 
        from setup import WebSetup
        WebSetup.register(self.app)

        try:
            # Initial database
            dbpath = self.app.config.get('DB_PATH', self.app.root_path)
            ModelDB().init_db(db_path=dbpath)
        except Exception as e:
            self.log.warn('initialize db exception : %s', e)
            self.log.exception('Exception')
        
    def run(self, port=5000):
        # setup page
        self.log.info('Flask web application start...')
        self.app.run(threaded=True, port=port)
        self.log.info('Flask web application stopped.')

    @staticmethod
    def pathlist(ftp):
        idx = 1 # start from idx 1
        paths = [ftp['rootpath'],]
        while True:
            rpn = ftp.get('rootpath{0}'.format(idx), None)
            if rpn:
                paths.append(rpn)
                idx += 1
            else:
                break
        return paths

    @staticmethod
    @app.cli.command('initdb')
    def initdb_command():
        '''Initializes the database.'''
        ModelDB().init_db()
        print 'Initialized the database.'
    
    @staticmethod
    @app.route('/')
    @app.route('/redirect')
    def ftpup():
        return render_template('ftpup.html', page='ftpup', rootpaths=WebApp.pathlist(REDIRECT['ftp']))

    @staticmethod
    @app.route('/timeconvert')
    def timec():
        return render_template('timec.html', page='timec')

    @staticmethod
    @app.route('/encode')
    def encoding():
        return render_template('encode.html', page='encoding')

    @staticmethod
    @app.route('/unicode')
    def unescape():
        return render_template('unicode.html', page='unescape')

    @staticmethod
    @app.route('/patch')
    def patch():
        return render_template('patch.html', page='patch', branchList=BranchModel.get_branchs())

    @staticmethod
    @app.route('/setup')
    def setup():
        rdtftp = dict()
        for key,val in FTPLIST.iteritems():
            if REDIRECT['ftp'] == val:
                rdtftp.update(val, name=key, paths='\n'.join(WebApp.pathlist(REDIRECT['ftp'])))
                break
        
        environ = {
            'harvest' : HARVEST,
            'environ' : ENVIRONS,
            'redirect' : REDIRECT,
            'ftp' : rdtftp
        }
        return render_template('setup.html', env=environ)

############################################################################################
#  app run

def create_app(**kwargs):
    '''product mode'''
    kwargs.update(DEBUG=False)
    application = WebApp(config=kwargs)
    return application.app

def develop(**kwargs):
    '''develop mode'''
    kwargs.update(DEBUG=True)
    port = kwargs.get('port') or 5000
    WebApp(config=kwargs).run(port = port)
    
def deploy():
    '''run deploy operations'''
    pass


if __name__ == '__main__':
    develop()