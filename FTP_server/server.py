#! usr/bin/env python
# -*- coding: utf-8 -*-
# __author: iamironman
# @file: server.py
# @time: 2019年01月23日
# @email: 875674794@qq.com


import struct
import os
import json
import sys
import pickle
import hashlib
import socketserver

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
rootdir = BASE_DIR + '/root'


def sk_sr(conn):
    operate_bytes_len = struct.unpack('i', conn.recv(4))[0]
    operate_bytes = conn.recv(operate_bytes_len)
    operate_json = operate_bytes.decode()
    operate_dic = json.loads(operate_json)
    return operate_dic


def sk_ss(conn, dic):
    dic_json = json.dumps(dic)
    dic_bytes = dic_json.encode()
    dic_bytes_len = struct.pack('i', len(dic_bytes))
    conn.send(dic_bytes_len)
    conn.send(dic_bytes)


class Account:
    def __init__(self, usr, pwd, flag):
        self.usr = usr
        self.pwd = pwd
        self.flag = flag


def pickle_read(path):
    with open(path, mode='rb') as f2:
        ret = pickle.load(f2)
    return ret


def pickle_write(path, obj):
    with open(path, mode='wb') as f1:
        pickle.dump(obj, f1)


def pwd_md5(usr, pwd):
    usr = (lambda x: x[-1] + '不存在破解' + str(len(x)))(usr)
    ret = hashlib.md5(usr.encode('utf-8'))
    ret.update(pwd.encode('utf-8'))
    return ret.hexdigest()


def resumeup(conn, finfo_dic, finfo_send, fpath):
    f1 = open(fpath, mode='a+b')
    recv_count = 0
    recv_size = finfo_dic['filesize'] - finfo_send['filesize']
    print('客户端正在上传文件：{}'.format(finfo_dic['filename']))
    while 1:
        if (recv_size - recv_count) >= 1024:
            content = conn.recv(1024)
        else:
            content = conn.recv(recv_size - recv_count)
        if content == b'None':
            return
        f1.write(content)
        float_rate = (recv_count + finfo_send['filesize']) / finfo_dic['filesize']
        rate = round(float_rate * 100, 2)
        sys.stdout.write('\r已传输:\033[1;32m{0}%\033[0m'.format(rate))
        recv_count += len(content)
        if (recv_count + finfo_send['filesize']) >= finfo_dic['filesize']:
            print('\n客户端上传文件成功: {} {}MB'.format(finfo_dic['filename'], round(finfo_dic['filesize'] / 1024 ** 2, 2)))
            break
    f1.close()
    ret = filemd5(fpath)
    conn.send(ret.encode())


def upload(conn):
    finfo_dic = sk_sr(conn)
    if finfo_dic == 'dir':
        return
    filename = finfo_dic['filename']
    finfo_send = {'filename': filename}
    fpath = os.path.join(rootdir, finfo_dic['filename'])
    if os.path.isfile(fpath):
        finfo_send['filesize'] = os.path.getsize(fpath)
        finfo_send['filemd5'] = filemd5(fpath)
        finfo_send['operate'] = 'resumeup'
        sk_ss(conn, finfo_send)
        resumeup(conn, finfo_dic, finfo_send, fpath)
    else:
        finfo_dic['operate'] = 'upload'
        sk_ss(conn, finfo_dic)
        f1 = open(fpath, mode='wb')
        recv_count = 0
        ret = hashlib.md5()
        print('客户端正在上传文件：{}'.format(finfo_dic['filename']))
        while 1:
            if (finfo_dic['filesize'] - recv_count) >= 1024:
                content = conn.recv(1024)
            else:
                content = conn.recv((finfo_dic['filesize'] - recv_count))
            ret.update(content)
            f1.write(content)
            float_rate = recv_count / finfo_dic['filesize']
            rate = round(float_rate * 100, 2)
            sys.stdout.write('\r已传输:\033[1;32m{0}%\033[0m'.format(rate))
            recv_count += len(content)
            if recv_count >= finfo_dic['filesize']:
                print('\n客户端上传文件成功: {} {}MB'.format(finfo_dic['filename'], round(finfo_dic['filesize'] / 1024 ** 2, 2)))
                break
        f1.close()
        ret1 = ret.hexdigest()
        conn.send(ret1.encode())


def filemd5(path):
    with open(path, mode='rb') as f2:
        ret = hashlib.md5()
        while 1:
            content = f2.read(1024)
            ret.update(content)
            if not content:
                break
    ret1 = ret.hexdigest().strip()
    return ret1


def resume(conn, dic, usr_filename, fpath, fsize):
    ret5 = filemd5(fpath)
    finfo_dic = {'filename': usr_filename, 'filesize': fsize, 'filemd5': ret5}
    sk_ss(conn, finfo_dic)
    send_count = fsize - dic['filesize']
    print('客户端正在下载文件：{}'.format(finfo_dic['filename']))
    with open(fpath, mode='rb') as f2:
        ret = hashlib.md5()
        flag = 1
        while flag:
            content = f2.read(1024)
            ret.update(content)
            ret1 = ret.hexdigest()
            if ret1 == dic['md5']:
                while send_count > 0:
                    content = f2.read(1024)
                    ret.update(content)
                    conn.send(content)
                    float_rate = (fsize - send_count) / fsize
                    rate = round(float_rate * 100, 2)
                    sys.stdout.write('\r已传输:\033[1;32m{0}%\033[0m'.format(rate))
                    send_count -= 1024
                print('\n客户端下载文件成功:  {} {}MB'.format(fpath, round(finfo_dic['filesize'] / 1024 ** 2, 2)))
                ret1 = ret.hexdigest().strip()
                sk_ss(conn, ret1)
                flag = 0
            elif ret1 == ret5:
                conn.send(b'None')
                return


def download(conn):
    filelis = os.listdir(rootdir)
    sk_ss(conn, filelis)
    dic = sk_sr(conn)
    if dic == 'None':
        return
    usr_filename = filelis[dic['num'] - 1]
    fpath = os.path.join(rootdir, usr_filename)
    if os.path.isdir(fpath):
        sk_ss(conn, 'dir')
        return
    fsize = os.path.getsize(fpath)
    if dic['operate'] == 'resume':
        resume(conn, dic, usr_filename, fpath, fsize)
    elif dic['operate'] == 'download':
        finfo_dic = {'filename': usr_filename, 'filesize': fsize}
        sk_ss(conn, finfo_dic)
        send_count = fsize
        print('客户端正在下载文件：{}'.format(usr_filename))
        with open(fpath, mode='rb') as f2:
            ret = hashlib.md5()
            while send_count > 0:
                content = f2.read(1024)
                ret.update(content)
                conn.send(content)
                float_rate = (fsize - send_count) / fsize
                rate = round(float_rate * 100, 2)
                sys.stdout.write('\r已传输:\033[1;32m{0}%\033[0m'.format(rate))
                send_count -= 1024
            print('\n客户端下载文件成功:  {} {}MB'.format(fpath, round(finfo_dic['filesize'] / 1024 ** 2, 2)))
            ret1 = ret.hexdigest().strip()
            sk_ss(conn, ret1)


def login(conn):
    dic = sk_sr(conn)
    if os.path.isfile(dic['usr']) and pwd_md5(dic['usr'], dic['pwd']) == pickle_read(dic['usr']).pwd:
        obj = pickle_read(dic['usr'])
        obj.flag = True
        pickle_write(dic['usr'], obj)
        sk_ss(conn, True)
        print('{}登录成功。'.format(dic['usr']))
    else:
        sk_ss(conn, False)


def logout(conn):
    dic = sk_sr(conn)
    try:
        obj = pickle_read(dic['usr'])
        obj.flag = False
        pickle_write(dic['usr'], obj)
        print('{}退出登录。'.format(dic['usr']))
    except FileNotFoundError:
        print('账户文件不存在。')


def register(conn):
    dic = sk_sr(conn)
    usr_obj = Account(dic['usr'], pwd_md5(dic['usr'], dic['pwd']), dic['flag'])
    pickle_write(usr_obj.usr, usr_obj)
    print('客户端注册成功：{}'.format(dic['usr']))
    sk_ss(conn, 1)


def view_dir(conn):
    filelis = os.listdir(rootdir)
    sk_ss(conn, filelis)


def new_dir(conn):
    dirname = sk_sr(conn)
    fpath = os.path.join(rootdir, dirname)
    os.mkdir(fpath)


def del_function(conn):
    filelis = os.listdir(rootdir)
    sk_ss(conn, filelis)
    choice = sk_sr(conn)
    try:
        filepath = os.path.join(rootdir, filelis[choice - 1])
    except IndexError:
        sk_ss(conn, '非法操作。')
    else:
        if os.path.isdir(filepath):
            try:
                os.rmdir(filepath)
            except Exception as e:
                print(e)
                sk_ss(conn, '目录非空，删除失败：{}'.format(filelis[choice - 1]))
            else:
                sk_ss(conn, '删除成功：{}'.format(filelis[choice - 1]))
        else:
            os.remove(filepath)
            sk_ss(conn, '删除成功：{}'.format(filelis[choice - 1]))


def up_dir(conn):
    global rootdir
    if rootdir == BASE_DIR + '/root':
        sk_ss(conn, 'root')
    else:
        rootdir = os.path.dirname(rootdir)
        sk_ss(conn, os.path.basename(rootdir))


def down_dir(conn):
    global rootdir
    filelis = os.listdir(rootdir)
    sk_ss(conn, filelis)
    choice = sk_sr(conn)
    try:
        filepath = os.path.join(rootdir, filelis[choice - 1])
    except IndexError:
        sk_ss(conn, '非法操作。')
    else:
        if os.path.isdir(filepath):
            rootdir = filepath
            sk_ss(conn, '进入成功：{}'.format(filelis[choice - 1]))
        else:
            sk_ss(conn, '非法操作：{}'.format(filelis[choice - 1]))


class Myserver(socketserver.BaseRequestHandler):
    def handle(self):
        conn = self.request
        obj = sys.modules[__name__]
        try:
            choice = conn.recv(1024).decode()
            if hasattr(obj, choice):
                getattr(obj, choice)(conn)
        except ConnectionAbortedError:
            print('\n客户端意外断开。')
        except ConnectionResetError:
            print('\n客户端意外断开。')


server = socketserver.ThreadingTCPServer(('localhost', 8888), Myserver)
server.serve_forever()
