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
from cmdb.instance import InstanceList
from cmdb.backup import BackupList

class DBAPortalRedis(object):
    _redis = None
    
    def __init__(self):
        self._redis = redis.StrictRedis(host=redispy_config.REDIS_IP, port=redispy_config.REDIS_PORT, encoding='utf-8')
        self._expire_server_all = 120
        self._expire_server_available = 120
        self._expire_server_total_count = 120
        self._expire_instance_all = 120
        self._expire_instance_total_count = 120

    def reset_dba_portal_redis(self):
        '''
        Reset redis data.
        '''
        print '%s: -- redis: reset backup data...' % time.strftime('%Y-%m-%d %H-%M-%S')        
        backup_list = BackupList()
        # print '%s: add backup mha into redis...' % time.strftime('%Y-%m-%d %H-%M-%S')
        # backup_mha = backup_list.mha()
        # backup_mha = json.dumps(backup_mha,ensure_ascii=False)
        # self._redis.set('backup_mha', backup_mha)
        # time.sleep(3)

        # print '%s: add backup mongo into redis...' % time.strftime('%Y-%m-%d %H-%M-%S')
        # backup_mongo = backup_list.mongo()
        # backup_mongo = json.dumps(backup_mongo,ensure_ascii=False)
        # self._redis.set('backup_mongo', backup_mongo)
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


        print '%s: -- redis: reset server data...' % time.strftime('%Y-%m-%d %H-%M-%S')        
        server_list = ServerList()
        server_all = server_list.list_all()
        self.set_json_with_expire('server_all', server_all, self._expire_server_all)
        time.sleep(3)
        server_available = server_list.list_available()
        self.set_json_with_expire('server_available', server_available, self._expire_server_available)
        time.sleep(3)
        # server_total_count = server_list.get_total_count()
        # self.set_json_with_expire('server_total_count', server_total_count, self._expire_server_total_count)
        # time.sleep(3)

        print '%s: -- redis: reset instance data...' % time.strftime('%Y-%m-%d %H-%M-%S')        
        instance_list = InstanceList()
        instance_all = instance_list.list_all()
        self.set_json_with_expire('instance_all', instance_all, self._expire_instance_all)
        time.sleep(3)
        instance_total_count = instance_list.get_total_count()
        self.set_json_with_expire('instance_total_count', instance_total_count, self._expire_instance_total_count)
        time.sleep(3)

        return True

    def set_json_with_expire(self, key, value, expire=60):
        '''
        Description: reset key to json value with expire time.
        Parameters format
        ### key: string
        ### value: json format data
        ### expire: time to live $expire seconds
        Example
        ### set_with_expire('server', {'test':1}, 10)
        ### server is "{\"test\": 1}}", and will live 10s
        '''
        if not ((type(key) is str or type(key) is unicode) and
                (type(expire) is int or type(expire) is float)):
            print "wrong parameters."
            print "set_with_expire('server', {'test':1}, 10)"
            return False

        print '%s: ---- redis: set %s' % (time.strftime('%Y-%m-%d %H-%M-%S'), key)
        try:
            value = json.dumps(value,ensure_ascii=False)
            pipeline = self._redis.pipeline()
            pipeline.set(key, value)
            pipeline.expire(key, expire)
            pipeline.execute()
            return True
        except Exception, e: 
            msg = "%s: %s" % (type(e).__name__, e.message) 
            print msg
            return False


    def get_backup_mha(self):
        backup_mha = json.loads(self._redis.get('backup_mha'))
        return backup_mha

    def set_backup_mha(self, data):
        print '%s: ---- redis: set backup_mha' % time.strftime('%Y-%m-%d %H-%M-%S')
        backup_mha = json.dumps(data,ensure_ascii=False)
        self._redis.set('backup_mha', backup_mha)
        return backup_mha

    def get_backup_mongo(self):
        backup_mongo = json.loads(self._redis.get('backup_mongo'))
        return backup_mongo

    def set_backup_mongo(self, data):
        print '%s: ---- redis: set backup_mongo' % time.strftime('%Y-%m-%d %H-%M-%S')
        backup_mongo = json.dumps(data,ensure_ascii=False)
        self._redis.set('backup_mongo', backup_mongo)
        return backup_mongo
    
    def get_backup_single_instance(self):
        backup_single_instance = json.loads(self._redis.get('backup_single_instance'))
        return backup_single_instance

    def set_backup_single_instance(self, data):
        print '%s: ---- redis: set backup_single_instance' % time.strftime('%Y-%m-%d %H-%M-%S')
        backup_single_instance = json.dumps(data,ensure_ascii=False)
        self._redis.set('backup_single_instance', backup_single_instance)
        return backup_single_instance

    def get_backup_configure(self):
        backup_configure = json.loads(self._redis.get('backup_configure'))
        return backup_configure

    def set_backup_configure(self, data):
        print '%s: ---- redis: set backup_configure' % time.strftime('%Y-%m-%d %H-%M-%S')
        backup_configure = json.dumps(data,ensure_ascii=False)
        self._redis.set('backup_configure', backup_configure)
        return backup_configure

    def get_backup_history_bu(self):
        backup_history_bu = json.loads(self._redis.get('backup_history_bu'))
        return backup_history_bu

    def set_backup_history_bu(self, data):
        print '%s: ---- redis: set backup_history_bu' % time.strftime('%Y-%m-%d %H-%M-%S')
        backup_history_bu = json.dumps(data,ensure_ascii=False)
        self._redis.set('backup_history_bu', backup_history_bu)
        return backup_history_bu

    def get_backup_email_backup_report(self):
        backup_email_backup_report = json.loads(self._redis.get('backup_email_backup_report'))
        return backup_email_backup_report

    def set_backup_email_backup_report(self, data):
        print '%s: ---- redis: set backup_email_backup_report' % time.strftime('%Y-%m-%d %H-%M-%S')
        backup_email_backup_report = json.dumps(data,ensure_ascii=False)
        pipeline = self._redis.pipeline()
        pipeline.set('backup_email_backup_report', backup_email_backup_report)
        pipeline.expire('backup_email_backup_report', 3600*6)
        pipeline.execute()
        return backup_email_backup_report


    def get_server_all(self):
        server_all = json.loads(self._redis.get('server_all'))
        return server_all

    def get_server_available(self):
        server_available = json.loads(self._redis.get('server_available'))
        return server_available

    def get_server_total_count(self):
        server_total_count = json.loads(self._redis.get('server_total_count'))
        return server_total_count

    def get_product_bu(self, key):
        product_bu = json.loads(self._redis.get(key))
        return product_bu

    def get_instance_total_count(self):
        instance_total_count = json.loads(self._redis.get('instance_total_count'))
        return instance_total_count

    def get_instance_all(self):
        instance_all = json.loads(self._redis.get('instance_all'))
        return instance_all


    def get_monitor_all(self, key):
        monitor_all = json.loads(self._redis.get(key))
        return monitor_all


if __name__ == '__main__':
    test = DBAPortalRedis()
    test.reset_dba_portal_redis()
