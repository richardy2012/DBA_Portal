#!/usr/bin/env python
# coding: utf-8

import json
import redispy_config
import time
import sys
import redis
sys.path.append("..")
from config import AppConfig

from cmdb.server import ServerList
from cmdb.instance import InstList
from cmdb.backup import BackupList

class DBAPortalRedis(object):
    _redis = None
    
    def __init__(self):
        self._redis = redis.StrictRedis(host=redispy_config.REDIS_IP, port=redispy_config.REDIS_PORT, encoding='utf-8')

    def init_dba_portal_redis(self):
        #self._redis.flushall()

        print '%s: add backup mha into redis...' % time.strftime('%Y-%m-%d %H-%M-%S')
        backup_list = BackupList()
        # backup_mha = backup_list.mha()
        # backup_mha = json.dumps(backup_mha,ensure_ascii=False)
        # self._redis.set('backup_mha', backup_mha)
        # time.sleep(3)
        # print '%s: add backup single-instance into redis...' % time.strftime('%Y-%m-%d %H-%M-%S')
        # backup_single_instance = backup_list.single_instance()
        # backup_single_instance = json.dumps(backup_single_instance,ensure_ascii=False)
        # self._redis.set('backup_single_instance', backup_single_instance)
        # time.sleep(3)
        # print '%s: add backup configure into redis...' % time.strftime('%Y-%m-%d %H-%M-%S')
        # backup_configure = backup_list.configure()
        # backup_configure = json.dumps(backup_configure,ensure_ascii=False)
        # self._redis.set('backup_configure', backup_configure)
        # time.sleep(3)
        # print '%s: add backup email_backup_report into redis...' % time.strftime('%Y-%m-%d %H-%M-%S')
        # backup_email_backup_report = backup_list.email_backup_report()
        # backup_email_backup_report = json.dumps(backup_email_backup_report,ensure_ascii=False)
        # self._redis.set('backup_email_backup_report', backup_email_backup_report)
        # time.sleep(3)


        print '%s: add server data into redis...' % time.strftime('%Y-%m-%d %H-%M-%S')
        server_list = ServerList()
        server_all = server_list.list_all()
        server_all = json.dumps(server_all,ensure_ascii=False)
        self._redis.set('server_all', server_all)
        time.sleep(3)
        server_available = server_list.list_available()
        server_available = json.dumps(server_available,ensure_ascii=False)
        self._redis.set('server_available', server_available)
        time.sleep(3)
        server_total_count = server_list.get_total_count()
        server_total_count = json.dumps(server_total_count,ensure_ascii=False)
        self._redis.set('server_total_count', server_total_count)
        time.sleep(3)

        print '%s: add instance data into redis...' % time.strftime('%Y-%m-%d %H-%M-%S')
        instance_list = InstList()
        instance_total_count = instance_list.get_total_count()
        instance_total_count = json.dumps(instance_total_count,ensure_ascii=False)
        self._redis.set('instance_total_count', instance_total_count)
        time.sleep(3)

        return True

    def get_backup_mha(self):
        backup_mha = json.loads(self._redis.get('backup_mha'))
        return backup_mha

    def set_backup_mha(self, data):
        print '%s: redis set backup_mha' % time.strftime('%Y-%m-%d %H-%M-%S')
        backup_mha = json.dumps(data,ensure_ascii=False)
        self._redis.set('backup_mha', backup_mha)
        return backup_mha
    
    def get_backup_single_instance(self):
        backup_single_instance = json.loads(self._redis.get('backup_single_instance'))
        return backup_single_instance

    def set_backup_single_instance(self, data):
        print '%s: redis set backup_single_instance' % time.strftime('%Y-%m-%d %H-%M-%S')
        backup_single_instance = json.dumps(data,ensure_ascii=False)
        self._redis.set('backup_single_instance', backup_single_instance)
        return backup_single_instance

    def get_backup_configure(self):
        backup_configure = json.loads(self._redis.get('backup_configure'))
        return backup_configure

    def set_backup_configure(self, data):
        print '%s: redis set backup_configure' % time.strftime('%Y-%m-%d %H-%M-%S')
        backup_configure = json.dumps(data,ensure_ascii=False)
        self._redis.set('backup_configure', backup_configure)
        return backup_configure

    def get_backup_email_backup_report(self):
        backup_email_backup_report = json.loads(self._redis.get('backup_email_backup_report'))
        return backup_email_backup_report

    def set_backup_email_backup_report(self, data):
        print '%s: redis set backup_email_backup_report' % time.strftime('%Y-%m-%d %H-%M-%S')
        backup_email_backup_report = json.dumps(data,ensure_ascii=False)
        self._redis.set('backup_email_backup_report', backup_email_backup_report)
        return backup_email_backup_report


    def get_server_all(self):
        server_all = json.loads(self._redis.get('server_all'))
        return server_all

    def set_server_all(self, data):
        print '%s: redis set server_all' % time.strftime('%Y-%m-%d %H-%M-%S')
        server_all = json.dumps(data,ensure_ascii=False)
        self._redis.set('server_all', server_all)
        return server_all

    def get_server_available(self):
        server_available = json.loads(self._redis.get('server_available'))
        return server_available

    def set_server_available(self, data):
        print '%s: redis set server_available' % time.strftime('%Y-%m-%d %H-%M-%S')
        server_available = json.dumps(data,ensure_ascii=False)
        self._redis.set('server_available', server_available)
        return server_available

    def get_server_total_count(self):
        server_total_count = json.loads(self._redis.get('server_total_count'))
        return server_total_count

    def set_server_total_count(self, data):
        print '%s: redis set server_total_count' % time.strftime('%Y-%m-%d %H-%M-%S')
        server_total_count = json.dumps(data,ensure_ascii=False)
        self._redis.set('server_total_count', server_total_count)
        return server_total_count


    def get_instance_total_count(self):
        instance_total_count = json.loads(self._redis.get('instance_total_count'))
        return instance_total_count

    def set_instance_total_count(self, data):
        print '%s: redis set instance_total_count' % time.strftime('%Y-%m-%d %H-%M-%S')
        instance_total_count = json.dumps(data,ensure_ascii=False)
        self._redis.set('instance_total_count', instance_total_count)
        return instance_total_count



if __name__ == '__main__':
    test = DBAPortalRedis()
    test.init_dba_portal_redis()
