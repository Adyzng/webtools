# coding: utf-8

""""
sync harvest to local temp
"""

import os
import ctypes

from threading import Lock
from harvest import Harvest

#from flask import request
from flask_restful import Resource, Api, reqparse

from web.helper import ErrorCode, ReplyJson, init_logger, Singleton
from web.settings import CODEPATH


class SyncHarvest(Resource, Singleton):
	'''Sync files from harvest
	:request
        type: sync/files, sync or file list
        path: relative path
    :responce
        files: [] array of file list
	'''
	# operation timeout : 30s
	_TIMEOUT = 30	

	def __init__(self):
		if not hasattr(self, type(self).__name__):
			setattr(self, type(self).__name__, True)
			self.log = init_logger()
			self.lock = Lock()
			self.args = reqparse.RequestParser()
			self.args.add_argument('type', default='', help='harvest operation type')
			self.args.add_argument('path', default=None, help='relative path on harvest code path')
	
	
	@classmethod
	def register(clz, api):
		if isinstance(api, Api):
			api.add_resource(clz, '/toolkit/harvest/<string:codepath>', endpoint='harvrid')
		else:
			raise TypeError('Unsupported parameter type: %s', type(api))
	
	def sync_harvest(self, codepath, args):
		'''Sync files from harvest, and return file list
			<>/toolkit/harvest/redirect?type=sync
			<>/toolkit/harvest/redirect?type=files&path=/
		'''
		_path = args['path']
		_type = args['type'].lower()

		if _path and _path[0] == '/':
			_path = _path[1:]

		files = []
		errMsg, status = None, ErrorCode.ERR_SUCCESS
		codepath = codepath.lower()

		while True:
			if _type not in ('sync', 'files', 'download'):
				self.log.error('Invalid harvest operation: %s', _type)
				status = ErrorCode.ERR_UN_SUPPORT
				break

			# !!!! currently only support <Redirect> !!!!
			if codepath != 'redirect':
				status = ErrorCode.ERR_UN_CODEPATH
				break

			config = CODEPATH.get(codepath, None)
			if not config:
				status = ErrorCode.ERR_UN_CODEPATH
				break

			try:
				harvest_obj = Harvest(config['config'])
				
				if _type == 'sync':
					harvest_obj.checkout()
					self.log.info('checkout completed.')
					files = harvest_obj.listdir()

				elif _type == 'download':
					lfile = os.path.join(harvest_obj.localpath, _path)
					if os.path.exists(lfile):
						self.log.warn('download file %s', lfile)
						filename = os.path.basename(lfile)
						return send_from_directory(os.path.dirname(lfile), filename=filename, as_attachment=True, attachment_filename=filename)
					else:
						self.log.warn('download file %s not exists', lfile)
						status = ErrorCode.ERR_SERVER_EXP
						errMsg = 'File {0} not exist, please sync from harvest first.'.format(_path)

				else:
					self.log.info('%s : harvest file list of %s', codepath, _path or '/')
					files = harvest_obj.listdir(_path)

			except Exception as e:
				self.log.error('SyncHarvest Exception : %s', e)
				status = ErrorCode.ERR_SERVER_EXP
				errMsg = e.message

			break # while
		
		return ReplyJson(status, msg=errMsg, files=files, count=len(files))


	def get(self, codepath):
		'''
       		<>/toolkit/harvest/redirect?type=sync
			<>/toolkit/harvest/redirect?type=files&path=/
	   	'''
		isset = False
		try:
			if self.lock.acquire(False):
				# sync call
				isset = True
				return self.sync_harvest(codepath, self.args.parse_args())
			else:
				# timeout responce
				self.log.warn('harvest checkout is ongoing.')
				return ReplyJson(ErrorCode.ERR_IN_PROGRESS)
		finally:
			if isset:
				# release lock at last
				self.lock.release()