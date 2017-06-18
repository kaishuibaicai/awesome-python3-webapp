#!/usr/bin/env python3
#-*- coding:utf-8 -*-

__author__ = 'kaishuibaicai'

'''
async web application
'''

import logging; logging.basicConfig(level=logging.INFO)

import asyncio, os, json, time     #asyncio的编程模型就是一个消息循环.

from datetime import datetime
from aiohttp import web

from coroweb import get
from models import User


def index(request):
    return web.Response(body=b'<h1>Awesome</h1>', content_type='text/html')   #此处的content_type参数默认值是None，设置成'text/html'解决浏览器提示保存的问题。




@asyncio.coroutine        #把一个generator标记为coroutine类型
def init(loop):           #init()是协程coroutine，是aiohttp的初始化函数
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', index)
    srv = yield from loop.create_server(app.make_handler(), '127.0.0.1', 9000)       #loop.create_server()则利用asyncio创建TCP服务
    logging.info('server started ai http://127.0.0.1:9000...')
    return srv


loop = asyncio.get_event_loop()               #获取asyncio里的EventLoop的引用，实现异步IO
loop.run_until_complete(init(loop))           #把上面的coroutine传到EventLoop中执行
loop.run_forever()                            #一直重复执行监听
