import logging; logging.basicConfig(level=logging.INFO)

import asyncio, os, json, time     #asyncio的编程模型就是一个消息循环
from datetime import datetime
from aiohttp import web

def index(request):
	return web.Response(body=b'<h1>Awesome</h1>', content_type='text/html')

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
