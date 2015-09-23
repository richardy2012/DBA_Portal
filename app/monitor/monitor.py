#-*- coding: utf-8 -*-
__author__ = 'caodanfeng'
import json,requests,time
import sys
import getopt
import monitor_config
sys.path.append("..")
from redispy.redispy import DBAPortalRedis
from config import AppConfig
from db_connect.MySQL_lightweight import MySQL_lightweight

class Monitor():
    _monitor_ip_lists = ["10.1.125.16","10.1.125.15","10.1.125.14","10.1.101.136","10.1.6.17","10.1.125.11","10.1.125.23","10.1.6.40","10.1.6.41","10.1.6.114","10.1.6.115","10.1.110.62","10.1.110.64","10.1.125.24","10.1.125.34","10.1.101.158","10.1.101.130","10.1.125.12","10.1.125.13","10.1.125.192","10.1.101.143","10.1.101.15","10.1.101.36","10.1.101.149","10.1.101.98","10.1.101.174","10.1.101.161","10.1.6.226","10.1.6.225","10.1.6.230","10.3.10.55","10.3.10.66","10.3.10.23","10.3.10.53","10.1.101.131","10.1.101.132","10.1.101.120","10.1.101.92","10.3.10.68","10.3.10.69","10.1.110.108","10.1.110.110","10.1.1.135","10.1.1.205"]
    _monitor_ip_dict = {
        "10.1.125.16":"pctorder","10.1.125.15":"pctorder","10.1.125.14":"pctorder","10.1.101.136":"pctorder","10.1.6.17":"pctorder",
        "10.1.125.11":"paybase","10.1.125.23":"paybase",
        "10.1.6.40":"tpfun","10.1.6.41":"tpfun",
        "10.1.6.114":"tgtp","10.1.6.115":"tgtp",
        "10.1.110.62":"pctaccount","10.1.110.64":"pctaccount",
        "10.1.125.24":"pctaccountaudit","10.1.125.34":"pctaccountaudit",
        "10.1.101.158":"pctchannel","10.1.101.130":"pctchannel",
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
        dbconfig = {'host':monitor_config.DBMONITOR_DB_IP,
                    'port':monitor_config.DBMONITOR_DB_PORT,
                    'user':AppConfig.MYSQL_ADMIN_USR,
                    'passwd':AppConfig.MYSQL_ADMIN_PSWORD,
                    'db':self._dbmonitor_db,
                    'charset':'utf8'}
        print dbconfig
        self._db = MySQL_lightweight(dbconfig)

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

        #print url
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
        if not (data and data['product'] and data['type']):
            print 'monitor -- parameters error: do not have product or type'
            return False

        hcs = []
        dba_portal_redis = DBAPortalRedis()
        data['product'] = self._monitor_ip_lists
        for monitor_ip in data['product']:
            redis_key = "monitor_" + data['type'] + "_" + monitor_ip
            if not data.has_key('timeRange'):
                data['timeRange'] = 24
            redis_key += ("_" + str(data['timeRange']))
            product = "db-mysql-" + monitor_ip + "-3306"
            data['product'] = product
            #monitor_all = dba_portal_redis.get_monitor_all(redis_key) if dba_portal_redis._redis.exists(redis_key) else ''
            monitor_all = ''

            if not monitor_all:
                monitor_all = self.list_all(data)
                # if monitor_all and monitor_all["lineCharts"]:
                #     dba_portal_redis.set_json_with_expire(redis_key, monitor_all, (600 + 600 * int(data['timeRange'])))

            monitor_id = "cat:Metric:" + data['type'] + ":SUM"
            hc = None
            for key1 in monitor_all:
                for lineChart in monitor_all[key1]:
                    if lineChart['id'] == monitor_id:
                        hc = lineChart

            hc_title = self._monitor_ip_dict[monitor_ip] + "-" + monitor_ip + ":3306"
            hc = self.cat2hc(hc, hc_title)
            hcs.append(hc)
        return hcs

    def flush_redis(self, type, timeRange=24):
        dba_portal_redis = DBAPortalRedis()
        for monitor_ip in self._monitor_ip_lists:
            redis_key = "monitor_" + type + "_" + monitor_ip
            if not timeRange:
                timeRange = 24
            redis_key += ("_" + str(timeRange))

            product = "db-mysql-" + monitor_ip + "-3306"
            monitor_all = dba_portal_redis.get_monitor_all(redis_key) if dba_portal_redis._redis.exists(redis_key) else ''

            if not monitor_all:
                print '.'
                monitor_all = self.list_all({'product':product})
                if monitor_all and monitor_all["lineCharts"]:
                    dba_portal_redis.set_json_with_expire(redis_key, monitor_all, (600 + 600 * int(timeRange)))
        return True


    def monitor_peak_subclass(self, data=None, ip_list=''):
        if not data:
            print 'monitor -- parameters error: do not have monitor type'
            return False

        if not data.has_key('type'): data['type'] = 'question'
        if not data.has_key('date'): data['date'] = time.strftime('%Y%m%d%H',time.localtime(time.time()))
        if not data.has_key('timeRange'): data['timeRange'] = 2

        dba_portal_redis = DBAPortalRedis()
        ip_list = [ip_list] if ip_list else self._monitor_ip_lists
        result = {}
        for monitor_ip in ip_list:
            product = "db-mysql-" + monitor_ip + "-3306"
            data['product'] = product
            print '.'
            monitor_all = self.list_all(data)
            monitor_id = "cat:Metric:" + data['type'] + ":SUM"
            for key1 in monitor_all:
                for lineChart in monitor_all[key1]:
                    if lineChart['id'] and lineChart['id'] == monitor_id:
                        instance = self._monitor_ip_dict[monitor_ip] + "-" + monitor_ip + ":3306"
                        result[instance] = self.get_peak(lineChart['datas'])
                        result[instance]['ip'] = monitor_ip
                        result[instance]['cluster'] = self._monitor_ip_dict[monitor_ip]
        return result


    def get_peak(self, cat_point_lists):
        if type(cat_point_lists) is not list:
            print "it is not a cat format point lists."
            return False
        cat_points = cat_point_lists[0]
        ret = {"x_list": [], "y_list": []}
        items = cat_points.items()
        items.sort()
        max_y = 0
        max_point = {}
        for key,value in items:
            #print key,int(value)
            if int(value) > max_y:
                max_y = int(value)
                tmp_time = time.localtime(int(key) /1000)
                tmp_time = time.strftime('%H:%M', tmp_time)
                max_point["time"] = tmp_time
                max_point["max"] = str(float(value)/1000) + 'K'
        return max_point

def usage():
    print "Usage:\tpython %s --type=[questions|tps] --date=2015091310 --range=2 --ip=10.1.125.14\n" % sys.argv[0]
    print "type:\tmonitor type that cat system supported."
    print "\tdefault: questions"
    print "date:\tending time point, format: %Year%Month%Day%Hour."
    print "\tdefault: now"
    print "range:\thours to be analyzed."
    print "\tdefault: 2"
    print "ip:\tip of mysql instance to be analyzed."
    print "\tdefault: all important mysql ips in 917\n"
    #print "Usage: python %s -t [questions|tps] -d 2015091710 -t 2 -i 10.1.125.14" % sys.argv[0]


if __name__ == '__main__':
    try:
        opts,args = getopt.getopt(sys.argv[1:], "ht:d:r:i:", ["help=","type=", "date=","range=","ip="])

        if len(sys.argv) < 2:
            usage()
            sys.exit(1)

        #check all param
        data = {}
        ip_list = ''
        for opt,arg in opts:
            if opt in ("-h", "--help") or opt not in ("-t", "--type", "-d", "--date", "-r", "--range", "-i", "--ip"):
                usage()
                sys.exit(1)
            if opt in ("-t", "--type"):
                data["type"] = arg
            elif opt in ("-d", "--date"):
                data["date"] = arg
                now = time.strftime('%Y%m%d%H',time.localtime(time.time()))
                if int(arg) > int(now):
                    print "Please check paras: date is not available."
                    sys.exit(1)
            elif opt in ("-r", "--range"):
                data["timeRange"] = arg
            elif opt in ("-i", "--ip"):
                ip_list = arg

        print 'processing'
        test_monitor = Monitor()
        result = test_monitor.monitor_peak_subclass(data, ip_list)
        #print result
        for instance in sorted(result.keys()):
            print "%s\t%s\t%s\t%s" % (result[instance]['cluster'], result[instance]['ip'], result[instance]['time'], result[instance]['max'])


    except getopt.GetoptError:
        print("getopt error!");
        usage();
        sys.exit(1);


#    for timeRange in (1,2,6,12,24):
#        for type in ("questions","tps","io_util","iops","usr","sys","thds_run","network_out"):
    # for timeRange in (1,2,6,12,24):
    #     for type in ("questions"):
    #         result = test_monitor.flush_redis(type, timeRange)
    #         print result

    # for day in range(911,912):
    #     date = '20150' + str(day) + '10'
    #     for type in ('questions', 'tps'):
    #         print date, type
    #         supported_query_key = {'type':type, 'timeRange':2, 'date':date}
    #         result = test_monitor.monitor_peak_subclass(supported_query_key)
    #         for instance in result:
    #             print "%s\t%s\t%s" % (instance, result[instance]['time'], result[instance]['max'])

