#!/usr/bin/env python
# coding: utf-8
__author__ = 'dfcao'
import json
import backup_config
import time
import sys
sys.path.append("..")
from config import AppConfig
from db_connect.MySQL_lightweight import MySQL_lightweight
from cmdb.cmdb_api_base import CmdbApiBase

class BackupList(CmdbApiBase):
    def mha(self):
        result = self.__call_interface__('BACKUP','backup_info/Mysql_Cluster',json_obj=None)
        return result

    def mongo(self):
        result = self.__call_interface__('BACKUP','backup_info/Mongo_Cluster',json_obj=None)
        return result

    def single_instance(self):
        result = self.__call_interface__('BACKUP','backup_info/Single',json_obj=None)
        return result

    def configure(self):
        result = self.__call_interface__('BACKUP','get_config',json_obj=None)
        return result

    def history(self,data):
        result = self.__call_interface__('BACKUP','backup_history',json_obj=data)
        return result

    def email_backup_report(self):
        result = self.__call_interface__('BACKUP','report',json_obj=None)
        return result

    def add_backup(self,data):
        result = self.__call_interface__('BACKUP','addbackup',json_obj=data)
        return result

    def del_backup(self,data):
        result = self.__call_interface__('BACKUP','delbackup',json_obj=data)
        return result

    def switch_flag(self,data):
        result = self.__call_interface__('BACKUP','switch_flag',json_obj=data)
        return result


def is_valid_date(str_in):
    '''Test if it is a valid string of date.'''
    try:
        time.strptime(str_in, "%Y-%m-%d")
        return True
    except:
        return False

class FileBackup(object):
    _file_backup_db = backup_config.FILE_BACKUP_DB
    _file_backup_servers = backup_config.FILE_BACKUP_SERVERS
    _file_backup_types = backup_config.FILE_BACKUP_TYPES
    _db = None

    def __init__(self):
        dbconfig = {'host':backup_config.BACKUP_INFO_DB_IP,
                    'port':backup_config.BACKUP_INFO_DB_PORT,
                    'user':AppConfig.MYSQL_ADMIN_USR,
                    'passwd':AppConfig.MYSQL_ADMIN_PSWORD,
                    'db':backup_config.FILE_BACKUP_DB,
                    'charset':'utf8'}
        self._db = MySQL_lightweight(dbconfig)

    def get_file_backup_info_from_db(self, st_date=time.strftime("%Y-%m-%d",time.localtime(time.time()-24*60*60)), en_date=time.strftime('%Y-%m-%d',time.localtime(time.time()))):
        if not (is_valid_date(st_date) and is_valid_date(en_date)):
            raise Exception('It is not a valid date.')
        sql = "SELECT name,file_name,file_size,bak_keep_host FROM file_backup WHERE TIME >= '%s' AND TIME < '%s' order by name" % (st_date, en_date)
        print sql
        self._db.query(sql)
        result = self._db.fetchAllArray()
        return result

    def get_file_backup_info(self, st_date=time.strftime("%Y-%m-%d",time.localtime(time.time()-24*60*60)),
                             en_date=time.strftime('%Y-%m-%d',time.localtime(time.time()))):
        if not (is_valid_date(st_date) and is_valid_date(en_date)):
            raise Exception('It is not a valid date.')

        result = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'noback': 0,
            'data_size': 0,
            'disk_use': 0,
            'bak_server': '',
            'info': {}
            }
        need_backup = backup_config.FILE_BACKUP_TYPES
        need_backup = list(need_backup)
        result['total'] = len(need_backup)
        items = self.get_file_backup_info_from_db()
        for item in items:
            if item['name'] in need_backup and item['file_size'] != 0:
                result['success'] += 1
                need_backup.remove(item['name'])
            result['data_size'] += item['file_size']
        result['failed'] = len(need_backup)
        result['info'] = items
        result['bak_servers'] = backup_config.FILE_BACKUP_SERVERS
        return result

    def get_latest_server_use(self, ip):
        if not (ip):
            raise Exception('It is not a valid ip.')
        sql = "Select IP, Path, DiskUse, AddTime from Backup_ServerUseFraction where IP='%s' Order by AddTime Desc limit 1;" % ip
        print sql
        self._db.query(sql)
        result = self._db.fetchOneRow()
        return result


if __name__ == '__main__':
    test = FileBackup()
    result = test.get_file_backup_info()
    print result

