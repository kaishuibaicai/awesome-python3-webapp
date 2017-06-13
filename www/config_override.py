#!/usr/bin/env python3
#-*- coding:utf-8 -*-

'自定义的配置文件，用于覆盖一些默认配置，从而避免对默认文件的直接修改'

__author__ = 'kaishuibaicai'

config = {
    "db":{     # 重载的数据库信息，将会覆盖默认的数据库相关配置信息
        "host": "127.0.0.1"
    }
}
