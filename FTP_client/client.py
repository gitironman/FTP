#! usr/bin/env python
# -*- coding: utf-8 -*-
# __author: iamironman
# @file: client.py
# @time: 2019年01月23日
# @email: 875674794@qq.com


import socket
import struct
import os
import json
import sys
import hashlib
import time

flag = False
flag1 = True
name = ''


def sk_cr(sk):
    operate_bytes_len = struct.unpack('i', sk.recv(4))[0]
    operate_bytes = sk.recv(operate_bytes_len)
    operate_json = operate_bytes.decode()
    operate_dic = json.loads(operate_json)
    return operate_dic


def sk_cs(sk, dic):
    dic_json = json.dumps(dic)
    dic_bytes = dic_json.encode()
    dic_bytes_len = struct.pack('i', len(dic_bytes))
    sk.send(dic_bytes_len)
    sk.send(dic_bytes)


def wapper(func):
    def inner(*args, **kwargs):
        if flag:
            ret = func(*args, **kwargs)
            return ret
        else:
            print('请先登录或注册。')

    return inner


def resumeup(sk, fpath, fsize, finfo_recv):
    send_count = 0
    ret5 = filemd5(fpath)
    with open(fpath, mode='rb') as f2:
        ret = hashlib.md5()
        flag2 = 1
        print('准备上传文件: {} ({}MB)'.format(finfo_recv['filename'], round(fsize / 1024 ** 2, 2)))
        old_time = time.time() - 0.00001
        print('即将启动断点续传功能，请等待：')
        while flag2:
            content = f2.read(1024)
            ret.update(content)
            ret1 = ret.hexdigest()
            if ret1 == finfo_recv['filemd5']:
                while 1:
                    new_time = time.time()
                    content = f2.read(1024)
                    ret.update(content)
                    sk.send(content)
                    float_rate = (send_count + finfo_recv['filesize']) / fsize
                    rate = round(float_rate * 100, 2)
                    sys.stdout.write(
                        '\r    {}% |{}| {}MB {}MB/s'.format(rate, '█' * int(rate / 2),
                                                               round((send_count + finfo_recv['filesize']) / 1024 ** 2,
                                                                     2),
                                                               (round(send_count / 1024 ** 2 / (new_time - old_time),
                                                                      2))))
                    send_count += 1024
                    if send_count > (fsize - finfo_recv['filesize']):
                        flag2 = 0
                        break
            elif ret1 == ret5:
                print('不同文件无法进行断点续传。')
                sk.send(b'None')
                return
        ret2 = ret.hexdigest()
        print('\n正在进行文件校验：')
        ret_recv = sk.recv(1024).decode()
        if ret_recv == ret2:
            print('校验成功:{}'.format(finfo_recv['filename']))
            print('上传成功:{}'.format(finfo_recv['filename']))
        else:
            print('校验失败:{}'.format(finfo_recv['filename']))
            print('上传失败:{}'.format(finfo_recv['filename']))


@wapper
def upload(sk):
    print('欢迎进入上传文件界面。')
    fpath = os.path.abspath(input('请输入文件的绝对路径:').strip())
    if os.path.isdir(fpath):
        sk_cs(sk, 'dir')
        print('非法操作。')
        return
    fname = os.path.basename(fpath)
    fsize = os.path.getsize(fpath)
    finfo_dic = {'filename': fname, 'filesize': fsize}
    sk_cs(sk, finfo_dic)
    finfo_recv = sk_cr(sk)
    if finfo_recv['operate'] == 'resumeup':
        print('服务器存在同名文件，正在启动断点续传功能，请等待：')
        resumeup(sk, fpath, fsize, finfo_recv)
    elif finfo_recv['operate'] == 'upload':
        send_count = 0
        with open(fpath, mode='rb') as f2:
            ret = hashlib.md5()
            print('准备上传文件: {} ({}MB)'.format(finfo_dic['filename'], round(finfo_dic['filesize'] / 1024 ** 2, 2)))
            old_time = time.time() - 0.00001
            while 1:
                new_time = time.time()
                content = f2.read(1024)
                ret.update(content)
                sk.send(content)
                float_rate = send_count / fsize
                rate = round(float_rate * 100, 2)
                sys.stdout.write(
                    '\r    {}% |{}| {}MB {}MB/s'.format(rate, '█' * int(rate / 2), round(send_count / 1024 ** 2, 2),
                                                        (round(send_count / 1024 ** 2 / (new_time - old_time), 2))))
                send_count += 1024
                if send_count > finfo_dic['filesize']:
                    break
            ret1 = ret.hexdigest()
            ret_recv = sk.recv(1024).decode()
            if ret_recv == ret1:
                print('\n文件校验成功:{}'.format(finfo_dic['filename']))
                print('上传成功:{}'.format(finfo_dic['filename']))
            else:
                print('\n文件校验失败:{}'.format(finfo_dic['filename']))
                print('上传失败:{}'.format(finfo_dic['filename']))


def resume(sk):
    finfo_dic = sk_cr(sk)
    if finfo_dic == 'dir':
        print('非法操作。')
        return
    f1 = open(finfo_dic['filename'], mode='a+b')
    filesize = os.path.getsize(finfo_dic['filename'])
    recv_count = finfo_dic['filesize'] - filesize
    recv_size = recv_count - 0.00001

    print('正在下载: {} ({}MB)'.format(finfo_dic['filename'], round(finfo_dic['filesize'] / 1024 ** 2, 2)))
    old_time = time.time() - 0.00001
    while recv_count > 0:
        new_time = time.time()
        if recv_count > 1024:
            content = sk.recv(1024)
        else:
            content = sk.recv(recv_count)
        if content == b'None':
            print('不同文件无法进行断点续传。')
            return
        f1.write(content)
        float_rate = (finfo_dic['filesize'] - recv_count) / finfo_dic['filesize']
        rate = round(float_rate * 100, 2)
        sys.stdout.write(
            '\r    {}% |{}| {}MB {}MB/s'.format(rate, '█' * int(rate / 2),
                                                   round((finfo_dic['filesize'] - recv_count) / 1024 ** 2, 2),
                                                   (round((recv_size - recv_count) / 1024 ** 2 / (
                                                           new_time - old_time), 2))))
        recv_count -= len(content)

    f1.close()
    ret1_recv = sk_cr(sk)
    print('\n正在进行文件校验：')
    ret2 = filemd5(finfo_dic['filename'])
    if ret1_recv == ret2:
        print('校验成功:{}'.format(finfo_dic['filename']))
        print('下载成功:{}'.format(finfo_dic['filename']))
    else:
        print('校验失败:{}'.format(finfo_dic['filename']))
        print('下载失败:{}'.format(finfo_dic['filename']))


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


@wapper
def download(sk):
    print('欢迎进入下载文件界面。')
    filelis = sk_cr(sk)
    for index, filename in enumerate(filelis, 1):
        print(index, filename)
    num = int(input('请输入要下载文件名的序号：').strip())
    try:
        filepath = filelis[int(num) - 1]
    except IndexError:
        print('非法操作。')
        sk_cs(sk, 'None')
        return
    else:
        if os.path.isfile(filelis[int(num) - 1]):
            print('本地存在同名文件，正在启动断点续传功能，请等待：')
            dic = {'num': num, 'operate': 'resume', 'filesize': os.path.getsize(filepath), 'md5': filemd5(filepath)}
            sk_cs(sk, dic)
            resume(sk)
        else:
            dic = {'num': num, 'operate': 'download'}
            sk_cs(sk, dic)
            finfo_dic = sk_cr(sk)
            if finfo_dic == 'dir':
                print('非法操作。')
                return
            f1 = open(finfo_dic['filename'], mode='wb')
            ret = hashlib.md5()
            recv_count = finfo_dic['filesize']
            print('正在下载: {} ({}MB)'.format(finfo_dic['filename'], round(finfo_dic['filesize'] / 1024 ** 2, 2)))
            old_time = time.time() - 0.00001
            while recv_count > 0:
                new_time = time.time()
                if recv_count > 1024:
                    content = sk.recv(1024)
                else:
                    content = sk.recv(recv_count)
                ret.update(content)
                f1.write(content)
                float_rate = (finfo_dic['filesize'] - recv_count) / finfo_dic['filesize']
                rate = round(float_rate * 100, 2)
                sys.stdout.write(
                    '\r    {}% |{}| {}MB {}MB/s'.format(rate, '█' * int(rate / 2),
                                                           round((finfo_dic['filesize'] - recv_count) / 1024 ** 2, 2),
                                                           (round((finfo_dic['filesize'] - recv_count) / 1024 ** 2 / (
                                                                   new_time - old_time), 2))))
                recv_count -= len(content)
            f1.close()
            ret1 = ret.hexdigest()
            ret1_recv = sk_cr(sk)
            if ret1_recv == ret1:
                print('\n文件校验成功:{}'.format(finfo_dic['filename']))
                print('下载成功:{}'.format(finfo_dic['filename']))
            else:
                print('\n文件校验失败:{}'.format(finfo_dic['filename']))
                print('下载失败:{}'.format(finfo_dic['filename']))


def login(sk):
    print('欢迎进入登录界面。')
    usr = input('用户名:').strip()
    pwd = input('密码:').strip()
    dic = {'usr': usr, 'pwd': pwd}
    sk_cs(sk, dic)
    ret = sk_cr(sk)
    if ret:
        global flag, flag1, name
        flag = True
        flag1 = False
        name = usr
        print('登录成功。')
    else:
        print('登录失败。')


def register(sk):
    print('欢迎进入注册界面。')
    usr = input('用户名:').strip()
    pwd = input('密码:').strip()
    dic = {'usr': usr, 'pwd': pwd, 'flag': 'True'}
    sk_cs(sk, dic)
    if sk_cr(sk):
        print('注册成功。')
        global flag, flag1, name
        flag = True
        flag1 = False
        name = usr
    else:
        print('注册失败。')


def logout(sk):
    dic = {'usr': name}
    sk_cs(sk, dic)
    global flag, flag1
    flag = False
    flag1 = True
    print('已退出。')
    quit()


@wapper
def view_dir(sk):
    print('欢迎进入查看目录界面。')
    filelis = sk_cr(sk)
    for index, filename in enumerate(filelis, 1):
        print(index, filename)


@wapper
def new_dir(sk):
    print('欢迎进入新建目录界面。')
    dirname = input('请输入文件夹名称：').strip()
    sk_cs(sk, dirname)
    print('新建目录成功：{}'.format(dirname))


@wapper
def del_function(sk):
    view_dir(sk)
    print('欢迎进入删除功能界面。')
    try:
        choice = int(input('请选择序号：').strip())
    except Exception as e:
        print('格式错误：', e)
    else:
        sk_cs(sk, choice)
    print(sk_cr(sk))


@wapper
def up_dir(sk):
    recv = sk_cr(sk)
    if recv == 'root':
        print('当前目录为root，返回失败。')
    else:
        print('返回目录成功：', recv)


@wapper
def down_dir(sk):
    view_dir(sk)
    print('欢迎进入下级目录界面。')
    try:
        choice = int(input('请选择序号：').strip())
    except Exception as e:
        print('格式错误：', e)
    else:
        sk_cs(sk, choice)
    print(sk_cr(sk))


run_lis = [
    ('登录', 'login'),
    ('注册', 'register'),
    ('上传', 'upload'),
    ('下载', 'download'),
    ('查看目录', 'view_dir'),
    ('新建目录', 'new_dir'),
    ('删除功能', 'del_function'),
    ('上级目录', 'up_dir'),
    ('下级目录', 'down_dir'),
    ('退出', 'logout'),
]


def run():
    print('\n欢迎进入FTP主程序界面。')
    try:
        sk = socket.socket()
        sk.connect(('localhost', 8888))
    except ConnectionRefusedError:
        print('\n未找到指定服务器。')
        quit()
    else:
        for i, t in enumerate(run_lis, 1):
            print(i, t[0])

        choice = input('请输入服务序号：').strip()
        if not choice.isdigit():
            print('请输入数字。')
        else:
            choice = int(choice)
            if choice not in [i for i in range(1, len(run_lis) + 1)]:
                print('超出范围')
            else:
                if choice in [1, 2]:
                    if flag1:
                        sk.send(run_lis[choice - 1][1].encode())
                    else:
                        print('您已登录，请先退出。')
                        return
                elif flag:
                    sk.send(run_lis[choice - 1][1].encode())
                obj = sys.modules[__name__]
                if hasattr(obj, run_lis[choice - 1][1]):
                    try:
                        getattr(obj, run_lis[choice - 1][1])(sk)
                    except ConnectionAbortedError:
                        print('\n服务端意外断开。')
                    except ConnectionResetError:
                        print('\n服务端意外断开。')


if __name__ == '__main__':
    while 1:
        run()
