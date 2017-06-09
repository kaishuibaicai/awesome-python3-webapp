#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'kaishuibaicai'

import asyncio, logging

import aiomysql


def log(sql, args=()):
	logging.info('SQL: %s' % sql)                         #生成日志信息


async def create_pool(loop, **kw):                            #*args是非关键字参数，用于元组，**kw是关键字参数，用于字典，详见：https://kelvin.mbioq.com/2015/08/04/what-does-kw-args-mean-in-python.html

	logging.info('create database connection pool...')    #生成日志信息：创建数据库连接池，每个http请求都从池中获取数据库连接。
	global __pool
	__pool = await aiomysql.create_pool(                  #aiomysql的创建连接池方法：http://aiomysql.readthedocs.io/en/latest/pool.html

		host=kw.get('host', 'localhost'),
		port=kw.get('port', 3306),
		user=kw['user'],
		password=kw['password'],
		db=kw['db'],
		charset=kw.get('charset', 'utf8'),
		autocommit=kw.get('autocommit', True),
		maxsize=kw.get('maxsize', 10),
		minsize=kw.get('minsize', 1),
		loop=loop
		)


async def select(sql, args, size=None):                        #数据库选择函数，需要传入SQL语句和SQL参数
	log(sql, args)
	global __pool
	async with __pool.get() as conn:
		async with conn.cursor(aiomysql.DictCursor) as cur:        #将游标设置为返回字典的游标，有方法和参数都合Cursor相同：http://aiomysql.readthedocs.io/en/latest/cursors.html?highlight=dictcursor

			await cur.execute(sql.replace('?', '%s'), args or ()) #SQL语句的占位符是？，而MySQL的占位符是%s，需要内部替换
			if size:                                           #如果传入size参数，通过fetchmany(size)获取指定数量的记录
				rs = await cur.fetchmany(size)
			else:                                              #否则通过fetchall()获取所有记录
				rs = await cur.fetchall()
		logging.info('rows returned: %s' % len(rs))
		return rs


async def execute(sql, args, autocommit=True):
	log(sql)
	async with _pool.get() as conn:
		if not autocommit:
			await conn.begin()
		try:
			async with conn.cursor(aiomysql.DictCursor) as cur:
				await cur.execute(sql.replace('?', '%s'), args)
				affected = cur.rowcount
			if not autocommit:
				await conn.commit()
		except BaseException as e:
			if not autocommit:
				await conn.rollback()
			raise
		return affected


def create_args_string(num):         #这个函数在元类中被引用，作用是创建一定数量的占位符
	L = []
	for n in range(num):
		L.append('?')        #例如：num=3, 那么L就是['?', '?', '?'],通过下面的代码返回字符串'?, ?, ?'
	return ', '.join(L)


class Field(object):                 #定义字段基类，后面各种各样的字段类都集成这个基类
	def __init__(self, name, column_type, primary_key, default):
		self.name = name                  #字段名
		self.column_type = column_type    #字段类型
		self.primary_key = primary_key    #主键
		self.default = default            #默认值
	
	def __str__(self):
		return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)


class StringField(Field):
	def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
		super().__init__(name, ddl, primary_key, default)


class BooleanField(Field):
	def __init__(self, name=None, default=False):
		super().__init__(name, 'boolean', False, default)


class IntegerField(Field):
	def __init__(self, name=None, primary_key=False, default=0):
		super().__init__(name, 'bigint', primary_key, default)


class FloatField(Field):
	def __init__(self, name=None, primary_kay=False, default=0.0):
		super().__init__(name, 'real', primary_key, default)


class TextField(Field):
	def __init__(self, name=None, default=None):
		super().__init__(name, 'text', False, default)




class ModelMetaclass(type):
	def __new__(cls, name, bases, attrs):
		if name == 'Model':
			return type.__new__(cls, name, bases, attrs)
		tableName = attrs.get('__table__', None) or name
		logging.info('found model: %s (table: %s)' % (name, tableName))
		mappings = dict()
		fields = []
		primaryKey = None
		for k, v in attrs.items():
			if isinstance(v, Field):
				logging.info('  found mapping: %s ==> %s' % (k, v))
				mappings[k] = v
				if v.primary_key:
					if primaryKey:
						raise StandardError('Duplicate primary key for field: %s' % k)
					primaryKey = k
				else:
					fields.append(k)
		if noet primaryKey:
			raise StandardError('Primary key not found.')
		for k in mapping.keys():
			attrs.pop(k)
		escaped_fields = list(map(lambda f: '`%s`' % f, fields))
		attrs['__mappings__'] = mappings    #保存属性和列的映射关系
		attrs['__table__'] = tableName
		attrs['__primary_key__'] = primaryKey    #主键属性名
		attrs['__fields__'] = fields             #除主键外的属性名
		attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
		attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
		attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
		attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
		return type.__new__(cls, name, bases, attrs)

class Model(dict, mataclass=ModelMetaclass):
	def __init__(self, **kw):
		super(Model, self).__init__(**kw)
	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Model' object has no attribute '%s'" % key)
	def __setattr__(self, key, value):
		self[key] = value
	def getValue(self, key):
		return getattr(self, key, None)
	def getValueOrDefault(self, key):
		value = getattr(self, key, None)
		if value is None:
			field = self.__mappings__[key]
			if field.default is not None:
				value = field.default() if callable(field.default) else field.default
				logging.debug('using default value for %s: %s' % (key, str(value)))
				setattr(self, key, value)
		return value


@classmethod
async def findAll(cls, where=None, args=None, **kw):
	' find objects by where clause. '
	sql = [cls.__select__]
	if where:
		sql.append('where')
		sql.append(where)
	if args is None:
		args = []
	orderBy = kw.get('orderBy', None)
	if orderBy:
		sql.append('order by')
		sql.append(orderBy)
	limit = kw.get('limit', None)
	if limit is not None:
		sql.append('limit')
		if isinstance(limit, int):
			sql.append('?')
			args.append(limit)
		elif isinstance(limit, tuple) and len(limit) == 2:
			sql.append('?, ?')
			args.extend(limit)
		else:
			raise ValueError('Invalid limit value: %s' % str(limit))
	rs = await select(' '.join(sql), args)
	return [cls(**r) for r in rs]


@classmethod
async def findNumber(cls, selectField, where=None, args=None):
	' find number by select and where. '
	sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
	if where:
		sql.append('where')
		sql.append(where)
	rs = await select(' '.join(sql), args, 1)
	if len(rs) == 0:
		return None
	return re[0]['_num_']


@classmethod
async def find(cls, pk):
	' find object by primary key. '
	rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
	if len(rs) == 0:
		return None
	return cls(**rs[0])


async def save(self):
	args = list(map(self.getValueOrDefault, self.__fields__))
	args.append(self.getValueOrDefault(self.__primary_key__))
	rows = await execute(self.__insert__, args)
	if rows != 1:
		logging.warn('failed to insert record: affected rows: %s' % rows)


async def update(self):
	args = list(map(self.getValue, self.__fields__))
	args.append(self.getValue(self.__pramary_key__))
	rows = await execute(self.__update__, args)
	if rows !=1:
		logging.warn('failed to update by primary key: affected rows: %s' % rows)


async def remove(self):
	args = [self.getValue(self.__primary_key__)]
	rows = await execute(self.__delete__, args)
	if rows != 1:
		logging.warn('failed to remove by primary key: affected rows: %s' % rows)
