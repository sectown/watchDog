#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/8/27 12:55 PM
# @Author  : Steven
# @Contact : 523348709@qq.com
# @Site    :
# @File    : main.py
# @Software: PyCharm
import tornado.web
import tornado.websocket
import tornado.httpserver
import tornado.ioloop
import json
import inspect
import os


class IndexPageHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class wsHandler(tornado.websocket.WebSocketHandler):
    MANAGER_CODE = 'HELLO'
    MANAGER_SOCKET = None
    hosts = {}  # host mac地址与socket对应 mac键值
    hostsData = {}  # 主机信息，用于更新主机信息 mac键值
    waiters = set()

    def check_origin(self, origin):
        return True

    def open(self):

        pass

    # 消息控制
    def on_message(self, message):
        # 对数据全部转换为字典 统一化处理
        type, detail = self.format_message(message)
        message = json.loads(message)

        self.debugger(type)
        if (type == 'show'):
            # 判断MANAGER_CODE是否一致，防止伪造
            if detail['code'] == wsHandler.MANAGER_CODE:
                wsHandler.MANAGER_SOCKET = self
                wsHandler.send_browser_data(msg_type='show', info='Welcome')

        elif (type == 'info'):
            # 收到新的系统信息后对信息进行更新

            #如果非第一次接入服务器，则进入if
            if detail['mac'] in wsHandler.hostsData:
                #如果是页面发来改变checked状态的，则进入if，否则不更新checked状态
                if 'checked' in detail['info']:
                    wsHandler.hostsData[detail['mac']]['checked']=detail['info']['checked']
            #第一次接入服务器，服务器存储添加字段checked
            else:
                detail['info']['checked']=False
                wsHandler.hostsData[detail['mac']] = detail['info']

            # 开始页面更新
            wsHandler.debugger(wsHandler.hostsData)
            wsHandler.send_browser_data(msg_type='info', info=wsHandler.hostsData)

        elif (type == 'operation'):
            # 直接发送原json数据
            if (detail['mode'] == "cmd"):  # 向客户机发送命令
                for mac in wsHandler.hostsData:
                    if wsHandler.hostsData[mac]['checked']:
                        wsHandler.hosts[mac].write_message(message)

            if (detail['mode'] == "result"):  # 向浏览器发送客户机命令执行结果
                self.write_message("_")
                wsHandler.send_browser_data(raw_data=message, reform=False)

    def on_close(self):
        # 如果是客户机断开连接则移除，否则置空MANAGER_SOCKET
        wsHandler.debugger('someone out')
        if self!=wsHandler.MANAGER_SOCKET:
            tmp_dict = {v: k for k, v in wsHandler.hosts.items()}
            tmp_mac = tmp_dict[self]
            del wsHandler.hosts[tmp_mac]
            del wsHandler.hostsData[tmp_mac]
            tmp_dict.clear()
            wsHandler.waiters.remove(self)
            wsHandler.debugger(wsHandler.hostsData)
            wsHandler.debugger(wsHandler.hosts)
        else:
            if wsHandler.MANAGER_SOCKET != None:
                if self == wsHandler.MANAGER_SOCKET:
                    wsHandler.MANAGER_SOCKET = None



    # 接收客户机的ping包
    def on_ping(self, data):
        data = data.decode()
        type, detail = self.format_message(data)
        # 记录主机mac地址和ping回溯时间\socket连接
        wsHandler.hosts[detail['mac']] = self
        # 记录下该socket
        wsHandler.waiters.add(self)

    # 用于发送广播
    @classmethod
    def broadcast(cls, data):
        for waiter in wsHandler.waiters:
            waiter.write_message(data)

    @classmethod
    def send_browser_data(cls, msg_type="", mac="", mode="", code="", result="", info=None, raw_data="", reform=True):
        if info == None:
            info = ""
        if reform:
            raw_data = {
                'type': msg_type,
                'detail': {
                    "mode": mode,
                    "mac": mac,
                    "code": code,
                    "result": result,
                    "info": info
                }
            }
        data = json.dumps(raw_data)
        if wsHandler.MANAGER_SOCKET != None:
            wsHandler.MANAGER_SOCKET.write_message(data)

    # 对json数据转换为字典
    @classmethod
    def format_message(cls, message):
        f_message = json.loads(message)
        type = f_message['type']
        detail = f_message['detail']

        return type, detail

    # 调试信息输出
    @classmethod
    def debugger(cls, data):
        print('[*]%s--->%s' % (inspect.stack()[1][3], data))


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', IndexPageHandler),
            (r'/ws', wsHandler),
        ]
        settings = {
            "template_path": os.path.join(os.path.dirname(__file__), "templates"),
            "static_path": "statics"
        }
        tornado.web.Application.__init__(self, handlers, **settings, debug=True)


if __name__ == '__main__':
    ws_app = Application()
    server = tornado.httpserver.HTTPServer(ws_app)
    server.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
