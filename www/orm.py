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

			await cur.execute(sql.replace('?', '%s'), args or ())
			if size:
				rs = await cur.fetchmany(size)
			else:
				rs = await cur.fetchall()
		logging.info('rows returned: %s' % len(rs))
		return rs

