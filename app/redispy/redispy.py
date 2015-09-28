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
from backup.backup import BackupList

class RTMRedis(object):
    _redis = None

    def __init__(self):
        self._redis = redis.StrictRedis(host=redispy_config.RTMREDIS_IP, port=redispy_config.RTMREDIS_PORT, encoding='utf-8')



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
        print '%s: -- redis: reset server data...' % time.strftime('%Y-%m-%d %H-%M-%S')
        server_list = ServerList()
        server_all = server_list.list_all()
        self.set_json_with_expire('server_all', server_all, self._expire_server_all)
        time.sleep(3)
        # server_available = server_list.list_available()
        # self.set_json_with_expire('server_available', server_available, self._expire_server_available)
        # time.sleep(3)
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

    def get_json(self, key):
        result = self._redis.get(key)
        if result: result = json.loads(result)
        return result


if __name__ == '__main__':
    test = DBAPortalRedis()
    test.reset_dba_portal_redis()
