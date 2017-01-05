# coding: utf-8

""""
sync ftp to local temp
"""

import os
import time

from threading import Lock
from ftpclient import FtpClient

#from flask import request
from flask_restful import Resource, Api, reqparse

from web.helper import ErrorCode, ReplyJson, init_logger, Singleton
from web.settings import CODEPATH

from contextlib import contextmanager

class FtpObject(object):
	# conntion timeout : 300s, after this time, connection closed
	_TIMEOUT = 300

	def __init__(self, label):
		self.label = label.lower()
		self.log = init_logger()
		self.lck = Lock()
		self.ftp = None
		self.ref = 0
		self.ts = 0
	
	@property
	def codepath(self):
		return self.label

	@contextmanager
	def connect(self):
		try:
			yield self._connect()
		finally:
			self._close()

	def _connect(self):
		''''actually connect to ftp server'''
		try:
			# wait to lock
			self.lck.acquire()
			ts = time.time() - self.ts

			# already timeout since last active connection
			if self.ftp and self.ref == 0 and ts > self._TIMEOUT:
				try:
					self.ftp.close()
					self.ftp = None
				except:
					self.ftp = None
					pass

			if not self.ftp:
				config = CODEPATH.get(self.label)
				if not config:
					err = '%s ftp configure is empty. It can not be connected.' % self.label
					self.log.error(err) 
					raise Exception(err)
				ftp = FtpClient(config['ftp'])
				ftp.connect()
				self.ref, self.ftp = 0, ftp
				self.log.info('connected to ftp: %s', self.ftp.host)
				
		except Exception as e:
			self.ftp = None
			raise
		finally:
			self.ref += 1
			self.ts = time.time()
			self.lck.release()
		return self.ftp


	def _close(self, force=False):
		''''close exist ftp connection'''
		try:
			self.lck.acquire()
			if self.ftp:
				# reduce the reference
				self.ref -= 1
				ts = time.time() - self.ts

				# no reference and timeout
				if self.ref == 0 and ts > self._TIMEOUT:
					try:
						self.ftp.close()
						self.ftp = None
					except:
						self.ftp = None
						pass
		finally:
			self.lck.release()


class ConnCache(object):
	'''ftp connection descriptor'''

	def __init__(self, label):
		'''only one instance for each ftp server'''
		self.label = label.lower()
		self.ftpobj = FtpObject(label)
	
	def __get__(self, instance, clz):
		return self.ftpobj

	def __set__(self, instance, value):
		'''do not set anything'''
		pass



class SyncFtp(Resource, Singleton):
	''''RESTful API wrapper for redirect/i18n ftp server upload/download '''

	# rediret ftp server
	redirect_ftp = ConnCache('redirect')

	def __init__(self):
		if not hasattr(self, '_init'):
			self._init = True
			self.log = init_logger()
			self.lck = Lock()
			self.args = reqparse.RequestParser()
			self.args.add_argument('type', default='', help='harvest operation type')
			self.args.add_argument('path', default=None, help='relative path on harvest code path')

	@classmethod
	def register(clz, api):
		if isinstance(api, Api):
			api.add_resource(clz, '/toolkit/ftp/<string:codepath>', endpoint='ftprid')
		else:
			raise TypeError('Unsupported parameter type: %s', type(api))
	
	def sync_ftp(self, codepath, ftpc, args):
		'''
		:param str codepath:
        	redirect: sync/upload [redirect] files between harvest and ftp
        	i18n: sync/upload [18n] files between harvest and ftp
		:param FtpClient ftpc:
			ftp client wrapper
		:request
			type: sync/upload/files, sync or upload or filelist
			path: relative path
		:responce
			files: [] array of file list
		'''
		_path = args['path']
		_type = args['type']

		if _path and _path[0] == '/':
			_path = _path[1:]

		files = []
		errMsg, status = None, ErrorCode.ERR_SUCCESS

		while True and ftpc:
			if _type not in ('sync', 'files', 'upload', 'download'):
				self.log.error('Invalid ftp operation: %s', _type)
				status = ErrorCode.ERR_UN_SUPPORT
				break
			
			try:
				if _type == 'upload':
					config = CODEPATH.get(codepath)
					lpath = os.path.join(config['path'], _path or '/')
					self.log.info('%s : ftp file upload to %s', codepath, _path or '/')

					if os.path.isfile(lpath):
						ftpc.upload_file(lpath, subpath=_path)
					elif os.path.isdir(lpath):
						ftpc.upload_dir(lpath, subpath=_path, recursive=True)
					else:
						status = ErrorCode.ERR_UN_CODEPATH
						errMsg = 'unknown local path : %s' % _path

				elif _type == 'download':
					self.log.info('download ftp file %s', _path)
					lfile = ftpc.download(_path)
					if lfile:
						filename = os.path.basename(lfile)
						return send_from_directory(os.path.dirname(lfile), filename=filename, as_attachment=True, attachment_filename=filename)
					else:
						status = ErrorCode.ERR_SERVER_EXP
						errMsg = 'Failed to download file {0} from ftp server.'.format(_path)
				
				else:
					self.log.info('%s : ftp file list of %s', codepath, _path or '/')
					files = ftpc.listdir(_path)

			except Exception as e:
				self.log.error('Exception : %s', e)
				status = ErrorCode.ERR_SERVER_EXP
				errMsg = e.message
			break # while
		
		return ReplyJson(status, msg=errMsg, files=files, count=len(files))

	@contextmanager
	def lock(self):
		try:
			acquired = False
			if self.lck:
				acquired = self.lck.acquire()
			yield
		finally:
			if acquired: 
				# release lock at last
				self.lck.release()


	def get(self, codepath):
		'''Sync / upload files between/to ftp server
			<>/toolkit/ftp/redirect?type=sync
			<>/toolkit/ftp/redirect?type=files&path=/
	   	'''
		# !!!! currently only support <Redirect> !!!!
		if codepath.lower() != 'redirect':
			return ReplyJson(ErrorCode.ERR_UN_CODEPATH)

		# create ftp connection with reference count
		with self.redirect_ftp.connect() as ftp:
			if not ftp:
				self.log.error('ftp connection failed')
				return ReplyJson(ErrorCode.ERR_SERVER_EXP)
			else:
				# synchronize all ftp operation
				with self.lock():
					return self.sync_ftp(codepath.lower(), ftp, self.args.parse_args())
		
	def post(self, codepath):
		'''same as GET'''
		return self.get(codepath)