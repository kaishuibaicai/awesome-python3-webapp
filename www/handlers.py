#!/usr/bin/env python3
#-*- coding:utf-8 -*-
''

__author__ = 'kaishuibaicai'

from models import User, Comment, Blog, next_id
from coroweb import get, post # 导入装饰器，这样就能方便的生成request handler
import re, time, json, logging, hashlib, base64, asyncio


# 此处所列所有的handler都会在app.py中通过add_routes自动注册到app.router上
# 因此，在此脚本尽情的书写request handler即可



# 对于首页的get请求的处理
@get('/')
async def index(request):
    # summary用于在博客首页上显示的句子，这样真的更有感觉
    summary = "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
    # 这里只是手动写了blogs的list，并没有真的将其存入数据库
    blogs = [
        Blog(id="1", name="Test1 Blog", summary=summary, created_at=time.time()-120),
        Blog(id="2", name="Test2 Blog", summary=summary, created_at=time.time()-3600),
        Blog(id="3", name="Test3 Blog", summary=summary, created_at=time.time()-7200)
    ]
    # 返回一个字典，其指示了使用何种模板，模板的内容
    # app.py的response_factory将会对handler的返回值进行分类处理
    return {
        "__template__": "blogs.html",
        "blogs": blogs
    }


@get('/api/users')
async def api_get_users():
    users = await User.findAll(orderBy='created_at desc')
    for u in users:
        u.passwd = '******'
    return dict(users=users)
