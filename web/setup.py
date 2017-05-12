# coding: utf-8
"""
restful api for setup
"""

import os
import json
from flask import Flask, Blueprint, request, jsonify

from web.settings import HARVEST, FTPLIST, REDIRECT, ENVIRONS, ConfigLoader
from web.helper import init_logger, ReplyJson, ErrorCode
from web.restful.harvest import Harvest


class WebSetup(object):
    # Blueprint instance
    api = Blueprint('SETUP', __name__)
    log = init_logger()

    # register in Flask application
    @staticmethod
    def register(app):
        if not isinstance(app, Flask):
            raise TypeError('app should be an instance of `flask.Flask`')
        else:
            app.register_blueprint(WebSetup.api, url_prefix='/setup')
        

    # harvert setup
    @staticmethod
    @api.route('/harvest', methods=['POST'])
    def harvest():
        '''setup harvest config
            <>/setup/harvest
        :request:
            { username: user, password: pswd, homepath: path }
        :response:
            { status: 0, message: '' }
        '''
        user = request.values.get('username')
        pswd = request.values.get('password')
        path = request.values.get('homepath') or os.environ.get('CA_SCM_HOME', "")
        
        status = ErrorCode.ERR_SUCCESS
        errmsg = ''

        while True:
            if not (user and pswd):
                WebSetup.log.warn('WebSetup.harvest: invaild parameter {user: %s, pswd: %d, path: %s}', user, len(pswd), path)
                status = ErrorCode.ERR_INVALID_PARAM
                break
            
            try:
                Harvest.generate_userfile(path, user, pswd)
                HARVEST['home'] = path
                HARVEST['username'] = user
            except Exception as e:
                status = ErrorCode.ERR_SERVER_EXP
                errmsg = 'WebSetup.harvest exception : {0}'.format(e)
                WebSetup.log.error(errmsg)
                WebSetup.log.exception('Exception')

            break	# while loop
        
        return jsonify(ReplyJson(status, errmsg))

    
    @staticmethod
    @api.route('/ftp', methods=['POST'])
    def ftp():
        '''setup config ftp server information
        
        :request:
            {ftps: [ {name : name, host: host, username: user, password: pswd, rootpaths: subp}, {} ]}
        :response:
            {status: 0, message: ''}
        '''
        ncount = 0
        value = request.values.get('ftplist', '[]')
        ftplist = json.loads(value)
        
        for ftp in ftplist:
            name = ftp.get('name')
            host = ftp.get('host')
            user = ftp.get('username')
            pswd = ftp.get('password')
            paths = ftp.get('rootpaths', '')
            if not (host and user and pswd):
                WebSetup.log.warn('ftp {0} is not valid'.format(name))
                continue
            if not FTPLIST.get(name):
                FTPLIST[name] = {}
            FTPLIST[name]['server'] = host
            FTPLIST[name]['username'] = user
            FTPLIST[name]['password'] = pswd

            idx = 0
            for path in paths.split('\n'):
                if not path:
                    continue
                if idx == 0:
                    FTPLIST[name]['rootpath'] = path
                else:
                    FTPLIST[name]['rootpath{0}'.format(idx)] = path
                idx += 1

            ncount += 1
            WebSetup.log.info('ftp {0}: {1}'.format(name, host))
        
        if ncount:
            status = ErrorCode.ERR_SUCCESS
        else:
            status = ErrorCode.ERR_INVALID_PARAM
        
        return jsonify(ReplyJson(status))


    @staticmethod
    @api.route('/redirect', methods=['POST'])
    def redirect():
        '''setup config redirect files information
        
        :request:
            {config: config, lpath: lpath, ftp: ftpsvr}
        :response:
            {status: 0, message: '' }
        '''
        config = request.values.get('config')
        locpath = request.values.get('lpath')
        ftphost = request.values.get('ftp')
        status = ErrorCode.ERR_SUCCESS

        while True:
            if not (config and locpath and ftphost):
                status = ErrorCode.ERR_INVALID_PARAM
                break
            
            REDIRECT['path'] = locpath
            REDIRECT['config'] = config

            if not os.path.exists(locpath):
                os.makedirs(locpath)

            valid = False
            for ftp in FTPLIST.itervalues():
                if ftp['server'] == ftphost:
                    valid = True
                    REDIRECT['ftp'] = ftp

            if not valid:
                WebSetup.log.warn('No valid ftp server {%s} found', ftphost)
                status = ErrorCode.ERR_INVALID_PARAM

            break  # while loop
        
        return jsonify(ReplyJson(status))
    
    @staticmethod
    @api.route('/environ', methods=['POST'])
    def environ():
        '''basic environ configure
        :request:
            {udpbin: udphome}
        :response:
            {status: 0, message: '' }
        '''
        udpbin = request.values.get('udpbin')
        status = ErrorCode.ERR_SUCCESS
        errmsg = ''

        while True:
            if not (udpbin and os.path.exists(udpbin)):
                status = ErrorCode.ERR_INVALID_PARAM
                errmsg = '{0} is not exist.'.format(udpbin)
                break
                
            try:
                ENVIRONS['udpbin'] = udpbin
                ConfigLoader.save()
            except Exception as e:
                errmsg = 'save config exception: {0}'.format(e)
                status = ErrorCode.ERR_SERVER_EXP
                WebSetup.log.error(errmsg)
                WebSetup.log.exception('Exception')

            break # while loop

        return jsonify(ReplyJson(status, msg=errmsg))
