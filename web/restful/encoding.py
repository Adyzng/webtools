# coding: utf-8

""""
Wrapper of message encrypt and decrypt: base64, udpenc, md5, sha1, sha256
"""
import os
import ctypes

import base64
import hashlib

#from flask import request
from flask_restful import Resource, Api, reqparse

from web.helper import ErrorCode, ReplyJson, init_logger, utf8_unicode
from web.settings import ENVIRONS


class MessageEncoder(Resource):
	'''message encrypt and decrypt
    :request
        source: source message without encrypt
        udp: udp encrypted message
        base64: base64 encrypted message
    :respone
        source: str
        udp: str
        base64: str
        md5: str
        sha1: str
        sha256: str
    '''
	def __init__(self):
		self.log = init_logger()
		self.args = reqparse.RequestParser()
		self.args.add_argument('source', default='', help='source none encrypted message')
		self.args.add_argument('base64', default='', help='base64 encrypted message')
		self.args.add_argument('udp', default='', help='udp encrypted message')
		
	@classmethod
	def register(clz, api):
		if isinstance(api, Api):
			api.add_resource(clz, '/toolkit/encdec', endpoint='encdec')
		else:
			raise TypeError('Unsupported parameter type: %s', type(api))

	def udp_enc_dec(self, source, encrypt=True):
		'''call UDP module AFCoreFunction.dll '''
		try:
			cur_dir = os.getcwd()
			module_name = os.path.join(ENVIRONS['udpbin'], 'AFCoreFunction.dll')
			os.chdir(os.path.dirname(module_name))

			AFCoreFunction = ctypes.WinDLL(os.path.basename(module_name))
			self.log.debug('loaded windows module: %s', module_name)

			if encrypt :
				udp_func = AFCoreFunction.AFEncryptToString
			else:
				udp_func = AFCoreFunction.AFDecryptFromString

			if udp_func :
				buf_len = ctypes.c_long(0)
				source = utf8_unicode(source) # change to uncode format if source is str 
				
				udp_func(source, None, ctypes.byref(buf_len))
				out_buf = ctypes.create_unicode_buffer(u'\0' * buf_len.value)
				if udp_func(source, out_buf, ctypes.byref(buf_len)):
					return out_buf.value
		except Exception as e:
			self.log.error('Call native library [AFCoreFunction.dll] failed. err = %X.', ctypes.GetLastError())
			self.log.exception('Exception')
		finally:
			os.chdir(cur_dir)
		return None

	
	def do_convert(self, args):
		'''real convert job'''

		md5, sha1, sha256 = '', '', ''
		status = ErrorCode.ERR_SUCCESS
		errmsg = None

		source = args['source']
		udp_fmt = None if source else args['udp']
		base_64 = None if source else args['base64']
		self.log.info('source message : %s, udp: %s, base64: %s', source, udp_fmt, base_64)

		try:
			# first, decode from udp encrypted format if source is None
			if not source and udp_fmt:
				source = self.udp_enc_dec(udp_fmt, False)
				if not source:
					status = ErrorCode.ERR_DECRYPT_MSG
					errmsg = 'udp decrypted message failed'
				
			# then, decode from base64 encrypted format if source is None
			if not source and base_64:
				source = base64.b64decode(base_64)
				if not source:
					status = ErrorCode.ERR_DECRYPT_MSG
					errmsg = 'base64 decrypted message failed'
			
			# calc md5/sha1/sha256
			if source:
				udp_fmt = udp_fmt if udp_fmt else self.udp_enc_dec(source)
				base_64 = base_64 if base_64 else base64.b64encode(source)
				md5 = hashlib.md5(source).hexdigest()
				sha1 = hashlib.sha1(source).hexdigest()
				sha256 = hashlib.sha256(source).hexdigest()

		except Exception as e:
			self.log.exception('Exception')
			status = ErrorCode.ERR_ENCRYPT_MSG
			return ReplyJson(status, errmsg, source=source)
		
		return ReplyJson(status, errmsg, source=source, udp=udp_fmt, base64=base_64, md5=md5, sha1=sha1, sha256=sha256)

	def get(self):
		'''message encrypt and decrypt
       		GET <>/toolkit/encdec?source=&udp=&base64=
	   	'''
		return self.do_convert(self.args.parse_args())

	def post(self):
		'''message encrypt and decrypt
       		POST <>/toolkit/encdec
	   	'''
		return self.do_convert(self.args.parse_args())
	