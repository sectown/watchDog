#!/usr/bin/env python

from socket import error as timeerror
import socket
from websocket import *
import time
import platform
import uuid
import os
import atexit

try:
    import thread
except ImportError:
    import _thread as thread
import json

register_url = "ws://localhost:8080/ws"
MAC=uuid.UUID(int=uuid.getnode()).hex[-12:]

# data = {
#     'type': msg_type,
#     'detail': {
#         "mode": mode,
#         "mac": mac,
#         "code": code,
#         "result": result,
#         "info": info
#     }
# }

# 初始化连接
def init_connection():
    while (True):
        try:
            ws = create_connection(register_url, timeout=3)
            print('Connection set up')
            return ws
        except timeerror as error:
            print("Timeout")


# 获取系统信息
def get_info():
    computerName = platform.node()
    systemInfo = platform.platform()
    cpuInfo = platform.processor()
    systemType = platform.system()
    hd_available = 'N/A'
    hd_capacity = 'N/A'
    hd_used = 'N/A'
    ip='N/A'

    # 获取HD信息
    if systemType!='Windows':
        disk = os.statvfs("/")
        hd_available = int(disk.f_bsize * disk.f_bavail / (1099511627776))
        hd_capacity = int(disk.f_bsize * disk.f_blocks / (1099511627776))
        hd_used= int(disk.f_bsize * disk.f_bfree / (1099511627776))


    #获取IP信息
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    t = int(time.time())
    data = {
        'name': computerName,
        'systemInfo': systemInfo,
        'cpuInfo': cpuInfo,
        'systemType': systemType,
        'availableHD': hd_available,
        'capacityHD': hd_capacity,
        'usedHD': hd_used,
        'time': t,
        'ip':ip
    }
    return data_package(msg_type='info', mac=MAC,info=data)


# ping包
def get_ping_payload():
    return data_package(msg_type='ping', mac=MAC)


# 包封装
def data_package(msg_type,mac,mode="",code="",result="",info=None):
    if info==None:
        info=""
    data = {
        'type': msg_type,
        'detail':{
            "mode":mode,
            "mac":mac,
            "code":code,
            "result":result,
            "info":info
        }
    }
    return json.dumps(data)


# 对json数据转换为字典
def format_message(message):
    message = json.loads(message)
    msg_type = message['type']
    detail = message['detail']
    mode = detail['mode']
    code = detail['code']
    return msg_type, mode, code

def program_close(ws):
    print('all done')
    ws.close()
if __name__ == '__main__':
    try:
        NUM = 0
        BEATTIME = 5
        ws=None
        ws = init_connection()

        while (True):
            if ws.connected:
                # 发送系统信息
                systemData = get_info()
                pingPayload = get_ping_payload()
                ws.ping(payload=pingPayload)
                # 等待信息
                try:
                    ws.send(systemData)
                    result = ws.recv()
                    print("[result]:" + result)
                    msg_type, mode,code = format_message(result)

                    if mode=='cmd':
                        cmd_result=os.popen(code).read()
                        data=data_package(msg_type='operation',mode='result',mac=MAC,result=cmd_result)
                        ws.send(data)

                        _=ws.recv()

                except WebSocketTimeoutException:
                    NUM = NUM + 1
                    print('HeartBeat-%d' % NUM)
                    pass
                time.sleep(BEATTIME)
            else:
                # 如果连接失败，就重新初始化
                ws = init_connection()
    except KeyboardInterrupt:
        if ws!=None:
            program_close(ws=ws)
