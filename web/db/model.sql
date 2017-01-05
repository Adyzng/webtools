DROP TABLE if exists branchs;
CREATE TABLE branchs (
	id		INTEGER PRIMARY KEY AUTOINCREMENT,			-- branch id
	branch	TEXT	NOT NULL,							-- branch name, eg: v5u4
	product	TEXT	DEFAULT "Unified Data Protection",	-- product name, eg: UDP
	sources	TEXT	NOT NULL,							-- source file path,
	version	TEXT	NOT NULL,							-- build verion, eg: 1989.1032
	reldate	TEXT	NOT NULL,							-- release date, eg: 2015.04.01
	pcount	INTEGER	NOT NULL							-- patch count of current branch
);

DROP TABLE if exists patchs;
CREATE TABLE patchs (
	id		INTEGER PRIMARY KEY AUTOINCREMENT,	-- patch id
	bid		INTEGER,							-- foreign key of branch id
	pid		TEXT	NOT NULL,					-- patch id of resided branch, eg: P00001
	pproj	TEXT	NOT NULL,					-- project name with extension
	pfile	TEXT	NOT NULL, 					-- files list with extension, seperated by ';'
	pdate	TEXT	NOT NULL,					-- patch date
	pdesc	TEXT	DEFAULT "",					-- patch description
	ppath	TEXT	DEFAULT "",					-- patch relative path
	FOREIGN KEY(bid) REFERENCES branchs(bid)	-- foreign key of branch id
);