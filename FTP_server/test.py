#! usr/bin/env python
# -*- coding: utf-8 -*-
# __author: iamironman
# @file: test.py
# @time: 2019年02月10日
# @email: 875674794@qq.com

import pickle, hashlib


class Account:
    def __init__(self, usr, pwd, flag):
        self.usr = usr
        self.pwd = pwd
        self.flag = flag


def pickle_read(path):
    with open(path, mode='rb') as f2:
        ret = pickle.load(f2)
    return ret


ret1 = pickle_read('1')
print(ret1, ret1.usr, ret1.pwd, ret1.flag)


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


# ret1 = filemd5(r'C:\Users\iamironman\py3\others\project\FTP\b.mp4')
# ret2 = filemd5(r'C:\Users\iamironman\py3\others\project\FTP\新建文件夹\b.mp4')
# print(ret1, ret2)


def resume1(path):
    with open(path, mode='rb') as f2:
        ret = hashlib.md5()
        while 1:
            content = f2.read(1024)
            ret.update(content)
            ret1 = ret.hexdigest().strip()
            if ret1 == 'c9e9abdbefcd9d70132c24ce133f5806':
                print('it works, ret1:', ret1)
                break


