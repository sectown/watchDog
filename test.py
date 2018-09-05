#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/9/3 8:52 AM
# @Author  : Steven
# @Contact : 523348709@qq.com
# @Site    : 
# @File    : test.py
# @Software: PyCharm
import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import time

def on_message(ws, message):
    print(message)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    # def run(*args):
    #     for i in range(3):
    #         time.sleep(1)
    #         ws.send("Hello %d" % i)
    #     time.sleep(1)
    #     ws.close()
    #     print("thread terminating...")
    # thread.start_new_thread(run, ())
    # ws.send('hello')
    print('open')


if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://localhost:8080/ws",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close,
                              on_open=on_open)
    # ws.on_open = on_open
    ws.run_forever()