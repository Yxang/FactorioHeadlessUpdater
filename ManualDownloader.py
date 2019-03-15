#! /usr/bin/python3
# -*- coding:utf-8 -*-
import sys
import time
import os
import logging
import urllib
from urllib import request
import lzma
import shutil
import tarfile
import argparse
import psutil

'''
 urllib.urlretrieve 的回调函数：
def callbackfunc(blocknum, blocksize, totalsize):
    @blocknum:  已经下载的数据块
    @blocksize: 数据块的大小
    @totalsize: 远程文件的大小
'''

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.INFO,
    stream=sys.stdout)


class Downloader(object):

    def __init__(self):
        self.start_time = time.time()

    def schedule(self, blocknum, blocksize, totalsize):
        speed = (blocknum * blocksize) / (time.time() - self.start_time)
        # speed_str = " Speed: %.2f" % speed
        speed_str = " Speed: %s" % self.format_size(speed)
        recv_size = blocknum * blocksize

        # 设置下载进度条
        f = sys.stdout
        pervent = recv_size / totalsize
        percent_str = "%.2f%%" % (pervent * 100)
        n = round(pervent * 50)
        s = ('#' * n).ljust(50, '-')
        f.write(percent_str.ljust(8, ' ') + '[' + s + ']' + speed_str)
        f.flush()
        time.sleep(0.1)
        f.write('\r')

    def format_size(self, bytes):
        # 字节bytes转化K\M\G
        try:
            bytes = float(bytes)
            kb = bytes / 1024
        except:
            print("传入的字节格式不对")
            return "Error"
        if kb >= 1024:
            M = kb / 1024
            if M >= 1024:
                G = M / 1024
                return "%.3fG" % (G)
            else:
                return "%.3fM" % (M)
        else:
            return "%.3fK" % (kb)

    def download(self, version, file_name='factorio.tar.xz', download='abort'):
        logging.info('Downloading...')
        file_name_len = len(file_name)
        self.start_time = time.time()
        file_path = os.path.join(os.getcwd(), file_name)
        file_dir = file_path[:-file_name_len]
        if not os.path.exists(file_dir):
            os.mkdir(file_dir)
        if not os.path.isfile(file_path) or download == 'overwrite':
            url = 'https://www.factorio.com/get-download/%s/headless/linux64' % version
            try:
                request.urlopen(url)
            except urllib.error.HTTPError:
                logging.info('HTTP Error, might input a wrong version')
                return False
            logging.info('Downloading factorio version %s from %s' %
                         (version, url))
            try:
                request.urlretrieve(url, file_path, self.schedule)
            except urllib.error.HTTPError:
                logging.info('Download failed')
                return False
        elif download == 'abort':
            logging.info('File exists')
            return False
        print()
        return True


class Decompressor(object):

    @staticmethod
    def un_xz(input_xzfile='factorio.tar.xz', output_file='factorio.tar'):
        with lzma.open(input_xzfile, 'rb') as input:
            with open(output_file, 'wb') as output:
                shutil.copyfileobj(input, output)

    @staticmethod
    def un_tar(file_name='factorio.tar', output_dir=None):
        tar = tarfile.open(file_name)
        names = tar.getnames()
        if not output_dir:
            output_dir = file_name + "_files"
        if os.path.isdir(output_dir):
            pass
        else:
            os.mkdir(output_dir)
        for name in names:
            tar.extract(name, output_dir)
        tar.close()
        os.remove(file_name)

    @staticmethod
    def decompress(input_xzfile='factorio.tar.xz', output_dir='factorio/'):
        logging.info('Decompressing...')
        Decompressor.un_xz(input_xzfile=input_xzfile)
        Decompressor.un_tar('factorio.tar', output_dir)
        return True


class Copyer(object):

    @staticmethod
    def __mycopy(sourceDir, targetDir):
        logging.debug(sourceDir)
        logging.debug(u"当前处理文件夹%s" % sourceDir)
        for f in os.listdir(sourceDir):
            sourceF = os.path.join(sourceDir, f)
            targetF = os.path.join(targetDir, f)

            if not os.path.exists(targetDir):
                os.makedirs(targetDir)

            if os.path.isdir(sourceF):
                Copyer.__mycopy(sourceF, targetF)
            else:
                if not os.path.exists(targetF) or (
                        os.path.exists(targetF) and (os.path.getsize(targetF) != os.path.getsize(sourceF))):
                    open(targetF, "wb").write(open(sourceF, "rb").read())
                    logging.debug(u"%s Copy complete" % targetF)


    @staticmethod
    def copy(sourceDir=r'factorio.tar_files/factorio', targetDir=r'factorio'):
        logging.info('Copying...')
        Copyer.__mycopy(sourceDir, targetDir)
        return True


class Killer(object):

    @staticmethod
    def kill(processName='factorio'):
        pids = psutil.pids()
        for pid in pids:
            p = psutil.Process(pid)
            if processName.lower() in p.name().lower():
                logging.info('killing pid %s, name %s' % (pid, p.name()))
                os.system('kill %s' % pid)

        for pid in pids:
            p = psutil.Process(pid)
            if processName.lower() in p.name().lower():
                return False
        return True


def rmrf(dir):
    for root, dirs, files in os.walk(dir, topdown=False):
        for name in files:
            try:
                os.remove(os.path.join(root, name))
            except:
                pass
        for name in dirs:
            try:
                os.rmdir(os.path.join(root, name))
            except:
                pass
    try:
        os.rmdir(dir_name)
    except:
        pass


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Upgrade factorio')
    parser.add_argument('--target-version', '-T', required=True, type=str, nargs=1, dest='version',
                        help='Target version of factorio')
    parser.add_argument('--tarxz-name', default='factorio.tar.xz', type=str, nargs=1, dest='tarxz_name',
                        help='Temporary tar.xz file\' s name, default is factorio.tar.xz')
    parser.add_argument('--dic-name', default='factorio_files/', type=str, nargs=1, dest='dir_name',
                        help='Temporary directory\' s name, default is factorio_files/')
    parser.add_argument('--del-tmp', '-d', default=True, type=bool, nargs=1, dest='del_tmp',
                        help='Whether to delete the temporary files, default is True')
    parser.add_argument('--download', default='abort', type=str, nargs=1, dest='download',
                        choices=['overwrite', 'skip', 'abort'],
                        help='How to deal with existing tar.xz file')

    args = parser.parse_args()
    # dont know why [0] here
    version = args.version[0]
    tarxz_name = args.tarxz_name
    dir_name = args.dir_name
    del_tmp = args.del_tmp
    download = args.download

    success = True

    if success and download != 'skip':
        success = Downloader().download(version=version, file_name=tarxz_name, download=download)
    if success:
        success = Decompressor.decompress(input_xzfile=tarxz_name, output_dir=dir_name)
    if success:
        Killer.kill()
    if success:
        success = Copyer.copy(sourceDir=dir_name + 'factorio')
    if success:
        logging.info('Upgrade success')
        if del_tmp:
            logging.info('Cleaning...')
            try:
                os.remove(tarxz_name)
            except:
                pass
            rmrf(dir_name)

            logging.info('Finished')

# TODO: 原来factorio的地址
# TODO: 抓中断，删文件
# TODO: 下载的文件都放进一个temp里
