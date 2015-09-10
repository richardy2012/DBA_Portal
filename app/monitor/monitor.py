#-*- coding: utf-8 -*-
__author__ = 'caodanfeng'
import urllib2
import urllib
import json,requests,time
import sys
import monitor_config
sys.path.append("..")
from redispy.redispy import DBAPortalRedis
#from cmdb_api_base import CmdbApiBase

class Monitor():
    _monitor_ip_lists = ["10.1.125.16","10.1.125.15","10.1.125.14","10.1.125.11","10.1.125.23","10.1.6.40","10.1.6.41","10.1.6.114","10.1.6.115","10.1.110.62","10.1.110.64","10.1.110.145","10.1.101.136","10.1.101.158","10.1.101.130","10.1.125.12","10.1.125.13","10.1.125.192","10.1.101.143","10.1.101.15","10.1.101.36","10.1.101.149","10.1.101.98","10.1.101.174","10.1.101.161","10.1.6.226","10.1.6.225","10.1.6.230","10.3.10.55","10.3.10.66","10.3.10.23","10.3.10.53","10.1.101.131","10.1.101.132","10.1.101.120","10.1.101.92","10.3.10.68","10.3.10.69","10.1.110.108","10.1.110.110","10.1.1.135","10.1.1.205"]
    _monitor_ip_dict = {
        "10.1.125.16":"pctorder","10.1.125.15":"pctorder","10.1.125.14":"pctorder",
        "10.1.125.11":"paybase","10.1.125.23":"paybase",
        "10.1.6.40":"tpfun","10.1.6.41":"tpfun",
        "10.1.6.114":"tgtp","10.1.6.115":"tgtp",
        "10.1.110.62":"pctaccount","10.1.110.64":"pctaccount","10.1.110.145":"pctaccount",
        "10.1.101.136":"pctchannel","10.1.101.158":"pctchannel","10.1.101.130":"pctchannel",
        "10.1.125.12":"pctengine","10.1.125.13":"pctengine","10.1.125.192":"pctengine",
        "10.1.101.143":"dianpingpct","10.1.101.15":"dianpingpct","10.1.101.36":"dianpingpct",
        "10.1.101.149":"deal","10.1.101.98":"deal","10.1.101.174":"deal","10.1.101.161":"deal",
        "10.1.6.226":"tpd_deal","10.1.6.225":"tpd_deal","10.1.6.230":"tpd_deal",
        "10.3.10.55":"tgstock","10.3.10.66":"tgstock",
        "10.3.10.23":"bonus","10.3.10.53":"bonus",
        "10.1.101.131":"tgreceipt","10.1.101.132":"tgreceipt","10.1.101.120":"tgreceipt","10.1.101.92":"tgreceipt",
        "10.3.10.68":"pctdiscount","10.3.10.69":"pctdiscount",
        "10.1.110.108":"mopay","10.1.110.110":"mopay",
        "10.1.1.135":"tgreceiptstock","10.1.1.205":"tgreceiptstock"
        }
    def __init__(self):
        pass
#print monitor_config.MONITOR_IPS
        #self._monitor_ip_lists = self.parse_ips(monitor_config.MONITOR_IPS)
        
    def parse_ips(self, ip_str):
        ip_lists = []
        if not ip_str:
            return ip_lists
        infoes = ip_str.split(',')
        for info in infoes:
            ip_lists.append(info)
        return ip_lists


    def list_all(self, data=None):
        if not (data and data['product']):
            print 'monitor -- parameters error: do not have product'
            return False
        url = 'http://cat.dp/cat/r/database?op=view&forceDownload=json'
        for key in data:
            url += ('&' + key + '=' +data[key])

        print url
        result = requests.get(url, timeout=20).json()
        return result

    def cat2hc(self, data=None, product=None):
        if not (data and data['datas']):
            print 'monitor -- parameters error: it is not cat_datas'
            return False

        xy = self.parse_cat_point_lists(data['datas'])        
        #today = time.strftime('%Y-%m-%d',time.localtime(time.time()))
        hc = {
            "chart": {"type": "line"},
            "title": {"text": product},
            "xAxis": {"categories": xy['x_list']},
            "yAxis": {"title": {"text": data['unit']}},
            "series": [
                {"name": data['title'],"data": xy['y_list']}
                #{"name": 'John',"data": [5, 7, 3]}
                ]
            }
        return hc

    def parse_cat_point_lists(self, cat_point_lists):
        if type(cat_point_lists) is not list:
            print "it is not a cat format point lists."
            return False
        cat_points = cat_point_lists[0]
        ret = {"x_list": [], "y_list": []}
        items = cat_points.items()
        items.sort()
        for key,value in items:
            tmp_time = time.localtime(int(key) /1000)
            tmp_time = time.strftime('%H:%M', tmp_time)
            ret["x_list"].append(tmp_time)
            ret["y_list"].append(value)
        return ret


    def monitor_subclass(self, data=None):
        if not (data and data['product'] and data['monitor_type']):
            print 'monitor -- parameters error: do not have product or monitor_type'
            return False
        
        hcs = []
        dba_portal_redis = DBAPortalRedis()
        data['product'] = self._monitor_ip_lists
        for monitor_ip in data['product']:
            redis_key = "monitor_" + data['monitor_type'] + "_" + monitor_ip
            if not data.has_key('timeRange'):
                data['timeRange'] = 24
            redis_key += ("_" + str(data['timeRange']))
            product = "db-mysql-" + monitor_ip + "-3306"
            data['product'] = product
            monitor_all = dba_portal_redis.get_monitor_all(redis_key) if dba_portal_redis._redis.exists(redis_key) else ''

            if not monitor_all:
                monitor_all = self.list_all(data)
                if monitor_all and monitor_all["lineCharts"]:
                    dba_portal_redis.set_json_with_expire(redis_key, monitor_all, 300 * int(data['timeRange']))

            monitor_id = "cat:Metric:" + data['monitor_type'] + ":SUM"
            hc = None
            for key1 in monitor_all:
                for lineChart in monitor_all[key1]:
                    if lineChart['id'] == monitor_id:
                        hc = lineChart

            hc_title = self._monitor_ip_dict[monitor_ip] + "-" + monitor_ip + ":3306"
            hc = self.cat2hc(hc, hc_title)
            hcs.append(hc)
        return hcs


    def flush_redis(self, monitor_type, timeRange=24):
        dba_portal_redis = DBAPortalRedis()
        for monitor_ip in self._monitor_ip_lists:
            redis_key = "monitor_" + monitor_type + "_" + monitor_ip
            if not timeRange:
                timeRange = 24
            redis_key += ("_" + str(timeRange))

            product = "db-mysql-" + monitor_ip + "-3306"
            monitor_all = dba_portal_redis.get_monitor_all(redis_key) if dba_portal_redis._redis.exists(redis_key) else ''

            if not monitor_all:
                monitor_all = self.list_all({'product':product})
                if monitor_all and monitor_all["lineCharts"]:
                    dba_portal_redis.set_json_with_expire(redis_key, monitor_all, 180 * int(timeRange))
        return True



if __name__ == '__main__':
    test_monitor = Monitor()
    for timeRange in (1,2,6,12,24):
        result = test_monitor.flush_redis('questions', timeRange)
        print result
