#-*- coding: utf-8 -*-
__author__ = 'caodanfeng'
import json,requests,time
import os,sys,re
import getopt
import monitor_config
sys.path.append("..")
from config import AppConfig
from db_connect.MySQL_lightweight import MySQL_lightweight

def float2humanread(integer):
    """
    Description: translate integer into human read format(K,M,G,T,P)
    Parameters format:
    ### integer: 1000000
    Example:
    ### float2humanread(1000000)
    ### return '1M'
    """
    try:
        integer = float(integer)
    except:
        raise Exception('please pass a int or float into function!')

    suffix_array = ['','K','M','G','T','P']
    i = 0
    while integer >= 1000 and i < len(suffix_array):
        integer /= 1000
        i += 1
    integer = "%.2f" % integer
    humanread = str(integer) + suffix_array[i]
    return humanread


class MonitorArchive():
    _dbmonitor_db = 'DBMonitor'
    _db = None
    _monitor_ip_lists = monitor_config.MONITOR_IP_LIST_917
    _monitor_ip_dict = monitor_config.MONITOR_IP_DICT_917
    _monitor_type = monitor_config.MONITOR_TYPE

    def __init__(self):
        dbconfig = {'host':monitor_config.DBMONITOR_DB_IP,
                    'port':monitor_config.DBMONITOR_DB_PORT,
                    'user':AppConfig.MYSQL_ADMIN_USR,
                    'passwd':AppConfig.MYSQL_ADMIN_PSWORD,
                    'db':self._dbmonitor_db,
                    'charset':'utf8'}
        print dbconfig
        self._db = MySQL_lightweight(dbconfig)


    def get_mtype_list(self):
        return self._monitor_type

    def get_hc_para(self, date, ip, port='3306', monitor_type='questions'):
        if not (self.check_date(date) and ip):
            print 'get_hc_para -- parameters error'
            return False
        st_time = date + ' 09:00:00'
        en_time = date + ' 11:00:00'
        sql = "select GroupName, MTime, %s from DBMonitor_History where IP='%s' and Port='%s' and MTime>='%s' and MTime<='%s' order by MTime" % (monitor_type, ip, port, st_time, en_time)
        print sql
        self._db.query(sql)
        rows = self._db.fetchAllArray();
        for row in rows:
            print row['MTime'], row[monitor_type]
        return rows

    def archive_dashboard(self, date, monitor_type='questions'):
        if not (self.check_date(date)):
            print 'archive_dashboard -- parameters error'
            return False
        st_time = date + ' 09:00:00'
        en_time = date + ' 11:00:00'
        sql = "select GroupName,IP,max(%s) as max_value from DBMonitor_History where MTime>='%s' and MTime<='%s' group by IP order by GroupName" % (monitor_type, st_time, en_time)
        print sql
        self._db.query(sql)
        rows = self._db.fetchAllArray();
        for row in rows:
            row['max_show'] = row['max_value'] if row['max_value'] else '0'
            row['max_show'] = float2humanread(row['max_value'])
        return rows

    def archive_instance(self, ip, date):
        if not (self.check_date(date)):
            print 'archive_dashboard -- parameters error'
            return False
        st_time = date + ' 09:00:00'
        en_time = date + ' 11:00:00'
        mtype_list = "`,`".join(self._monitor_type)
        #print mtype_list
        sql = "select MTime,GroupName,IP,`%s` from DBMonitor_History where IP='%s' and MTime>='%s' and MTime<='%s' order by MTime" % (mtype_list,ip, st_time, en_time)
        #sql = "select MTime,GroupName,IP,questions,tps from DBMonitor_History where IP='%s' and MTime>='%s' and MTime<='%s' order by MTime" % (ip, st_time, en_time)
        print sql
        self._db.query(sql)
        rows = self._db.fetchAllArray();
        hcs = {}
        for mtype in self._monitor_type:
            hcs[mtype] = {
                "chart": {"type": "line"},
                "title": {"text": mtype},
                "xAxis": {"categories": []},
                "yAxis": {"title": {"text": "Value/秒"}},
                "series": [
                    {"name": mtype,"data": []}
                ]
            }

        for row in rows:
            tmp_time = row["MTime"].strftime('%H:%M')
            for mtype in self._monitor_type:
                hcs[mtype]["xAxis"]["categories"].append(tmp_time)
                hcs[mtype]["series"][0]["data"].append(row[mtype])
        # for mtype in hcs:
        #     print hcs[mtype]
        return hcs

    def check_date(self,date):
        """
        Description: check date if it is a formatted date
        Parameters:
        ### date: '2000-03-03'
        Example:
        ### check_date('2000-03-03')
        ### return True
        """
        if not (date and (type(date) is str or type(date) is unicode)):
            print 'check_date -- parameters error'
            return False
        date = date.encode("utf-8") if type(date) is unicode else date
        match = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', date)
        return True if match else False


    def backup_917_in_cat(self, ip=None, date=None):
        if not (ip and date):
            print 'monitor -- parameters error: need ip and date'
            return False
        product = "db-mysql-" + str(ip) + "-3306"
        url = 'http://cat.dp/cat/r/database?op=view&forceDownload=json&timeRange=2'
        url += ('&product=%s&date=%s' % (product,date))
        print url
        result = requests.get(url, timeout=20).json()
        if result.has_key('lineCharts') and result['lineCharts']:
            f_out = '917archive/' + str(ip) + '_' + str(date)
            with open(f_out, 'w') as f:
                f.write(json.dumps(result))
        return result

    def list_stat_type(self, ip=None, date=None):
        if not (ip and date):
            print 'monitor -- parameters error: need ip and date'
            return False
        product = "db-mysql-" + str(ip) + "-3306"
        url = 'http://cat.dp/cat/r/database?op=view&forceDownload=json&timeRange=2'
        url += ('&product=%s&date=%s' % (product,date))
        print url
        result = requests.get(url, timeout=20).json()
        if result.has_key('lineCharts') and result['lineCharts']:
            for lineChart in result['lineCharts']:
                sub = lineChart['id'].split(':')
                print sub[2]
        return True

    def json_into_db(self, ip=None, date=None):
        if not (ip and date):
            print 'monitor -- parameters error: need ip and date'
            return False
        product = "db-mysql-" + str(ip) + "-3306"
        f_name = '917archive/' + str(ip) + '_' + str(date)
        print f_name
        count = 0
        if os.path.exists(f_name):
            with open(f_name, 'r') as f:
                dump = f.read()
                data_json = json.loads(dump) if type(dump) is str else ''
                #print type(data_json)
                simple_json = {}
                start_timestamp = None
                if data_json.has_key('lineCharts') and data_json['lineCharts']:
                    for lineChart in data_json['lineCharts']:
                        start_timestamp = lineChart['start']
                        sub = lineChart['id'].split(':')
                        mtype = sub[2]
                        simple_json[mtype] = lineChart['datas'][0]
                if start_timestamp:
                    start_timestamp = int(time.mktime(time.strptime(start_timestamp,'%Y/%m/%d %H:%M'))) * 1000
                if simple_json:
                    for minute in range(0,120):
                        sentinel = start_timestamp + 60000 * minute
                        MTime = time.localtime(sentinel/1000)
                        MTime = time.strftime('%Y-%m-%d %H:%M:%S', MTime)
                        GroupName = self._monitor_ip_dict[ip]
                        keys = 'GroupName,IP,Port,MTime'
                        values = "'%s','%s',%s,'%s'" % (GroupName,ip,'3306',MTime)
                        for mtype in self._monitor_type:
                            keys += (',`' + mtype + '`')
                            value = str(simple_json[mtype][str(sentinel)]) if simple_json[mtype].has_key(str(sentinel)) else '0'
                            values += (',' + value)
                        sql = 'INSERT INTO DBMonitor_History (%s) VALUES(%s)' % (keys, values)
                        #print sql
                        count += 1
                        ret = self._db.insert(sql)
                        if ret:
                            print ip
                            print ret
        print count
        return True


def usage():
    print "Backup all 917 important instance monitor data from CAT."
    print "Usage: python %s -t" % sys.argv[0]

if __name__ == '__main__':
    opts,args = getopt.getopt(sys.argv[1:], "hatd")

    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    for opt, arg in opts:
        if opt in ("-h"):
            usage()
            sys.exit(1)
        if opt in ("-a"):
            monitor_archive = MonitorArchive()
            for day in range(918,919):
                date = '20150' + str(day) + '10'
                for ip in monitor_archive._monitor_ip_lists:
                    print date, ip
                    monitor_archive.backup_917_in_cat(ip, date)
        if opt in ("-t"):
            monitor_archive = MonitorArchive()
            ip = '10.1.125.14'
            date = '2015091710'
            monitor_archive.list_stat_type(ip, date)
        if opt in ("-d"):
            monitor_archive = MonitorArchive()
            for day in range(910,919):
                date = '20150' + str(day) + '10'
                for ip in monitor_archive._monitor_ip_lists:
                    print date, ip
                    monitor_archive.json_into_db(ip, date)
