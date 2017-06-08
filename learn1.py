#!/usr/bin/env/ python3
#-*- coding:utf-8 -*-

__author__ = 'kaishuibaicai'

import aiomysql
import asyncio, logging

def log(sql, args=()):
	logging.info('SQL: %s' % sql)

@asyncio.coroutine
def create_pool(loop, **kw):          #创建连接池，每个HTTP请求都可以从连接池直接获取数据库连接。不用频繁打开关闭数据库。
        logging.info('create database connection pool...')
        global __pool
        __pool = yield from aiomysql.create_pool(
                host=kw.get('host', 'localhost'),
                port=kw.get('port', 3306),
                user=kw['user'],
                password=kw['password'],
                db=kw['db'],
                charset=kw.get('charset', 'utf8'),
                autocommit=kw.get('autocommit', True),
                maxsize=kw.get('maxsize', 10),
                minsiza=kw.get('minsize', 1),
                loop=loop
        )


@asyncio.coroutine
def select(sql, args, size=None):       #select函数执行，需要传入SQL语句和SQL参数
        log(sql, args)
        global __pool
        with (yield from __pool) as conn:
                cur = yield from conn.cursor(aiomysql.DictCursor)
                yield from cur.execute(sql.replace('?', '%s'), args or ())  #SQL语句的占位符是？，而MySQL的占位符是%s，需要内部替换
                if size:                                                    #如果传入size参数，通过fetchmany(size)获取指定数量的记录
                        rs = yield from cur.fetchmany(size)
                else:                                                       #否则通过fetchall()获取所有记录
                        rs = yield from cur.fetchall()
                yield from cur.close()
                logging.info('rows returned: %s' % len(rs))
                return rs


@asyncio.coroutine
def execute(aql, args, autocommit=True):                  #execute()函数和select()函数不同的是：cursor对象不返回结果集，而是通过rowcount返回结果数
        log(sql)
        with (yield from __pool) as conn:
                try:
                        cur = yield from conn.cursor()
                        yield from cur.execute(sql.replace('?', '%s'), args)
                        affected = cur.rowcount
                        yield from cur.close()
                except BaseException as e:
                        raise
                return affected
class Field(object):
	def __init__(self, name, column_type, primary_key, default):
		self.name = name
		self.column_type = column_type
		self.primary_key = primary_key
		self.default = default
	def __str__(self):
		return '<%s, %s:%s>' %(self.__class__.__name__, self.column_type, self.name)

class StringField(Field):
	def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
		super().__init__(name, ddl, primary_key, default)

class ModelMetaclass(type):
	def __new__(cls, name, bases, attrs):
		if name == 'Model':                   #排除Model类本身
			return type.__new__(cls, name, bases, attrs)
		tableName = attrs.get('__table__', None) or name               #获取table名称
		logging.info('found model: %s (table: %s)' % (name, tableName))
		mappings = dict()                     #获取所有的Field和主键名
		fields = []
		primaryKey = None
		for k, v in attrs.items():
			if isinstance(v, Field):
				logging.info('  found mapping: % ==> %s' % (k, v))
				mappings[k] = v
				if v.primary_key:             
					if primaryKey:           #找到主键
						raise RuntimeError('Duplicate primary key for field: %s' % k)
					primaryKey = k
				else:
					fields.append(k)
		if not primaryKey:
			raise RuntimeError('Primary key not found.')
		for k in mappings.keys():
			attrs.pop(k)
		escaped_fields = list(map(lambda f: '^%s^' % f, fields))
		attrs['__mappings__'] = mappings                 #保存属性和列的映射关系
		attrs['__table__'] = tableName
		attrs['__primary_key__'] = primaryKey            #主键属性名
		attrs['__fields__'] = fields                     #除主键外的属性名
		#构建默认的SELECT， INSERT， UPDATE和DELETE语句：
		attrs['__select__'] = 'select ^%s^, %s from ^%s^' %(primaryKey, ', '.join(escaped_fields), tableName)
		attrs['__insert__'] = 'insert into ^%s^ (%s, ^%s^) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
		attrs['__update__'] = 'update ^%s^ set %s where ^%s^ =?' % (tableName, ', '.join(map(lambda f: '^%s^=?' % (mappings.get(f).name or f), fields)), primaryKey)
		attrs['__delete__'] = 'delete from ^%s^ where ^%s^=?' % (tableName, primaryKey)
		return type.__new__(cls, name, bases, attrs)

class Model(dict, metaclass=ModelMetaclass):
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
		if value is None:
			field = self.__mappings__[key]
			if field.default is not None:
				value = field.default() if callable(field.default) else field.default
				logging.debug('using default value for %s: %s' % (key, str(value)))
				setattr(self, key, value)
		return value	

	@classmethod
	@asyncio.coroutine
	def find(cls, pk):                                  #实现主键查找
		'find object by primary key.'
		rs = yield from select('%s where ^%s^ =?' % (cls.__select__, cls.__primary_key__), [pk], 1)
		if len(rs) == 0:
			return None
		return cls(**rs[0])

	@asyncio.coroutine
	def save(self):                                      #User实例存入数据库方法
		args = list(map(self.getValueOrDefault, self.__fields__))
		args.append(self.getValueOrDefault(self.__primary_key__))
		rows = yield from execute(self.__insert__, args)
		if rows != 1:
			logging.warn('failed to insert record: affected rows: %s' % rows)

class User(Model):                    #定义一个user对象，__table__,id,name是类的属性，不是实例的属性，类级别上定义的属性用来描述User和表的映射
	__table__ = 'users'
	id = IntegerField(primary_key=True)
	name = StringField()

