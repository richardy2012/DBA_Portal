#-*- coding: utf-8 -*-
__author__ = 'caodanfeng'
import json,requests,time
import os,sys,re
import getopt
import monitor_config
sys.path.append("..")
from config import AppConfig
from db_connect.MySQL_lightweight import MySQL_lightweight

class MonitorArchive():
    _dbmonitor_db = 'DBMonitor'
    _db = None
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
    _monitor_type = [
        'com_drop_table',
        'com_create_index',
        'tps',
        'com_kill',
        'thd_idle_thds',
        'aborted_clients',
        'aborted_connects',
        'cre_tmp_tabs',
        'com_select',
        'tb_open_cache_overs',
        'com_update',
        'com_alter_table',
        'questions',
        'thds_conn',
        'thds_run',
        'delay',
        'tb_open_cache_hits',
        'cre_tmp_disk_tabs',
        'com_delete',
        'thd_thds',
        'tb_open_cache_miss',
        'com_drop_index',
        'com_insert',
        'network_out',
        'network_in',
        'sys',
        'idle',
        'wa',
        'usr',
        'load',
        'swapTotal',
        'free',
        'swapFree',
        'swapUsed',
        'used',
        'inn_row_lk_time_avg',
        'inn_deadlocks',
        'inn_row_lk_time_max',
        'inn_mutex_spin_waits',
        'inn_mutex_spin_rounds',
        'inn_curr_row_lks',
        'inn_mutex_os_waits',
        'inn_row_lk_waits',
        'inn_x_lk_spin_waits',
        'tb_lks_waited',
        'inn_s_lk_os_waits',
        'inn_row_lk_curr_waits',
        'inn_s_lk_spin_rounds',
        'inn_row_lk_time',
        'inn_bp_wait_free',
        'inn_x_lk_os_waits',
        'inn_log_waits',
        'tb_lks_immediate',
        'inn_s_lk_spin_waits',
        'inn_x_lk_spin_rounds',
        'inn_rows_updated',
        'inn_rows_inserted',
        'inn_data_preads',
        'inn_ibuf_mer',
        'inn_his_list_len',
        'inn_bp_pgs_tot',
        'slow_queries',
        'inn_bp_pgs_md_noty',
        'inn_log_write_req',
        'inn_ibuf_free_list',
        'inn_os_log_fsyncs',
        'inn_os_log_pfsyncs',
        'inn_ckp_max_age',
        'created_tmp_files',
        'inn_bp_reads',
        'bytes_sent',
        'inn_bp_pgs_old',
        'inn_bp_read_ah_evi',
        'bytes_received',
        'queries',
        'inn_log_writes',
        'inn_ibuf_mer_ins',
        'inn_pgs_cre',
        'inn_data_pwrites',
        'inn_bp_pgs_lru_flu',
        'inn_data_pfsyncs',
        'modified_age',
        'inn_rows_del',
        'inn_data_written',
        'inn_bp_pgs_flu',
        'inn_data_writes',
        'inn_pread',
        'inn_bp_pgs_misc',
        'sort_scan',
        'inn_data_reads',
        'inn_bp_read_ah',
        'inn_bp_pgs_made_y',
        'inn_data_read',
        'inn_bp_pgs_dirty',
        'inn_ibuf_mer_dels',
        'inn_os_log_written',
        'handler_commit',
        'inn_bp_pgs_free',
        'inn_bp_wri_req',
        'handler_rollback',
        'sort_range',
        'inn_data_fsyncs',
        'inn_ava_ulogs',
        'inn_bp_read_req',
        'inn_ckp_age',
        'inn_pwritten',
        'inn_bp_read_ah_rnd',
        'sort_rows',
        'sort_merge_pas',
        'inn_ibuf_mer_del_mks',
        'inn_os_log_pwrites',
        'io_reads',
        'io_writes',
        'io_util',
        'iops',
        'diskUsedRatio',
        'diskAvail'
    ]

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
            row['max_show'] = (str(row['max_value']/1000) + 'K') if row['max_value'] else '0'
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
