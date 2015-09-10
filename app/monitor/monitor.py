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

    _mha_monitor_ip1 = ["10.1.101.182",
                       "10.1.101.183",
                       "10.1.110.71",
                       "10.1.110.73",
                       "10.1.110.65",
                       "10.1.110.67",
                       "10.1.1.97",
                       "10.1.1.98",
#                       "10.1.1.240",
                       "10.1.1.121",
                       "10.1.1.73",
                       "10.1.1.28",
                       "10.1.101.126",
                       "10.1.101.151",
                       "10.3.10.23",
                       "10.3.10.53",
#                       "10.1.1.101",
#                       "10.1.1.208",
#                       "10.1.101.123",
                       "10.1.101.125",
                       "10.1.1.233",
                       "10.1.1.107",
                       "10.1.125.30",
                       "10.1.125.25",
                       "10.1.101.109",
                       "10.1.101.110",
                       "10.1.125.27",
                       "10.1.125.28",
                       "10.1.6.70",
                       "10.1.6.91",
                       "10.1.125.31",
                       "10.1.125.32",
                       "10.128.19.130",
#                       "10.128.19.131",
#                       "10.1.101.123",
                       "10.1.101.125",
                       "10.1.101.149",
                       "10.1.101.98",
                       "10.1.101.174",
                       "10.1.101.161",]
    _mha_monitor_ip2 = [
                       "10.3.10.22",
                       "10.3.10.63",
                       "10.3.10.39",
                       "10.3.10.62",
                       "10.1.101.143",
                       "10.1.101.15",
                       "10.1.101.36",
                       "10.3.10.19",
                       "10.3.10.34",
                       "10.1.101.79",
                       "10.1.101.90",
#                       "10.1.101.147",
                       "10.1.101.152",
                       "10.1.1.122",
                       "10.1.1.124",
#                       "10.1.1.197",
#                       "10.1.1.168",
                       "10.1.125.18",
                       "10.1.125.19",
                       "10.1.101.145",
                       "10.1.101.150",
                       "10.1.6.234",
                       "10.1.6.235",
#                       "10.1.1.169",
                       "10.1.1.170",
                       "10.1.1.210",
#                       "10.1.1.211",
                       "10.1.1.106",
                       "10.1.1.45",
                       "10.1.101.91",
                       "10.1.101.93",
                       "10.1.101.57",
                       "10.1.101.58",
                       "10.1.101.115",
                       "10.1.101.117",
                       "10.3.10.24",
                       "10.3.10.54",
                       "10.1.1.194",
                       "10.1.1.173",
                       "10.1.110.108",
                       "10.1.110.110",
                       "10.1.125.25",
                       "10.1.125.30",
                       "10.1.125.11",
                       "10.1.125.23",
                       "10.1.110.62",
                       "10.1.110.64",
                       "10.1.110.145",
                       "10.1.101.136",
                       "10.1.101.158",
                       "10.1.101.130",
                       "10.3.10.68",
                       "10.3.10.69",
                       "10.1.125.12",
                       "10.1.125.13",
                       "10.1.125.192",
                       "10.1.125.16",
                       "10.1.125.15",
                       "10.1.125.14",
                       "10.1.6.62",
                       "10.1.6.63",
                       "10.1.6.17",
                       ]
    _mha_monitor_ip3 = [
                       "10.1.133.130",
                       "10.1.133.140",
                       "10.1.1.46",
                       "10.1.1.47",
                       "10.1.6.86",
                       "10.1.6.87",
#                       "10.3.10.25",
                       "10.3.10.36",
                       "10.1.101.171",
                       "10.1.101.172",
                       "10.1.101.31",
                       "10.1.101.49",
                       "10.1.115.60",
                       "10.1.115.70",
                       "10.1.1.143",
#                       "10.1.1.144",
                       "10.1.101.101",
                       "10.1.101.82",
                       "10.1.125.35",
                       "10.1.125.33",
                       "10.1.6.199",
                       "10.1.6.51",
                       "10.1.110.114",
                       "10.1.110.115",
                       "10.1.110.69",
                       "10.1.110.81",
                       "10.1.110.82",
                       "10.1.110.66",
                       "10.1.101.127",
                       "10.1.101.129",
                       "10.1.125.35",
                       "10.1.125.36",
#                       "10.1.111.211",
#                       "10.1.111.214",
#                       "10.1.111.217",
#                       "10.1.111.218",
                       "10.1.1.114",
                       "10.1.1.22",
                       "10.1.1.136",
                       "10.1.101.112",
                       "10.1.101.113",
                       "10.1.101.62",
                       "10.1.101.39",
                       "10.1.101.131",
                       "10.1.101.132",
                       "10.1.101.120",
                       "10.1.101.92",
                       "10.1.1.135",
                       "10.1.1.205",
                       "10.3.10.55",
                       "10.3.10.66",
                       "10.1.6.114",
                       "10.1.6.115",
                       "10.1.101.142",
                       "10.1.101.144",
                       "10.3.10.37",
                       "10.3.10.67",
                       "10.1.6.226",
                       "10.1.6.225",
                       "10.1.6.230",
                       "10.1.6.40",
                       "10.1.6.41",
                       "10.1.101.170",
                       "10.1.101.169",
                       ]
    _mha_monitor_ip4 = [
                       "10.3.10.11",
                       "10.3.10.26",
                       "10.3.10.12",
                       "10.3.10.27",
                       "10.3.10.13",
                       "10.3.10.28",
                       "10.3.10.14",
                       "10.3.10.29",
                       "10.3.10.15",
                       "10.3.10.30",
                       "10.3.10.16",
                       "10.3.10.31",
                       "10.3.10.17",
                       "10.3.10.32",
                       "10.3.10.18",
                       "10.3.10.33",
                       "10.3.10.20",
                       "10.3.10.35",
                       "10.3.10.56",
                       "10.3.10.57",
                       "10.3.10.58",
                       "10.3.10.59",
                       "10.3.10.60",
                       "10.3.10.61",
                       "10.1.101.133",
                       "10.1.101.146",
                       "10.1.101.47",
                       "10.1.101.74",
                       "10.3.10.65",
                       "10.3.10.64",
                       "10.1.6.210",
                       "10.1.6.215",
                       "10.1.101.135",
                       #"10.1.101.137"
                       ]

    _mha_dict = {
        "10.1.101.182":"ad",
        "10.1.101.183":"ad",
        "10.1.110.71":"apollo01",
        "10.1.110.73":"apollo01",
        "10.1.110.65":"apollo02",
        "10.1.110.67":"apollo02",
        "10.1.1.97":"audit",
        "10.1.1.98":"audit",
        "10.1.1.240":"bicms",
        "10.1.1.121":"bicms",
        "10.1.1.73":"biz",
        "10.1.1.28":"biz",
        "10.1.101.126":"biz02",
        "10.1.101.151":"biz02",
        "10.3.10.23":"bonus",
        "10.3.10.53":"bonus",
        "10.1.1.101":"bugtest",
        "10.1.1.208":"bugtest",
        "10.1.101.123":"cat",
        "10.1.101.125":"cat",
        "10.1.1.233":"category",
        "10.1.1.107":"category",
        "10.1.125.30":"child",
        "10.1.125.25":"child",
        "10.1.101.109":"common09",
        "10.1.101.110":"common09",
        "10.1.125.27":"crawler",
        "10.1.125.28":"crawler",
        "10.1.6.70":"credit",
        "10.1.6.91":"credit",
        "10.1.125.31":"crm",
        "10.1.125.32":"crm",
        "10.128.19.130":"csc01",
        "10.128.19.131":"csc01",
        "10.1.101.123":"datacomm02",
        "10.1.101.125":"datacomm02",
        "10.1.101.149":"deal",
        "10.1.101.98":"deal",
        "10.1.101.174":"deal",
        "10.1.101.161":"deal",
        "10.3.10.22":"dianpingbc",
        "10.3.10.63":"dianpingbc",
        "10.3.10.39":"dianpingbs",
        "10.3.10.62":"dianpingbs",
        "10.1.101.143":"dianpingpct",
        "10.1.101.15":"dianpingpct",
        "10.1.101.36":"dianpingpct",
        "10.3.10.19":"dpuser01",
        "10.3.10.34":"dpuser01",
        "10.1.101.79":"dw",
        "10.1.101.90":"dw",
        "10.1.101.147":"follow",
        "10.1.101.152":"follow",
        "10.1.1.122":"group01",
        "10.1.1.124":"group01",
        "10.1.1.197":"group02",
        "10.1.1.168":"group02",
        "10.1.125.18":"hive11",
        "10.1.125.19":"hive11",
        "10.1.101.145":"hotel",
        "10.1.101.150":"hotel",
        "10.1.6.234":"kvdb",
        "10.1.6.235":"kvdb",
        "10.1.1.169":"log",
        "10.1.1.170":"log",
        "10.1.1.210":"mail",
        "10.1.1.211":"mail",
        "10.1.1.106":"main",
        "10.1.1.45":"main",
        "10.1.101.91":"main03",
        "10.1.101.93":"main03",
        "10.1.101.57":"mc",
        "10.1.101.58":"mc",
        "10.1.101.115":"mfs01new",
        "10.1.101.117":"mfs01new",
        "10.3.10.24":"midas",
        "10.3.10.54":"midas",
        "10.1.1.194":"mobile",
        "10.1.1.173":"mobile",
        "10.1.110.108":"mopay",
        "10.1.110.110":"mopay",
        "10.1.125.25":"ovs01",
        "10.1.125.30":"ovs01",
        "10.1.125.11":"paybase",
        "10.1.125.23":"paybase",
        "10.1.110.62":"pctaccount",
        "10.1.110.64":"pctaccount",
        "10.1.110.145":"pctaccount",
        "10.1.101.136":"pctchannel",
        "10.1.101.158":"pctchannel",
        "10.1.101.130":"pctchannel",
        "10.3.10.68":"pctdiscount",
        "10.3.10.69":"pctdiscount",
        "10.1.125.12":"pctengine",
        "10.1.125.13":"pctengine",
        "10.1.125.192":"pctengine",
        "10.1.125.16":"pctorder",
        "10.1.125.15":"pctorder",
        "10.1.125.14":"pctorder",
        "10.1.6.62":"pctorderprocess",
        "10.1.6.63":"pctorderprocess",
        "10.1.6.17":"pctorderprocess",
        "10.1.133.130":"pctreconcile",
        "10.1.133.140":"pctreconcile",
        "10.1.1.46":"pic",
        "10.1.1.47":"pic",
        "10.1.6.86":"pic02",
        "10.1.6.87":"pic02",
        "10.3.10.25":"picplaza",
        "10.3.10.36":"picplaza",
        "10.1.101.171":"plat",
        "10.1.101.172":"plat",
        "10.1.101.31":"plat02",
        "10.1.101.49":"plat02",
        "10.1.115.60":"poi",
        "10.1.115.70":"poi",
        "10.1.1.143":"ppu01",
        "10.1.1.144":"ppu01",
        "10.1.101.101":"review",
        "10.1.101.82":"review",
        "10.1.125.35":"sales",
        "10.1.125.33":"sales",
        "10.1.6.199":"search",
        "10.1.6.51":"search",
        "10.1.110.114":"settle",
        "10.1.110.115":"settle",
        "10.1.110.69":"shop",
        "10.1.110.81":"shop",
        "10.1.110.82":"shop",
        "10.1.110.66":"shop",
        "10.1.101.127":"small01",
        "10.1.101.129":"small01",
        "10.1.125.35":"test_dba",
        "10.1.125.36":"test_dba",
        "10.1.111.211":"test_vm",
        "10.1.111.214":"test_vm",
        "10.1.111.217":"test_vm",
        "10.1.111.218":"test_vm",
        "10.1.1.114":"tg",
        "10.1.1.22":"tg",
        "10.1.1.136":"tg",
        "10.1.101.112":"tgevent",
        "10.1.101.113":"tgevent",
        "10.1.101.62":"tgkv",
        "10.1.101.39":"tgkv",
        "10.1.101.131":"tgreceipt",
        "10.1.101.132":"tgreceipt",
        "10.1.101.120":"tgreceipt",
        "10.1.101.92":"tgreceipt",
        "10.1.1.135":"tgreceiptstock",
        "10.1.1.205":"tgreceiptstock",
        "10.3.10.55":"tgstock",
        "10.3.10.66":"tgstock",
        "10.1.6.114":"tgtp",
        "10.1.6.115":"tgtp",
        "10.1.101.142":"tinylife",
        "10.1.101.144":"tinylife",
        "10.3.10.37":"toplist",
        "10.3.10.67":"toplist",
        "10.1.6.226":"tpd_deal",
        "10.1.6.225":"tpd_deal",
        "10.1.6.230":"tpd_deal",
        "10.1.6.40":"tpfun",
        "10.1.6.41":"tpfun",
        "10.1.101.170":"uc",
        "10.1.101.169":"uc",
        "10.3.10.11":"unifiedorder0",
        "10.3.10.26":"unifiedorder0",
        "10.3.10.12":"unifiedorder1",
        "10.3.10.27":"unifiedorder1",
        "10.3.10.13":"unifiedorder2",
        "10.3.10.28":"unifiedorder2",
        "10.3.10.14":"unifiedorder3",
        "10.3.10.29":"unifiedorder3",
        "10.3.10.15":"unifiedorder4",
        "10.3.10.30":"unifiedorder4",
        "10.3.10.16":"unifiedorder5",
        "10.3.10.31":"unifiedorder5",
        "10.3.10.17":"unifiedorder6",
        "10.3.10.32":"unifiedorder6",
        "10.3.10.18":"unifiedorder7",
        "10.3.10.33":"unifiedorder7",
        "10.3.10.20":"unifiedorder_config",
        "10.3.10.35":"unifiedorder_config",
        "10.3.10.56":"unifiedorder_operation",
        "10.3.10.57":"unifiedorder_operation",
        "10.3.10.58":"unifiedorder_shop01",
        "10.3.10.59":"unifiedorder_shop01",
        "10.3.10.60":"unifiedorder_shop02",
        "10.3.10.61":"unifiedorder_shop02",
        "10.1.101.133":"usrmsg",
        "10.1.101.146":"usrmsg",
        "10.1.101.47":"wed",
        "10.1.101.74":"wed",
        "10.3.10.65":"yym3",
        "10.3.10.64":"yym3",
        "10.1.6.210":"zabbix",
        "10.1.6.215":"zabbix",
        "10.1.101.135":"zsuser",
        "10.1.101.137":"zsuser"
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
            url += ('&' + key + '=' + str(data[key]))

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
                    dba_portal_redis.set_json_with_expire(redis_key, monitor_all, (10 + 10 * int(data['timeRange'])))

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

    def monitor_all_mha(self, data=None):
        if not (data and data['product'] and data['monitor_type']):
            print 'monitor -- parameters error: do not have product or monitor_type'
            return False
        
        hcs = []
        dba_portal_redis = DBAPortalRedis()
        if data['monitor_range'] == 'all1':
            data['product'] = self._mha_monitor_ip1
        elif data['monitor_range'] == 'all2':
            data['product'] = self._mha_monitor_ip2
        elif data['monitor_range'] == 'all3':
            data['product'] = self._mha_monitor_ip3
        elif data['monitor_range'] == 'all4':
            data['product'] = self._mha_monitor_ip4
        for monitor_ip in data['product']:
            if not data.has_key('timeRange'):
                data['timeRange'] = '24'
            product = "db-mysql-" + monitor_ip + "-3306"
            data['product'] = product
            monitor_all = self.list_all(data)
            monitor_id = "cat:Metric:" + data['monitor_type'] + ":SUM"
            hc = None
            for key1 in monitor_all:
                for lineChart in monitor_all[key1]:
                    if lineChart['id'] == monitor_id:
                        hc = lineChart            
            hc_title = self._mha_dict[monitor_ip] + "-" + monitor_ip + ""
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
                    dba_portal_redis.set_json_with_expire(redis_key, monitor_all, (10 + 10 * int(timeRange)))
        return True



if __name__ == '__main__':
    test_monitor = Monitor()
#    for timeRange in (1,2,6,12,24):
#        for monitor_type in ("questions","tps","io_util","iops","usr","sys","thds_run","network_out"):
    for timeRange in (1,2,6,12,24):
        for monitor_type in ("questions"):
            result = test_monitor.flush_redis(monitor_type, timeRange)
            print result
