#-*- coding: utf-8 -*-
__author__ = 'caodanfeng'
import urllib2
import urllib
import json,requests,time
#from cmdb_api_base import CmdbApiBase

class Monitor():
    def list_all(self, data=None):
        if not (data and data['product']):
            print 'monitor -- parameters error: do not have product'
            return False
        url = 'http://cat.dp/cat/r/database?op=view&group=&timeRange=1&forceDownload=json'
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
        for product in data['product']:
            monitor_all = self.list_all({'product':product})
            monitor_id = "cat:Metric:" + data['monitor_type'] + ":SUM"
            hc = None
            for key1 in monitor_all:
                for lineChart in monitor_all[key1]:
                    if lineChart['id'] == monitor_id:
                        hc = lineChart
            hc = self.cat2hc(hc, product)
            hcs.append(hc)
        return hcs




if __name__ == '__main__':
    test_monitor = Monitor()
    query_condition = {'product':'db-mysql-10.1.125.14-3306', 'monitor_type':'questions'}
    result = test_monitor.monitor_subclass(query_condition)
    print result
