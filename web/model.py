# coding: utf-8

# using new type class
__metaclass__ = type

import os
import sqlite3
from datetime import date
from datetime import datetime

from helper import Singleton, init_logger


###########################################################################################
###  Sqlite db management
###########################################################################################
class ModelDB(Singleton):
	'''DB Manangement'''
	DB_NAME = 'apmtor.db'
	DB_SUBDIR = 'db'
	SQL_SCRIPT = 'model.sql'

	def __init__(self):
		'''initialize only once'''
		if not hasattr(self, '_initialized'):
			self._initialized = True
			self.db_path = None
			self.db_file = None
			self.log = init_logger()
	
	def init_db(self, db_path=None, overwrite=False):
		'''Initial database, if `overwrite` is `True`, it will reset all database tables'''
		db_path = os.path.join(db_path, ModelDB.DB_SUBDIR) if db_path else os.path.join(os.getcwd(), ModelDB.DB_SUBDIR)
		if not os.path.exists(db_path):
			os.makedirs(db_path)

		self.db_path = db_path
		self.db_file = os.path.join(db_path, ModelDB.DB_NAME)

		if not os.path.exists(self.db_file) or overwrite:
			script_file = os.path.join(self.db_path, ModelDB.SQL_SCRIPT)
			if os.path.exists(script_file):
				db = self.connect_db()
				with open(script_file, mode='r') as f:
					db.cursor().executescript(f.read())
				db.commit()
				self.log.info('db initialized: %s', self.db_file)
			else:
				self.log.warn('db not initialized, script file not exists: %s', script_file)

	def connect_db(self):
		'''Connects to the specific database.'''
		if self.db_path is None or self.db_file is None:
			self.init_db()
		rv = sqlite3.connect(self.db_file)
		rv.row_factory = sqlite3.Row
		return rv


# helper function
def connect_db():
	'''helper function used to connect db'''
	return ModelDB().connect_db()


###########################################################################################
###             Model class
###########################################################################################
class BaseModel:
	TABLE = ''
	COLUMN = ''
	PLACEHOLDER = ''

class BranchModel(BaseModel):
	TABLE = 'branchs'
	COLUMN = 'id,branch,product,sources,version,reldate,pcount'
	PLACEHOLDER = '?, ?, ?, ?, ?, ?, ?'

	__available_brs = None

	'''
	id		INTEGER PRIMARY KEY AUTOINCREMENT,			-- branch id
	branch	TEXT	NOT NULL,							-- branch name, eg: v5u4
	product	TEXT	DEFAULT "Unified Data Protection",	-- product name, eg: UDP
	sources	TEXT	NOT NULL,							-- source file path,
	version	TEXT	NOT NULL,							-- build verion, eg: 1989.1032
	reldate	TEXT	NOT NULL,							-- release date, eg: 2015.04.01
	pcount	INTEGER	NOT NULL							-- patch count of current branch
	'''
	def __init__(self, info={}):
		if isinstance(info, dict):
			self.id = None
			self.branch = info.get('branch')
			self.pcount = info.get('pcount', 0)
			self.product = info.get('product', 'Unified Data Protection')
			self.sources = info.get('sources', '')
			self.version = info.get('version', '')
			self.reldate = info.get('reldate', str(date.today()))
		elif isinstance(info, sqlite3.Row):
			self.id = info['id']
			self.branch = info['branch']
			self.pcount = info['pcount']
			self.product = info['product']
			self.sources = info['sources']
			self.version = info['version']
			self.reldate = info['reldate']
		else:
			raise ValueError("Invalid constructor parameter.")
		

	@property
	def value(self):
		return (self.id, self.branch, self.product, self.sources, self.version, self.reldate, self.pcount)
	
	@classmethod
	def get_branch(cls, idt):
		'''return BranchModel instance with `name` or `id` '''
		if cls.__available_brs is None:
			cls.__available_brs = cls.fetch_all()
		
		if isinstance(idt, (str, unicode)):
			for br in cls.__available_brs:
				if idt.lower() == br.branch.lower():
					return br
		elif isinstance(idt, (int, long)):
			for br in cls.__available_brs:
				if idt == br.id:
					return br
		return None

		
	@classmethod
	def get_branchs(cls):
		'''get all branchs, return instance array'''
		if cls.__available_brs is None:
			cls.__available_brs = cls.fetch_all()
		return cls.__available_brs


	@classmethod
	def fetch(cls, bid=None, branch=None):
		'''fetch first one item from table branchs'''
		with connect_db() as db:
			if not bid and not branch:
				cursor = db.execute(
					"SELECT * FROM %s" % (cls.TABLE)
				)
			elif bid and not branch:
				cursor = db.execute(
					"SELECT * FROM %s WHERE id==?" % (cls.TABLE),
					(bid,)
				)
			elif not bid and branch:
				cursor = db.execute(
					"SELECT * FROM %s WHERE branch==?" % (cls.TABLE),
					(branch,)
				)
			elif bid and branch:
				cursor = db.execute(
					"SELECT * FROM %s WHERE id==? and branch==?" % (cls.TABLE),
					(bid, branch)
				)
			return [BranchModel(v) for v in cursor.fetchall()]

	@classmethod
	def fetch_all(cls):
		'''fetch all items from table branchs'''
		with connect_db() as db:
			return [BranchModel(row) for row in db.execute("select * from %s" % (cls.TABLE))]

	@classmethod
	def count(cls):
		'''get the row counts of table branchs'''
		with connect_db() as db:
			row = db.execute("SELECT count(*) FROM %s" % (cls.TABLE)).fetchone()
			return row[0] if len(row) else 0
	
	def next_pid(self):
		'''get next patch id'''
		return 'P%05d' % (self.pcount + 1)

	def insert(self):
		'''insert a item into table branchs'''
		if not self.branch or self.id is not None:
			raise ValueError("Invalid branch to insert into database.")
		with connect_db() as db:
			cursor = db.execute(
				"SELECT id FROM %s WHERE branch==?" % (self.TABLE),
				(self.branch,)
			)
			if cursor.fetchone() is None:
				cursor = db.execute(
					"INSERT INTO %s (%s) VALUES (%s)" % (self.TABLE, self.COLUMN, self.PLACEHOLDER), 
					self.value
				)
				return cursor.rowcount
			else:
				print '%s already exist' % self.branch
				return 0

	def delete(self):
		'''delete an row from table branchs'''
		if not self.id or not self.branch:
			raise ValueError("Invalid branch id to delete from database.")
		with connect_db() as db:
			cursor = db.execute(
				"DELETE FROM %s WHERE id==? and branch==?" % (self.TABLE), 
				(self.id, self.branch)
			)
			return cursor.rowcount

	def update(self):
		'''update branch information in table Branchs'''
		if not self.id:
			raise ValueError("Invalid branch id to delete from database.")
		with connect_db() as db:
			cursor = db.execute(
				"UPDATE %s " \
				"SET branch=?, product=?, sources=?, version=?, reldate=?, pcount=? " \
				"WHERE id==?; " % (self.TABLE), 
				(self.branch, self.product, self.sources, self.version, self.reldate, self.pcount, self.id)
			)
			return cursor.rowcount

	def update_pcount(self):
		'''simple interface to increment pcount and update db'''
		if not self.id:
			raise ValueError("Invalid branch id to delete from database.")
		with connect_db() as db:
			self.pcount += 1
			cursor = db.execute(
				"UPDATE %s SET pcount=? WHERE id==?;" % (self.TABLE), 
				(self.pcount, self.id)
			)
			return cursor.rowcount


class PatchModel(BaseModel):
	TABLE = 'patchs'
	COLUMN = 'id,bid,pid,pproj,pfile,pdate,pdesc,ppath'
	PLACEHOLDER = '?, ?, ?, ?, ?, ?, ?, ?' 
	'''
	id		INTEGER PRIMARY KEY AUTOINCREMENT,	-- patch id
	bid		INTEGER ,							-- foreign key of branch id
	pid		TEXT	NOT NULL,					-- patch id of resided branch, eg: P00001
	pproj	TEXT	NOT NULL,					-- project name with extension
	pfile	TEXT	NOT NULL, 					-- files list with extension, seperated by ';'
	pdate	TEXT	NOT NULL,					-- patch date
	pdesc	TEXT	DEFAULT "",					-- patch description
	ppath	TEXT	DEFAULT ""					-- patch relative path
	'''
	def __init__(self, info={}):
		if isinstance(info, dict):
			self.id = None
			self.bid = info.get('bid', None)
			self.pid = info.get('pid', None)
			self.pproj = info.get('projs', '')
			self.pfile = info.get('files', '')
			self.pdate = info.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
			self.pdesc = info.get('desc', '')
			self.ppath = info.get('path', '')
		elif isinstance(info, sqlite3.Row):
			self.id = info['id']
			self.bid = info['bid']
			self.pid = info['pid']
			self.pproj = info['pproj']
			self.pfile = info['pfile']
			self.pdate = info['pdate']
			self.pdesc = info['pdesc']
			self.ppath = info['ppath']
		else:
			raise ValueError("Invalid constructor parameter.")

	@property
	def value(self):
		return (self.id, self.bid, self.pid, self.pproj, self.pfile, self.pdate, self.pdesc, self.ppath)
	
	@classmethod
	def fetch(cls, pid=None, bid=None):
		'''fetch one item from table'''
		with connect_db() as db:
			if not pid and not bid:
				cursor = db.execute(
					"SELECT * FROM %s" % (cls.TABLE)
				)
			elif not pid and bid:
				cursor = db.execute(
					"SELECT * FROM %s WHERE bid==?" % (cls.TABLE),
					(bid,)
				)
			elif pid and not bid:
				cursor = db.execute(
					"SELECT * FROM %s WHERE pid==?" % (cls.TABLE),
					(pid,)
				)
			elif pid and bid:
				cursor = db.execute(
					"SELECT * FROM %s WHERE pid==? and bid==?" % (cls.TABLE),
					(pid, bid)
				)
			return [PatchModel(v) for v in cursor.fetchall()]

	@classmethod
	def fetch_all(cls, bid=None):
		if not bid:
			sql = "SELECT * FROM %s;" % (cls.TABLE) 
		else:
			sql = "SELECT * FROM %s WHERE bid==%d;" % (cls.TABLE, int(bid))
		with connect_db() as db:
			return [PatchModel(row) for row in db.execute(sql)]

	@classmethod
	def count(cls):
		'''get the row counts of table patchs'''
		with connect_db() as db:
			row = db.execute("SELECT count(*) FROM %s" % (cls.TABLE)).fetchone()
			return row[0] if len(row) else 0
	
	def insert(self):
		'''insert a item into table patchs'''
		if self.id or not self.bid or not self.pid:
			raise ValueError("Invalid patch to insert into database.")
		insert_row = 0
		with connect_db() as db:
			cursor = db.execute(
				'SELECT id FROM %s WHERE pid==? and bid==?' % (self.TABLE), 
				(self.pid, self.bid)
			)
			if cursor.fetchone() is None:
				cursor = db.execute(
					"INSERT INTO %s (%s) VALUES (%s)" % (self.TABLE, self.COLUMN, self.PLACEHOLDER), 
					self.value
				)
				insert_row = cursor.rowcount

		if insert_row:
			BranchModel.get_branch(self.bid).update_pcount()
		else:
			print '%s already exist' % self.pid
		return insert_row

	def delete(self):
		'''delete an row from table patchs'''
		if not self.id or not self.pid:
			raise ValueError("Invalid patch id to delete from database.")
		with connect_db() as db:
			cursor = db.execute(
				"DELETE FROM %s WHERE id==? and pid==?" % (self.TABLE),
				(self.id, self.pid)
			)
			return cursor.rowcount

	def update(self):
		'''update patch information in table patchs'''
		if not self.id or not self.bid or not self.pid:
			raise ValueError("Invalid patch id to delete from database.")
		with connect_db() as db:
			cursor = db.execute(
				"UPDATE %s " \
				"SET bid=?, pid=?, pproj=?, pfile=?, pdate=?, pdesc=?, ppath=? " \
				"WHERE id==?; " % (self.TABLE), 
				(self.bid, self.pid, self.pproj, self.pfile, self.pdate, self.pdesc, self.ppath, self.id)
			)
			return cursor.rowcount

	def update_ppath(self):
		'''simple function to just upate ppath'''
		if not self.id or not self.bid or not self.pid:
			raise ValueError("Invalid patch id to delete from database.")
		with connect_db() as db:
			cursor = db.execute(
				"UPDATE %s " 	\
				"SET ppath=? " 	\
				"WHERE id==?; " % (self.TABLE), (self.ppath, self.id)
			)
			return cursor.rowcount



###########################################################################################
###             DB unit test operation
###########################################################################################

BRANCH_LIST = [
	{
		"branch"  : 'v5',
		"product" : 'Unified Data Protection',
		"sources" : u'D:\\Source\\WorkArea\\UDP_U4\\D2D\\Native',
		"version" : '1897',
		"reldate" : '2014-12-28',
		"pcount"  : 0
	},
	{
		"branch"  : 'v5u4',
		"product" : 'Unified Data Protection',
		"sources" : u'D:\\Source\\WorkArea\\UDP_U4\\D2D\\Native',
		"version" : '1897.1806',
		"reldate" : '2015-7-28',
		"pcount"  : 0
	},
	{
		"branch"  : 'v6',
		"product" : 'Unified Data Protection',
		"sources" : u'D:\\Source\\WorkArea\\UDP_U4\\D2D\\Native',
		"version" : '3972',
		"reldate" : '2016-02-01',
		"pcount"  : 0
	},
	{
		"branch"  : 'v6u3',
		"product" : 'Unified Data Protection',
		"sources" : u'D:\\Source\\WorkArea\\UDP_U4\\D2D\\Native',
		"version" : '3972.774',
		"reldate" : '2016-8-19',
		"pcount"  : 0
	}
]

TEST_PATCH = [
	{
		"bid"	: 1 ,
		"pid"	: "P00001",
		"pproj" : "AFBackend.vcxproj",
		"pfile"	: "a.cpp;b.cpp;c.h",
		#"pdate" : "",
		"pdesc"	: "Test patch 1",
		"ppath" : "C:\\test\\native\\web\\P00001"
	},
	{
		"bid"	: 1 ,
		"pid"	: "P00002",
		"pproj" : "DRCore.vcxproj",
		"pfile"	: "d.cpp;e.cpp;f.h",
		#"pdate" : "",
		"pdesc"	: "Test patch 2 for v5",
		#"ppath" : ""
	},
	{
		"bid"	: 3 ,
		"pid"	: "P00001",
		"pproj" : "AFMntMgr.vcxproj",
		"pfile"	: "h.cpp;g.cpp;t.h",
		#"pdate" : "",
		"pdesc"	: "Test patch 3",
		#"ppath" : ""
	}
]


def insert_default_branchs():
	for v in BRANCH_LIST:
		br = BranchModel(v)
		br.insert()

def insert_default_patchs():
	for v in TEST_PATCH:
		ph = PatchModel(v)
		ph.insert()

def show_all_branchs():
	for v in BranchModel.fetch_all():
		print v.value

def show_all_patchs(bid=None):
	for v in PatchModel.fetch_all(bid):
		print v.value


def test():
	#init_db()
	insert_default_branchs()
	insert_default_patchs()
	
	print "total count:", BranchModel.count()
	show_all_branchs()

	print "patch count:", PatchModel.count()
	show_all_patchs()
	
	print "patch count for bid==1 is:", len(PatchModel.fetch_all(bid=1))

	print "update branch id == 1:"
	br = BranchModel.fetch(bid=1)[0]
	br.pcount = 20
	br.update()
	print br.value

	print "branch id == 1:"
	br2 = BranchModel.fetch(branch='v5')[0]
	print br2.value

	print "update patch id == 1:"
	ph = PatchModel.fetch(pid="P00001")[0]
	ph.ppath = r"C:\test\native\web\P00001"
	ph.update()
	print ph.value

	print "patch id == 1:"
	ph2 = PatchModel.fetch(pid="P00001")[0]
	print ph2.value

