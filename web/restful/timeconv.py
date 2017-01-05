# coding: utf-8

""""
Wrapper of time counvert between seconds/local/utc
"""

import time
#from datetime import datetime

#from flask import request
from flask_restful import Resource, Api, reqparse

# helper class/function
from web.helper import ErrorCode, ReplyJson, init_logger

class TimeConvert(Resource):
	'''convert millisecond and localtime/utctime

    :request
        sec : seconds
        utc : utc time string, format: %Y-%m-%d %H:%M:%S
        local : local time string, format: %Y-%m-%d %H:%M:%S
    :response
        sec : seconds
        utc : utc time string, format: %Y-%m-%d %H:%M:%S
        local : local time string, format: %Y-%m-%d %H:%M:%S
        timezone: string
    '''

	def __init__(self):
		self.log = init_logger()
		self.args = reqparse.RequestParser()
		self.args.add_argument('sec', default='', help='seconds since 1970.01.01 00:00:00')
		self.args.add_argument('utc', default='', help='utc time string with format: %Y-%m-%d %H:%M:%S')
		self.args.add_argument('local', default='', help='local time string with format: %Y-%m-%d %H:%M:%S')

	@classmethod
	def register(clz, api):	
		if isinstance(api, Api):
			api.add_resource(clz, '/toolkit/timeconvert', endpoint='timeconvert')
		else:
			raise TypeError('Unsupported parameter type: %s', type(api))
	

	def do_convert(self, args):
		'''do convert'''
		try:
			long_sec = args['sec']
			utc_tms, local_tms = args['utc'], args['local']
			status = ErrorCode.ERR_SUCCESS
			self.log.info('input time: sec=%s, utc=%s, local=%s', long_sec, utc_tms, local_tms)

			if long_sec: 
				long_sec = long(float(long_sec))

			if not long_sec and not utc_tms and not local_tms:
				long_sec = long(time.time())

			str_fmt = '%Y-%m-%d %H:%M:%S'
			if not long_sec and utc_tms:
				# mktime() convert to local time, so need to conside the timezone (negtive value)
				# using utc time
				long_sec = long(time.mktime(time.strptime(utc_tms, str_fmt)) - time.timezone)
			elif not long_sec and local_tms:
				# using local time
				long_sec = long(time.mktime(time.strptime(local_tms, str_fmt)))
			else:
				# using seconds
				long_sec = long_sec
			
			utc_tms = time.strftime(str_fmt, time.gmtime(long_sec))
			local_tms = time.strftime(str_fmt, time.localtime(long_sec))
			self.log.info('after convert: sec=%s, utc=%s, loc=%s', long_sec, utc_tms, local_tms)
			
		except Exception as e:
			self.log.error('TimeConvert exception : %s', e)
			status = ErrorCode.ERR_TIME_FORMAT
			return ReplyJson(status)

		return ReplyJson(status, sec=long_sec, utc=utc_tms, local=local_tms, timezone=', '.join(time.tzname))


	def get(self):
		'''convert millisecond and localtime/utctime
		   GET <>/toolkit/timeconvert?sec=&utc=&local=
		'''
		return self.do_convert(self.args.parse_args())

	def post(self):
		'''convert millisecond and localtime/utctime
		   POST <>/toolkit/timeconvert
		'''
		return self.do_convert(self.args.parse_args())

