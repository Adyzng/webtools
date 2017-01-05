# coding: utf-8

# using new type class
__metaclass__ = type

'''
Help functions for amptor web app
'''

import os
import sys
import time
import json

import logging
from logging import Logger
from logging.handlers import RotatingFileHandler


# export table
__all__ = ['init_logger', 'ErrorCode', 'ReplyJson', 'utf8_unicode', 'Singleton']


#########################################################################################################
# global logger instance
def init_logger(app=None, logname=None, pkgname='webapm'):
	'''init logger object from Flask.logger
	:param Flask app:
		Flask application instance
	:param str | None logname:
		logger object name, default `webapm`
	:param str : None pkgename:
		package name, default `webapm`
	:return
		log object
	'''
	logger_name = logname if logname else 'webapm'
	if logger_name not in Logger.manager.loggerDict:
		from flask import Flask
		if isinstance(app, Flask):
			app.logger_name = logger_name
			logger = app.logger
			log_path = app.root_path
		else:
			logger = logging.getLogger('logger_name')
			log_path = os.getcwd()
		# debug for all
		logger.setLevel(logging.DEBUG)

		# create logs folder
		logs_folder = os.path.join(log_path, 'logs')
		if not os.path.exists(logs_folder):
			os.mkdir(logs_folder)

		# logs format
		datefmt = "%Y-%m-%d %H:%M:%S"
		msgsfmt = '[%(asctime)s - %(process)4d - %(levelname)-7s]: %(message)s [%(name)s:%(filename)s:%(lineno)d]'
		formatter = logging.Formatter(msgsfmt, datefmt)

		# create info logger and set level to info, file: 32MB and 10s retension
		hinfo = RotatingFileHandler(filename=os.path.join(logs_folder, pkgname + '.log'), maxBytes=(1 << 25), backupCount=10)
		hinfo.setFormatter(formatter)
		hinfo.setLevel(logging.INFO)
		logger.addHandler(hinfo)

		# create error logger
		herror = RotatingFileHandler(filename=os.path.join(logs_folder, pkgname + '.err'), maxBytes=(1 << 25), backupCount=10)
		herror.setFormatter(formatter)
		herror.setLevel(logging.ERROR)
		logger.addHandler(herror)

	logger = logging.getLogger(logger_name)
	return logger


# file time format
def timeformat(time_second):
	'''format time string from file stats
	:param int time_second:
		file/folder modified time
	'''
	return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_second))


# uft8 convert to unicode
utf8_unicode = lambda s: s.decode('utf-8', 'replace') if isinstance(s, str) else s

# unicode to uft8
unicode_utf8 = lambda s: s.encode('utf-8', 'replace') if isinstance(s, unicode) else s


#########################################################################################################
#  error code

class ErrorCode :
	# error code
	ERR_SUCCESS         = 0
	ERR_PID_NOT_VALID   = 1
	ERR_BID_NOT_VALID   = 2
	ERR_DENIED_FILE     = 3
	ERR_NO_SUCH_FILE    = 4
	ERR_PATCH_CREATE    = 5
	ERR_PATCH_BUILD     = 6
	ERR_INVALID_FILE	= 7
	ERR_DELETE_FILE		= 8
	ERR_TIME_FORMAT		= 9
	ERR_ENCRYPT_MSG		= 10
	ERR_DECRYPT_MSG		= 11
	ERR_UN_CODEPATH		= 12
	ERR_UN_SUPPORT		= 13
	ERR_SERVER_EXP		= 14
	ERR_IN_PROGRESS     = 15
	ERR_INVALID_PARAM	= 16

	# error message
	_ERR_STATUS_MSG = {
		ERR_SUCCESS         : 'success',
		ERR_PID_NOT_VALID   : 'pid not valid',
		ERR_BID_NOT_VALID   : 'branch not valid',
		ERR_DENIED_FILE     : 'denied file',
		ERR_NO_SUCH_FILE    : 'no such file',
		ERR_PATCH_CREATE    : 'patch create failed',
		ERR_PATCH_BUILD     : 'patch build failed',
		ERR_INVALID_FILE	: 'invalid file',
		ERR_DELETE_FILE		: 'failed to delete file',
		ERR_TIME_FORMAT		: 'time format in unknown',
		ERR_ENCRYPT_MSG		: 'encrypt message failed',
		ERR_DECRYPT_MSG		: 'decrypt message failed',
		ERR_UN_CODEPATH		: 'unknown code path',
		ERR_UN_SUPPORT		: 'not support operation',
		ERR_SERVER_EXP		: 'server exception',
		ERR_IN_PROGRESS     : 'operation in progress',
		ERR_INVALID_PARAM	: 'invalid input parameter',
	}

	@classmethod
	def message(clz, err):
		'''error code to error message'''
		return clz._ERR_STATUS_MSG.get(err, 'unknown error')


def ReplyJson(err, msg=None, **kwargs):
	''''format response json data'''
	reply = dict(status = err, message = msg if msg else ErrorCode.message(err) )
	for k, v in kwargs.iteritems():
		reply[k] = v
	return reply


##########################################################################################
#  Singleton 

class SingletonDecorator:
	'''class decorator, making other class to Singleton'''
	def __init__(self, cls):
		self._cls = cls

	def __call__(self):
		'''make the instance of'''
		raise TypeError('Singletons must be accessed through "Instance()".')

	def __instancecheck__(self, inst):
		'''make isinstance() works'''
		return isinstance(inst, self._cls)

	def instance(self):
		try:
			return self._instance
		except:
			self._instance = self._cls()
			return self._instance


class Singleton(object):
	'''
	class level single instance
	'''
	def __init__(self, *args, **kwargs):
		pass
		
	def __new__(cls, *args, **kwargs):
		'''
		customize new operator for this class, when trying to new an object of this class,
		it always return the single instance
		'''
		if not hasattr(cls, '_instance'):
			cls._instance = super(Singleton, cls).__new__(cls, args, kwargs)
		return cls._instance



# print'\n'.join([''.join([('Love'[(x-y)%4]if((x*0.05)**2+(y*0.1)**2-1)**3-(x*0.05)**2*(y*0.1)**3<=0 else' ')for x in range(-30,30)])for y in range(15,-15,-1)])
# print'\n'.join([''.join(['*'if abs((lambda a:lambda z,c,n:a(a,z,c,n))(lambda s,z,c,n:z if n==0 else s(s,z*z+c,c,n-1))(0,0.02*x+0.05j*y,40))<2 else ' ' for x in range(-80,20)])for y in range(-20,20)])