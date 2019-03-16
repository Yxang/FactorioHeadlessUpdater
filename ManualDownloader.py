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
        logging.debug('Dealing with paths')
        pslash = file_name.rfind('/')
        file_name_len = len(file_name[pslash:])
        self.start_time = time.time()
        file_path = os.path.join(os.getcwd(), file_name)
        file_dir = file_path[:-file_name_len]
        if not os.path.exists(file_dir):
            os.mkdir(file_dir)
        logging.debug('downloading')
        if not os.path.isfile(file_path) or download == 'overwrite':
            url = 'https://www.factorio.com/get-download/%s/headless/linux64' % version

            try:
                logging.debug('Touching url')
                request.urlopen(url)
            except urllib.error.HTTPError:
                logging.info('HTTP Error, might input a wrong version')
                return False

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
        logging.info('\nDownload finished')
        return True


class Decompressor(object):

    def __init__(self, tar_dir='./tmp/factorio.tar'):
        self.tar_dir = tar_dir

    def un_xz(self, input_xzfile='./tmp/factorio.tar.xz', output_file=None):
        logging.debug("Start decompressing xz file")
        if not output_file:
            output_file = self.tar_dir
        with lzma.open(input_xzfile, 'rb') as input:
            with open(output_file, 'wb') as output:
                shutil.copyfileobj(input, output)
        logging.debug('xz decompression finished')

    def un_tar(self, file_name=None, output_dir=None):
        logging.debug('Start decompressing tar file')
        if not file_name:
            file_name = self.tar_dir
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
        logging.debug('tar decompression finished')

    def decompress(self, input_xzfile='factorio.tar.xz', output_dir='factorio/'):
        logging.info('Decompressing...')
        self.un_xz(input_xzfile=input_xzfile)
        self.un_tar('./tmp/factorio.tar', output_dir)
        return True


class Transferer(object):

    def __init__(self, tmp_dir):
        self.tmp_dir = tmp_dir
        self.has_backup = False
        self.backup_dir = os.path.join(self.tmp_dir, 'data_backup')

    def __backup_data(self, targetDir):
        logging.debug('Start backup')
        backup_dir = self.backup_dir
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        shutil.move(os.path.join(targetDir, './data/base'),
                    os.path.join(backup_dir, './base'))
        shutil.move(os.path.join(targetDir, './data/core'),
                    os.path.join(backup_dir, './core'))
        logging.debug('Backup finished')
        return True

    def __recover_data(self, targetDir):
        logging.debug('Start recovery')
        self.__mycopy(os.path.join(self.backup_dir, './base'),
                    os.path.join(targetDir, './data/base'))
        self.__mycopy(os.path.join(self.backup_dir, './core'),
                    os.path.join(targetDir, './data/core'))
        logging.debug('Recovery finished')
        return True

    def __rm_data(self):
        logging.debug('Start removing backups')
        rmrf(self.backup_dir)
        logging.debug('Removal finished')
        return True


    def __mycopy(self, sourceDir, targetDir):
        # logging.debug('Start copying files')
        # logging.debug(sourceDir)
        # logging.debug(u"dealing with %s" % sourceDir)
        for f in os.listdir(sourceDir):
            sourceF = os.path.join(sourceDir, f)
            targetF = os.path.join(targetDir, f)

            if not os.path.exists(targetDir):
                os.makedirs(targetDir)

            if os.path.isdir(sourceF):
                self.__mycopy(sourceF, targetF)
            else:
                if not os.path.exists(targetF) or (
                        os.path.exists(targetF) and (os.path.getsize(targetF) != os.path.getsize(sourceF))):
                    open(targetF, "wb").write(open(sourceF, "rb").read())
                    # logging.debug(u"%s Copy complete" % targetF)
        # logging.debug('Copy finished')
        return True

    def transfer(self, sourceDir=r'factorio_files/factorio', targetDir=r'factorio'):
        logging.info('Transfering...')
        self.__backup_data(targetDir=targetDir)
        try:
            self.__mycopy(sourceDir, targetDir)
        except:
            logging.info('Copy fails, recovering...')
            self.__recover_data(targetDir=targetDir)
        else:
            logging.info('Copy success')
            self.__rm_data()
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
    os.rmdir(dir)


def ret_arg(obj, type):
    return obj if isinstance(obj, type) else obj[0]


if __name__ == '__main__':

    ###########################################
    # Defining parser
    ###########################################
    parser = argparse.ArgumentParser(description='Upgrade factorio')
    parser.add_argument('--tar-version', '-T', required=True, type=str, nargs=1, dest='version',
                        help='Target version of factorio')
    parser.add_argument('--tar-dir', '-D', default='factorio', type=str, nargs=1, dest='tar_dir',
                        help='target directory for factorio')
    parser.add_argument('--tmp-dir', default='./tmp/', type=str, nargs=1, dest='tmp_dir',
                        help='Temporary directory\' s name, all downloaded and decompressed file will be stored in it')
    parser.add_argument('--tarxz-name', default='factorio.tar.xz', type=str, nargs=1, dest='tarxz_name',
                        help='Temporary tar.xz file\' s name, default is factorio.tar.xz')
    parser.add_argument('--unxz-dir', default='factorio_files/', type=str, nargs=1, dest='untarxz_dir',
                        help='The name for the temp decompressing directory, default is factorio_files/ inside TMP_DIR')
    parser.add_argument('--download', default='abort', type=str, nargs=1, dest='download',
                        choices=['overwrite', 'skip', 'abort'],
                        help='Configuration to downloading stage')
    parser.add_argument('--cleaning', default=1, type=int, nargs=1, dest='cleaning',
                        help='Whether to clean the temp files')

    ###########################################
    # Dealing with inputs
    ###########################################

    # grep them
    args = parser.parse_args()
    logging.debug(args)
    version = ret_arg(args.version, str)
    tar_dir = ret_arg(args.tar_dir, str)
    tmp_dir = ret_arg(args.tmp_dir, str)
    tarxz_name = ret_arg(args.tarxz_name, str)
    untarxz_dir = ret_arg(args.untarxz_dir, str)
    unxz_name = 'factorio.tar'
    download = ret_arg(args.download, str)
    cleaning = bool(ret_arg(args.cleaning, int))

    # join the dirs
    tarxz_name = os.path.join(tmp_dir, tarxz_name)
    untarxz_dir = os.path.join(tmp_dir, untarxz_dir)
    unxz_name = os.path.join(tmp_dir, unxz_name)

    # debug: print them
    logging.debug('version %s' % version)
    logging.debug('tar_dir %s' % tar_dir)
    logging.debug('tmp_dir %s' % tmp_dir)
    logging.debug('tarxz_name %s' % tarxz_name)
    logging.debug('untarxz_dir %s' % untarxz_dir)
    logging.debug('unxz_name %s' % unxz_name)
    logging.debug('download %s' % download)
    logging.debug('cleaning %s' % cleaning)

    success = True

    if success and download != 'skip':
        success = Downloader().download(version=version, file_name=tarxz_name, download=download)
    elif download == 'skip':
        logging.info('Skip downloading')
    if success:
        success = Decompressor().decompress(input_xzfile=tarxz_name, output_dir=untarxz_dir)
    if success:
        Killer.kill()
    if success:
        success = Transferer(tmp_dir=tmp_dir).transfer(sourceDir=untarxz_dir + './factorio', targetDir=tar_dir)
    if success:
        logging.info('Upgrade success')
        if cleaning:
            logging.info('Cleaning...')
            rmrf(tmp_dir)
        else:
            logging.info('Not cleaning')

            logging.info('Finished')

# TODO: 抓中断，删文件