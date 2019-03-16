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
import wget

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.DEBUG,
    stream=sys.stdout)


class Downloader(object):

    def __init__(self):
        self.start_time = time.time()

    def download(self, version, file_name='factorio.tar.xz', download='abort'):
        if download == 'skip':
            logging.info('Skip downloading')
            return True
        logging.info('Downloading...')
        pslash = file_name.rfind('/')
        file_name_len = len(file_name[pslash:])
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

            try:
                os.remove(file_path)
            except FileNotFoundError:
                pass

            logging.info('Downloading factorio version %s from %s' %
                         (version, url))
            try:
                wget.download(url, out=file_name)
            except urllib.error.HTTPError:
                logging.info('Download failed')
                return False
        elif download == 'abort':
            logging.info('File exists')
            return False
        else:
            raise RuntimeError('not abort and overwrite')
        logging.info('Download finished')
        return True


class Decompressor(object):

    @staticmethod
    def un_xz(input_xzfile='factorio.tar.xz', output_file='./tmp/factorio.tar'):
        with lzma.open(input_xzfile, 'rb') as input:
            with open(output_file, 'wb') as output:
                shutil.copyfileobj(input, output)

    @staticmethod
    def un_tar(file_name='./tmp/factorio.tar', output_dir=None):
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
        Decompressor.un_tar('./tmp/factorio.tar', output_dir)
        return True


class Copyer(object):

    @staticmethod
    def __rm_data_core(targetDir):
        # TODO: remvoe 'source' and 'core' dir
        pass

    @staticmethod
    def __mycopy(sourceDir, targetDir):
        logging.debug(sourceDir)
        logging.debug(u"dealing with %s" % sourceDir)
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
            try:
                if processName.lower() in p.name().lower():
                    logging.info('killing pid %s, name %s' % (pid, p.name()))
                    os.system('kill %s' % pid)
            except:
                pass

        for pid in pids:
            p = psutil.Process(pid)
            try:
                if processName.lower() in p.name().lower():
                    return False
            except:
                pass
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


def ret_arg(obj, type):
    return obj if isinstance(obj, type) else obj[0]


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Upgrade factorio')
    parser.add_argument('--tar-version', '-T', required=True, type=str, nargs=1, dest='version',
                        help='Target version of factorio')
    parser.add_argument('--tar-dir', '-D', default='factorio', type=str, nargs=1, dest='tar_dir',
                        help='target directory for factorio')
    parser.add_argument('--tarxz-name', default='./tmp/factorio.tar.xz', type=str, nargs=1, dest='tarxz_name',
                        help='Temporary tar.xz file\' s name, default is factorio.tar.xz')
    parser.add_argument('--dic-name', default='./tmp/factorio_files/', type=str, nargs=1, dest='dir_name',
                        help='Temporary directory\' s name, default is factorio_files/')
    parser.add_argument('--download', default='abort', type=str, nargs=1, dest='download',
                        choices=['overwrite', 'skip', 'abort'],
                        help='Configuration to downloading stage')
    parser.add_argument('--cleaning', default=1, type=int, nargs=1, dest='cleaning',
                        help='Whether to clean the temp files')

    args = parser.parse_args()
    version = ret_arg(args.version[0], str)
    tar_dir = ret_arg(args.tar_dir[0], str)
    tarxz_name = ret_arg(args.tarxz_name, str)
    dir_name = ret_arg(args.dir_name, str)
    download = ret_arg(args.download, str)
    cleaning = bool(ret_arg(args.cleaning, int))

    logging.debug(args)

    success = True

    if success and download != 'skip':
        success = Downloader().download(version=version, file_name=tarxz_name, download=download)
    elif download == 'skip':
        logging.info('Skip downloading')
    if success:
        success = Decompressor.decompress(input_xzfile=tarxz_name, output_dir=dir_name)
    if success:
        Killer.kill()
    if success:
        success = Copyer.copy(sourceDir=dir_name + 'factorio', targetDir=tar_dir)
    if success:
        logging.info('Upgrade success')
        if cleaning:
            logging.info('Cleaning...')
            try:
                os.remove(tarxz_name)
            except:
                pass
            rmrf(dir_name)
        else:
            logging.info('Not cleaning')

            logging.info('Finished')

# TODO: 抓中断，删文件
# TODO: 改成wget
# TODO: 删core和base，备份
