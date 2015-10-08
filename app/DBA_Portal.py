# coding: utf8
import requests,json,flask
import sys,time,re,datetime
import bs4, redis

from flask import Flask,render_template,request,url_for,redirect,flash,current_app,abort
from datetime import timedelta

from cmdb.server import ServerList
from cmdb.instance import InstanceList
from cmdb.server_info_form import ServerInfoForm, ServerInitForm, InstanceInfoForm, StandbyServerInfoForm, ApplyServerForm, InstallDbForm, BackupForm
from config import AppConfig
from cmdb.cmdb_api_base import CmdbApiCallException
from cmdb.cluster import Cluster

from cas_urls import create_cas_login_url
from cas_urls import create_cas_logout_url
from cas_urls import create_cas_validate_url

from backup.backup import FileBackup, BackupList
from monitor.monitor import Monitor
from monitor.archive917 import MonitorArchive

from redispy.redispy import DBAPortalRedis,RTMRedis

try:
    from urllib import urlopen
except ImportError:
    from urllib.request import urlopen

reload(sys)
sys.setdefaultencoding('utf8')

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'hello_dba'
app.config['USER_CODE'] = 'Zaq!@#$%^yhgtREWSXcdfvbnhy&*90oiujkl'


###################################
# global useful function
###################################

def have_accessed():
    """
    Description: access whether the user have login or not.
    """
    try:
        if current_app.config.has_key('CAS_TOKEN_SESSION_KEY') and current_app.config['CAS_TOKEN_SESSION_KEY'] in flask.session:
            return True
        else:
            return False
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')

def add_authority_parameters(query_condition=None):
    """
    Description: all click button operation need to have authority parameters. This function add authority parameters to query_condition.
    Parameters format:
    ### query_condition: {key1:value1,key2:,value2}
    Example:
    ### query_condition = add_authority_parameters({'ip':'10.1.1.192','port':'3306')}
    ### query_condition is {'ip':'10.1.1.192','port':'3306','code':app.config['USER_CODE'],...}
    """
    if (not query_condition) or (not isinstance(query_condition, dict)):
        query_condition = {}
    try:
        query_condition['code'] = app.config['USER_CODE']
        query_condition['realname'] = flask.session['CAS_NAME']
        query_condition['username'] = flask.session['CAS_USERNAME']
        query_condition['userid'] = flask.session['CAS_NUMBER']
        return query_condition
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')

def get_parameters_from_url(request_url=request,query_key=None):
    """
    Description: get parameters from url.
    Parameters format:
    ### query_key: [key1,key2,key3]
    Example:
    ### url: http://portal.dba.dp/standbylist?cpu=16&ram_size=24GB
    ### ret_val = get_parameters_from_url(['idc','cpu','ram_size'])
    ### ret_val is {'cpu':'16','ram_size':'24GB'}
    """
    query_condition = dict()
    for key in query_key:
        request_value = request_url.values.get(key, False)
        if request_value:
            query_condition[key] = request_value
        # else:
        #     query_condition[key] = ''
    return query_condition

def parse_comment_string(comment_string):
    """
    Description: get needed value from string.
    Parameters format:
    ### comment_string: 'key1:value1,key2:,value2'
    ### key: 'key1'
    Example:
    ### comment = parse_comment_string('name:Lily,gender:F')
    ### comment is {'name':'Lily','gender':'F'}
    """
    comment_dict = {}
    if not comment_string:
        return comment_dict
    infoes = comment_string.split(',')
    for info in infoes:
        pattern = re.compile(r'^(?P<key>\w+)\:(?P<value>.*)$')
        tmp = pattern.match(info)
        if tmp:
            comment_dict[tmp.group('key')] = tmp.group('value')
    return comment_dict

def get_value_from_string(info_string, query_key):
    """
    Description: get needed value from string.
    Parameters format:
    ### info_string: 'key1:value1,key2:,value2'
    ### key: 'key1'
    Example:
    ### gender = get_value_from_string('name:Lily,gender:F','gender')
    ### gender is 'F'
    """
    if not (info_string and query_key):
        return ''
    infoes = info_string.split(',')
    for info in infoes:
        pattern = re.compile(r'^(?P<key>\w+)\:(?P<value>.*)$')
        tmp = pattern.match(info)
        if tmp and tmp.group('key') == query_key:
            return tmp.group('value')
    return ''

def is_recently_time(input_time, days=1):
    """
    Description: judge whether input_time is recently time.
    Parameters format:
    ### input_time: '2015-03-05 01:02:03'
    ### days: 2
    Example:
    ### is_recently_time('2015-03-05 01:02:03', days=1)
    ### return Flase
    """
    if not input_time:
        return False
    input_time = datetime.datetime.strptime(input_time, "%Y-%m-%d %H:%M:%S")
    now = datetime.datetime.now()
    recently_time = now - datetime.timedelta(days=days)
    return True if recently_time < input_time else False

def byte2humanread(byte):
    """
    Description: translate byte into human read size(MB,GB,TB)
    Parameters format:
    ### byte: 1048576
    Example:
    ### byte2humanread(1048576)
    ### return '1M'
    """
    try:
        byte = int(byte)
    except:
        raise Exception('please pass a int into function!')

    suffix_array = ['B','KB','MB','GB','TB','PB']
    i = 0
    byte = float(byte)
    while byte >= 1024 and i < len(suffix_array):
        byte /= 1024
        i += 1
    byte = "%.2f" % byte
    humanread = str(byte) + suffix_array[i]
    return humanread

def ignore_overflow_buss(buss):
    """
    Description: ignore overflow bussiness unit and reserve only one bu.
    Parameters buss:
    ### byte: 平台技术中心
    Example:
    ### ignore_overflow_buss('平台技术中心,新业务与企业发展,推广结婚亲子家装')
    ### return '平台技术中心...'
    """
    if buss is None or type(buss) is not unicode:
        print 'please pass buss name into the function!'
        return ''
    busses = buss.split(',')
    if len(busses) > 1:
        return busses[0] + '...'
    return busses[0]

def check_date(date):
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

###################################
# form function part
###################################
def fill_init_server_form(server_form=None, mirror=''):
    server_list = ServerList()
    mirror_list = server_list.list_supported_mirror()
    mirror_list = zip(mirror_list, mirror_list)
    server_form.mirror.choices = mirror_list

    if not mirror: mirror = ''
    server_form.mirror.data = mirror
    return server_form

def fill_apply_server_form(server_form=None, ip=''):
    server_list = ServerList()

    bu_list = server_list.list_supported_bu()
    type_list = server_list.list_supported_type()
    dba_owner_list = server_list.list_supported_dba()
    server_form.bu.choices = bu_list
    server_form.type.choices = zip(type_list,type_list)
    server_form.dba_owner.choices = dba_owner_list
    #server_form.type.choices = zip(['mysql','mongodb','redis','memcached'],['mysql','mongodb','redis','memcached'])

    if not ip: ip = ''
    server_form.ip.data = ip
    return server_form

def fill_install_db_form(server_form=None, db_type=None, instance=None, comment=None):
    server_list = ServerList()
    owner_list = server_list.list_supported_dba()
    biz_list = server_list.list_supported_biz()
    if comment.has_key('bu') and comment['bu']:
        biz_li = get_product(comment['bu'])
        if biz_li:
            biz_li = json.loads(biz_li)
        biz_list = zip(biz_li,biz_li)

    server_form.dba_owner.choices = owner_list
    server_form.buss.choices = biz_list
    server_form.backup.data = 'y'
    server_form.zabbix.data = 'y'
    server_form.version.choices = server_list.list_supported_db_version(db_type)
    server_form.port.choices = server_list.list_supported_db_port(db_type, instance)
    return server_form

def fill_server_info_form(server_form=None, idc='', logic_cpu_count='', ram_size=''):
    server_list = ServerList()

    idc_list = server_list.list_supported_idc()
    cpu_list = server_list.list_supported_cpu()
    ram_size_list = server_list.list_supported_ram_size()

    server_form.idc.choices = idc_list
    server_form.logic_cpu_count.choices = cpu_list
    server_form.ram_size.choices = ram_size_list

    if not idc: idc = ''
    if not logic_cpu_count: logic_cpu_count = ''
    if not ram_size: ram_size = ''

    server_form.idc.data = idc
    server_form.logic_cpu_count.data = logic_cpu_count
    server_form.ram_size.data = ram_size

    return server_form

def fill_standby_server_info_form(server_form=None, idc='', cpu='', ram_size=''):
    server_list = ServerList()

    idc_list = server_list.list_supported_idc()
    cpu_list = server_list.list_supported_cpu()
    ram_size_list = server_list.list_supported_ram_size()

    server_form.idc.choices = idc_list
    server_form.cpu.choices = cpu_list
    server_form.ram_size.choices = ram_size_list

    if not idc: idc = ''
    if not cpu: cpu = ''
    if not ram_size: ram_size = ''

    server_form.idc.data = idc
    server_form.cpu.data = cpu
    server_form.ram_size.data = ram_size

    return server_form

def fill_inst_info_form(server_form=None, type='', status='', dba_owner='', cluster_name=''):
    instance_list = InstanceList()

    type_list = instance_list.list_supported_type()
    status_list = instance_list.list_supported_status()
    dba_owner_list = instance_list.list_supported_dba()
    cluster_name_list = instance_list.list_supported_cluster()
    #cluster_name_list = [('', ''), (u'alone', u'alone')]
    server_form.type.choices = type_list
    server_form.status.choices = status_list
    server_form.dba_owner.choices = dba_owner_list
    server_form.cluster_name.choices = cluster_name_list

    server_form.type.data = type
    server_form.status.data = status
    server_form.dba_owner.data = dba_owner
    server_form.cluster_name.data = cluster_name
    return server_form

def fill_backup_form(buss=[],ip=[],port=[],type=['MySQL','MongoDB']):
    backup_form = BackupForm()

    backup_form.buss.choices = zip(buss,buss)
    backup_form.ip.choices = zip(ip,ip)
    backup_form.port.choices = zip(port,port)
    backup_form.type.choices = zip(type,type)

    backup_form.buss.data = buss[0] if buss else ''
    backup_form.ip.data = ip[0] if ip else ''
    backup_form.port.data = port[0] if port else ''
    backup_form.type.data = type[0] if type else ''
    return backup_form


###################################
# function in server module
###################################

@app.route("/operate_server/<operate_type>/<server_id>")
def operate_server(operate_type=None,server_id=None):
    """
    Description: operate server.
    Parameters format:
    ### operate_type: offline,online,delete
    ### server_id: server_id
    Example:
    ### portal.dba.dp//operate_server/offline/2102310QPD10F1003373
    """
    if not have_accessed():
        return redirect(url_for('login'))
    try:
        if not (server_id and operate_type):
            flash('请选择服务器,请选择操作类型', 'danger')
            return redirect(url_for('server_list'))
        server_list = ServerList()
        query_result = None

        if operate_type == 'offline':
            query_result = server_list.offline_by_id(server_id)
            flash('服务器异步下线成功...请勿再次下线相同机器！', 'success')
        elif operate_type == 'online':
            query_result = server_list.online_by_id(server_id)
            flash('服务器异步上线成功...请勿再次上线相同机器！', 'success')
        elif operate_type == 'delete':
            query_result = server_list.delete_by_id(server_id)
            flash('服务器异步删除成功...请勿再次删除相同机器！', 'success')
        return redirect(url_for('server_list'))
    except CmdbApiCallException, e:
        flash(e.detail_msg(), 'danger')
        return render_template('blank.html')
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')

@app.route("/serverinfo/<server_id>")
def server_info(server_id=None):
    if not have_accessed():
        return redirect(url_for('login'))

    try:
        data = dict({'page_data': dict()})
        server_list = ServerList()
        data['page_data']['server_id'] = server_id

        single_server_info = dict()
        query_result = server_list.machine_info_by_id(server_id)
        if not query_result:
            machine_info = dict()
            query_result = server_list.info_by_id(server_id)

        if len(query_result) > 0:
            machine_info = query_result[0]
            data['page_data']['machine_info'] = machine_info
            data['page_name'] = 'Server Info'
            data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
            return render_template('serverinfo.html', data=data)
        else:
            flash('server_id not exist', 'danger')
            return render_template('blank.html')
    except CmdbApiCallException, e:
        flash(e.detail_msg(), 'danger')
        return render_template('blank.html')
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')

@app.route("/initsystem/<server_id>", methods=['GET', 'POST'])
def init_system(server_id=None):
    if not have_accessed():
        return redirect(url_for('login'))

    try:
        if request.method == 'POST':
            supported_query_key = ['server_id', 'server_ip', 'mirror', 'comment']
            query_condition = get_parameters_from_url(request,supported_query_key)
            server_list = ServerList()
            result = server_list.init_system_with_mirror(query_condition)
            flash('System initial request sent', 'success')
        else:
            if not server_id or server_id == 0:
                page_data = ''

        page_data = server_list.info_by_id(server_id)[0]
        server_form = ServerInitForm()
        if request.form.get('mirror', False):
            server_form = fill_init_server_form(server_form, request.form.get('mirror', ''))
        else:
            server_form = fill_init_server_form(server_form, mirror=page_data['mirror'])
        data['page_name'] = 'Server Info'
        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
        data['form'] = server_form
        data['page_data'] = page_data
        return render_template('init_system.html', data=data)
    except CmdbApiCallException, e:
        flash(e.detail_msg(), 'danger')
        app.logger.error(str(e))
        return render_template('blank.html')
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')

@app.route("/serverinfoedit/<server_id>", methods=['GET', 'POST'])
def server_info_edit(server_id=None):
    if not have_accessed():
        return redirect(url_for('login'))
 
    try:
        data = dict()
        server_list = ServerList()
        if request.method == 'POST':
            page_data = request.form
            server_list.save_server_info(page_data)
            flash('Edit Server Information Success', 'success')
        else:
            if not server_id or server_id == 0:
                page_data = ''
            else:
                page_data = server_list.info_by_id(server_id)[0]

        server_form = ServerInfoForm()
        supported_select_key = ['owner', 'mirror', 'server_status', 'env']
        fill_select_data = dict()
        for key in supported_select_key:
            fill_select_data[key] = page_data[key]
        server_form = fill_server_info_form(server_form=server_form, **fill_select_data)
        data['page_name'] = 'Server Info'
        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
        data['form'] = server_form
        data['page_data'] = page_data
        return render_template('serverinfoedit.html', data=data)
    except CmdbApiCallException, e:
        flash(e.detail_msg(), 'danger')
        app.logger.error(str(e))
        return render_template('blank.html')
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')

    return render_template('servermodify.html')

@app.route("/standbylist")
def standby_list():
    if not have_accessed():
        return redirect(url_for('login'))

    try:
        data = dict()
        supported_query_key = ['idc', 'cpu', 'ram_size']
        query_condition = get_parameters_from_url(request,supported_query_key)

        #dba_portal_redis = DBAPortalRedis()
        #server_available = dba_portal_redis.get_json('server_available')
        server_list = ServerList()
        server_available = None
        if not server_available:
            server_available = server_list.list_available()
            #dba_portal_redis.set_json_with_expire('server_available', server_available, dba_portal_redis._expire_server_available)

        page_data = server_available
        filter_form = StandbyServerInfoForm()
        filter_form = fill_standby_server_info_form(server_form=filter_form, **query_condition)

        message_list = ({'from': 'admin', 'time': '2013-01-01', 'content': 'This is a test message'},)
        task_list = ({'name': 'task 1', 'progress': 10},)
        data['message_list'] = message_list
        data['task_list'] = task_list
        data['page_name'] = '待用服务器列表'
        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
        data['user_priv'] = flask.session['USER_PRIV'] if flask.session and flask.session['USER_PRIV'] else ''
        data['page_data'] = page_data
        data['filter_form'] = filter_form
        #flash(json.dumps(page_data),'danger')
        return render_template('standbylist.html', data=data)
    except CmdbApiCallException, e:
        flash(e.detail_msg(), 'danger')
        app.logger.error(str(e))
        return render_template('blank.html')
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        app.logger.error(str(e))
        return render_template('blank.html')

@app.route("/server_list")
def server_list():
    if not have_accessed():
        return redirect(url_for('login'))
    try:
        supported_query_key = ['ram_size', 'idc', 'logic_cpu_count']
        query_condition = get_parameters_from_url(request,supported_query_key)

        dba_portal_redis = DBAPortalRedis()
        server_list = ServerList()
        server_all = dba_portal_redis.get_json('server_all')
        if not server_all:
            server_all = server_list.list_all()
            dba_portal_redis.set_json_with_expire('server_all', server_all, dba_portal_redis._expire_server_all)

        instance_list = InstanceList()
        instance_all = dba_portal_redis.get_json('instance_all')
        if not instance_all:
            instance_all = instance_list.list_all()
            dba_portal_redis.set_json_with_expire('instance_all', instance_all, dba_portal_redis._expire_instance_all)
        instances = [instance['server_ip'] for instance in instance_all]

        #filtered_servers = all_servers.list_all(data=query_condition)
        filtered_servers = server_all
        page_data={}
        have_instance = []
        no_instance = []
        recently_apply = []
        for server in filtered_servers:
            dba_owner = get_value_from_string(server['comment'],'dba')
            server['dba_owner'] = dba_owner
            apply_server_time = get_value_from_string(server['comment'],'apply_time')
            if apply_server_time and is_recently_time(apply_server_time, days=7):
                server['recently_apply'] = 1
                server['offline_warning'] = "此机器刚申请，是否强制下线？"
                server['force'] = True
                recently_apply.append(server)
            else:
                server['recently_apply'] = 0
                server['offline_warning'] = "确认下线？"
                server['force'] = False
            if server['private_ip'] in instances:
                server['in'] = 0
                have_instance.append(server)
            else:
                server['in'] = 1
                no_instance.append(server)

        for server_type in ['have_instance','no_instance','recently_apply']:
            page_data[server_type] = eval(server_type)

        if 'count' in query_condition:
            query_condition.pop('count')

        filter_form = ServerInfoForm()
        filter_form = fill_server_info_form(server_form=filter_form, **query_condition)
        message_list = ({'from': 'admin', 'time': '2013-01-01', 'content': 'This is a test message'},)
        task_list = ({'name': 'task 1', 'progress': 10},)
        data = dict()
        data['message_list'] = message_list
        data['task_list'] = task_list
        data['page_name'] = '服务器列表'
        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
        data['user_priv'] = flask.session['USER_PRIV'] if flask.session and flask.session['USER_PRIV'] else ''
        data['page_data'] = page_data
        data['filter_form'] = filter_form
        #flash(data, 'danger')
        return render_template('server_list.html', data=data)
    except CmdbApiCallException, e:
        flash(e.detail_msg(), 'danger')
        app.logger.error(str(e))
        return render_template('blank.html')
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        flash(msg, 'danger')
        app.logger.error(str(e))
        return render_template('blank.html')

@app.route("/applyserver")
def applyserver():
    if not have_accessed():
        return redirect(url_for('login'))
    try:
        data = dict()
        query_condition = dict()
        all_servers = ServerList()
        request_value = request.args.get('serverid', False)
        if not request_value:
            raise Exception('您还没有选择服务器')

        page_data = all_servers.list_selected_server(data=request_value, api='getuseableserver')
        ips=[]
        comment = []
        for pa in page_data:
            ips+=[pa['ip']]
            comment += ['%s %s %s CPU:%s 内存:%s' % (pa['ip'], pa['idc'], pa['rack_location'], pa['cpu'], pa['ram_size'])]
        comment = '\n'.join(comment)
        ips = ','.join(ips)
        filter_form = ApplyServerForm()
        filter_form = fill_apply_server_form(server_form=filter_form, ip=ips)

        message_list = ({'from': 'admin', 'time': '2013-01-01', 'content': 'This is a test message'},)
        task_list = ({'name': 'task 1', 'progress': 10},)
        data['message_list'] = message_list
        data['task_list'] = task_list
        data['page_name'] = '申请使用服务器'
        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
        if not page_data:
            raise  Exception('您选择的服务器信息有误')
        data['page_data'] = page_data
        data['form'] = filter_form
        data['comment'] = comment
        return render_template('applyserver.html', data=data)
    except CmdbApiCallException, e:
        app.logger.error(str(e))
        flash(e.detail_msg(), 'danger')
        return render_template('blank.html')
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')

@app.route("/applyresult", methods=['GET', 'POST'])
def applyresult():
    if not have_accessed():
        return redirect(url_for('login'))
    try:
        data = dict()
        supported_query_key = ['bu', 'product', 'type','ip','comment','dba_owner']
        query_condition = get_parameters_from_url(request,supported_query_key)

        all_servers = ServerList()
        query_condition = add_authority_parameters(query_condition)
        result = all_servers.getApplyresult(data=query_condition)
        data['result'] = 'success'
        data['info'] = '服务器申请已成功提交，流程单号，请至任务中心查询流程进度。申请信息：' + str(query_condition)
        data['page_name'] = '申请使用服务器'
        data['user_priv'] = flask.session['USER_PRIV'] if flask.session and flask.session['USER_PRIV'] else ''
        return render_template('applyresult.html', data=data)
    except CmdbApiCallException, e:
        app.logger.error(str(e))
        flash(e.detail_msg(), 'danger')
        return render_template('blank.html')
    except Exception, e:
        app.logger.error(str(e))
        msg = "%s: %s" % (type(e).__name__, e.message)
        flash(msg, 'danger')
        return render_template('blank.html')

@app.route("/install/<db_type>")
def install_db(db_type=None):
    if not have_accessed():
        return redirect(url_for('login'))
    if not db_type:
        return redirect(url_for('serverlist'))
    try:
        data = dict()
        query_condition = dict()
        request_value = request.args.get('serverid', False)
        if request_value=='undefined':
            flash("您还没有选择服务器",'danger')
            return server_list()

        server_list = ServerList()
        instance_list = InstanceList()
        page_data = server_list.list_all(data={"private_ip":request_value})
        page_data[0]['serverid'] = request_value
        instance_data = instance_list.list_all(data=dict(server_ip=request_value))
        if len(page_data) < 1:
            flash(json.dumps(page_data),'danger')
            return render_template('blank.html')
        filter_form = InstallDbForm()
        comment=page_data[0].get('comment','')
        if comment== None:
            comment = 'a:b'
        comment = parse_comment_string(comment)
        flash(json.dumps(comment))
        filter_form = fill_install_db_form(server_form=filter_form,db_type=db_type,instance=instance_data,comment=comment)
        message_list = ({'from': 'admin', 'time': '2013-01-01', 'content': 'This is a test message'},)
        task_list = ({'name': 'task 1', 'progress': 10},)
        data['message_list'] = message_list
        data['task_list'] = task_list
        data['page_name'] = '部署%s实例' % db_type
        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
        data['user_priv'] = flask.session['USER_PRIV'] if flask.session and flask.session['USER_PRIV'] else ''
        data['user_code'] = app.config['USER_CODE']
        data['db_type'] = db_type
        if not page_data:
            raise Exception('您选择的服务器信息有误')
        data['page_data'] = page_data
        data['instance_data'] = instance_data
        data['form'] = filter_form
        if db_type == 'mysql':
            return render_template('installmysql.html', data=data)
        elif db_type == 'mongodb':
            return render_template('installmongodb.html', data=data)
        elif db_type == 'memcache':
            return render_template('installmemcache.html', data=data)
    except CmdbApiCallException, e:
        flash(e.detail_msg(), 'danger')
        return render_template('blank.html')
    except Exception, e:
        app.logger.error(str(e))
        msg = "%s: %s" % (type(e).__name__, e.message)
        flash(msg, 'danger')
        return render_template('blank.html')

@app.route("/installresult/<db_type>", methods=['GET', 'POST'])
def install_result(db_type=None):
    if not have_accessed():
        return redirect(url_for('login'))
    if not db_type:
        return redirect(url_for('server_list'))
    try:
        data = dict()
        supported_query_key = ['buss', 'version', 'mem', 'dba_owner', 'comment', 'backup', 'zabbix', 'port','server_ip','server_id','db_type','replSet']
        query_condition = get_parameters_from_url(request,supported_query_key)
        query_condition = add_authority_parameters(query_condition)

        all_servers = ServerList()
        instance = InstanceList()
        result = instance.add_instance(query_condition)
        data['result'] = 'success'
        data['info'] = '已进入安装池！安装信息：'+ json.dumps(query_condition,ensure_ascii=False)
        data['page_name'] = '数据库实例安装'
        data['user_priv'] = flask.session['USER_PRIV'] if flask.session and flask.session['USER_PRIV'] else ''
        return render_template('install_db_result.html', data=data)
    except CmdbApiCallException, e:
        app.logger.error(str(e))
        flash(e.detail_msg(), 'danger')
        return render_template('blank.html')
    except Exception, e:
        app.logger.error(str(e))
        msg = "%s: %s" % (type(e).__name__, e.message)
        flash(msg, 'danger')
        return render_template('blank.html')

@app.route("/addserver/", methods=['GET', 'POST'])
def add_server():
    if not have_accessed():
        return redirect(url_for('login'))
    try:
        server_list = ServerList()
        env = server_list.list_supported_env()
        mirror = server_list.list_supported_mirror()
        use_status = server_list.list_supported_use_status()
        owner = server_list.list_supported_dba()
        status = server_list.list_supported_status()

        server_form = ServerInfoForm()
        server_form.env.choices = env
        server_form.mirror.choices = mirror
        server_form.server_status.choices = status
        server_form.use_status.choices = use_status
        server_form.owner.choices = owner
        data = dict()
        if request.method == 'POST':
            server_post = request.form
            server_info = ServerList()
            result = server_info.add_server(server_post)
            page_data = dict()
            page_data['add_result'] = dict()
            flash('Add Server Success!', 'success')
            return redirect(url_for('server_info', server_id=request.form['server_id']))
            data['form_data'] = server_post
        else:
            page_data = ''
            data['form_data'] = dict()

        data['page_name'] = 'Add Server'
        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
        data['form'] = server_form
        data['page_data'] = page_data
        return render_template('addserver.html', data=data)
    except CmdbApiCallException, e:
        app.logger.error(str(e))
        flash(e.detail_msg(), 'danger')
        return render_template('blank.html')
    except Exception, e:
        app.logger.error(str(e))
        msg = "%s: %s" % (type(e).__name__, e.message)
        flash(msg, 'danger')
        return render_template('blank.html')

@app.route('/get_product/<bu>')
def get_product(bu):
    if not have_accessed():
        return redirect(url_for('login'))

    try:
        #dba_portal_redis = DBAPortalRedis()
        #key = 'product_bu_' + str(hash(bu))
        #product_bu = dba_portal_redis.get_product_bu(key) if dba_portal_redis._redis.exists(key) else ''
        product_bu = ''

        if not product_bu:
            product_bu = []
            url = "http://api.cmdb.dp/api/v0.1/bu/"+bu+"/products"
            rep = requests.get(url).json()
            for re in rep['products']:
                product_bu += [re['product_name']]
            #dba_portal_redis.set_json_with_expire(key, product_bu, 3600*24)
            product_bu = json.dumps(product_bu)
        return product_bu
    except Exception,e:
        app.logger.error(str(e))
        return json.dumps([])

###################################
#instance function part
###################################
@app.route("/instance_list/")
def instance_list():
    if not have_accessed():
        return redirect(url_for('login'))
    try:
        supported_query_key = ['cluster_name', 'dba_owner', 'type', 'status']
        query_condition = get_parameters_from_url(request,supported_query_key)
        all_insts = InstanceList()
        filter_form = InstanceInfoForm()
        filter_form = fill_inst_info_form(server_form=filter_form, **query_condition)
        query_condition['cluster'] = True
        page_data = all_insts.list_all(data=query_condition)
        i=0
        for instance in page_data:
            if instance['cluster_name'] == 'alone':
                page_data[i]['cluster_name'] = ''
            if instance['offline_time'] and is_recently_time(instance['offline_time'], days=3):
                page_data[i]['recently_time'] = True
            else:
                page_data[i]['recently_time'] = False

            if page_data[i]['status'] == '在线':
                page_data[i]['order'] = 4
            elif page_data[i]['status'] is None:
                page_data[i]['order'] = 3
            else:
                if page_data[i]['dba_owner'] == flask.session['CAS_NAME']:
                    page_data[i]['order'] = 0
                elif page_data[i]['status'] == '已初始化':
                    page_data[i]['order'] = 2
                elif page_data[i]['status'] == '下线':
                    page_data[i]['order'] = 1
            i += 1

        data = dict()
        data['page_name'] = 'Instance List'
        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
        data['user_priv'] = flask.session['USER_PRIV'] if flask.session and flask.session['USER_PRIV'] else ''
        data['page_data'] = page_data
        data['filter_form'] = filter_form
        return render_template('instance_list.html', data=data)
    except CmdbApiCallException, e:
        app.logger.error(str(e))
        flash(e.detail_msg(), 'danger')
        return render_template('blank.html')
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')

@app.route("/instanceinfo/<id>")
def instance_info(id=None):
    if not have_accessed():
        return redirect(url_for('login'))
    try:
        data = dict({'page_data': dict()})
        server_list = ServerList()
        instance = InstanceList()

        single_instance_info = dict()
        query_result = instance.info_by_id(id)
        single_instance_info = query_result[0]
        data['page_data']['instance_info'] = single_instance_info

        server_id = single_instance_info['server_id']
        single_server_info = dict()
        query_result = server_list.info_by_id(server_id)
        single_server_info = query_result[0]
        data['page_data']['server_info'] = single_server_info
        data['page_data']['server_info']['server_id'] = server_id

        machine_info = dict()
        query_result = server_list.machine_info_by_id(server_id)
        machine_info = query_result[0]
        data['page_data']['machine_info'] = machine_info

        data['page_name'] = 'Instance Info'
        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
        return render_template('instanceinfo.html', data=data)
    except CmdbApiCallException, e:
        app.logger.error(str(e))
        flash(e.detail_msg(), 'danger')
        return render_template('blank.html')
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')

@app.route("/addinstance/", methods=['GET', 'POST'])
def add_instance():
    if not have_accessed():
        return redirect(url_for('login'))
    try:
        instance_list = InstanceList()
        type_list = instance_list.list_supported_type()
        status_list = instance_list.list_supported_status()
        dba_owner_list = instance_list.list_supported_dba()

        server_form = InstanceInfoForm()
        server_form.type.choices = type_list
        server_form.status.choices = status_list
        server_form.dba_owner.choices = dba_owner_list

        data = dict({'page_data': {}, 'form_data': {}})
        if request.method == 'POST':
            server_post = request.form
            server_info = InstanceList()
            result = server_info.add_instance(server_post)
            page_data = dict()
            page_data['add_result'] = dict()
            flash('Add Server Success!', 'success')
            return redirect(url_for('instance_list'))
            data['form_data'] = server_post
        elif request.method == 'GET':
            server_id = request.args.get('server_id')
            server_list = ServerList()
            server_ip = server_list.get_ip_by_id(server_id)
            data['form_data']['server_id'] = server_id
            data['form_data']['server_ip'] = server_ip
            page_data = ''
        else:
            page_data = ''
        data['page_name'] = 'Add Server'
        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
        data['form'] = server_form
        data['page_data'] = page_data
        return render_template('addinstance.html', data=data)
    except CmdbApiCallException, e:
        flash(e.detail_msg(), 'danger')
        app.logger.error(str(e))
        return render_template('blank.html')
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')

@app.route("/operate_instance/<operate_type>")
def operate_instance(operate_type=None):
    if not have_accessed():
        return redirect(url_for('login'))

    try:
        if not operate_type:
            flash('请选择操作类型', 'danger')
            return redirect(url_for('instance_list'))

        supported_query_key = ['id','ip','port']
        if operate_type == 'offline':
            supported_query_key.append('force')
        query_condition = get_parameters_from_url(request,supported_query_key)
        query_condition = add_authority_parameters(query_condition)

        instance_list = InstanceList()
        if operate_type == 'online':
            instance_list.online_instance(data=query_condition)
        elif operate_type == 'pre_offline':
            instance_list.pre_offline_instance(data=query_condition)
        elif operate_type == 'offline':
            instance_list.offline_instance(data=query_condition)
        flash('%s %s:%s Success' % (operate_type,query_condition['ip'],query_condition['port']), 'danger')
        return redirect('/instance_list')
    except CmdbApiCallException, e:
        app.logger.error(str(e))
        flash(e.detail_msg(), 'danger')
        return render_template('blank.html')
    except Exception, e:
        app.logger.error(str(e))
        msg = "%s: %s" % (type(e).__name__, e.message)
        flash(msg, 'danger')
        return render_template('blank.html')


###################################
# function in cluster module
###################################
@app.route("/schemalist")
def schema_list():
    if not have_accessed():
        return redirect(url_for('login'))
    try:
        message_list = ({'from': 'admin', 'time': '2013-01-01', 'content': 'This is a test message'},)
        task_list = ({'name': 'task 1', 'progress': 10},)

        data = dict()
        data['message_list'] = message_list
        data['task_list'] = task_list
        data['page_name'] = 'ToDo'
        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
        return render_template('schemalist.html', data=data)
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')

@app.route("/cluster_list")
def cluster_list():
    if not have_accessed():
        return redirect(url_for('login'))
    try:
        cluster = Cluster()
        info = cluster.get_cluster_list()
        data = dict()
        if info.has_key('mmm'):
            data['mmm'] = info['mmm']
        data['mha']  =info['mha']
        data['page_name'] = '集群信息'
        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
        return render_template('cluster_list.html', data=data)
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')

@app.route("/test")
def test():
    if not have_accessed():
        return redirect(url_for('login'))
    try:
        message_list = ({'from': 'admin', 'time': '2013-01-01', 'content': 'This is a test message'},)
        task_list = ({'name': 'task 1', 'progress': 10},)
        data = dict()
        data['message_list'] = message_list
        data['task_list'] = task_list
        data['page_name'] = 'test page'
        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
        return render_template('test.html', data=data)
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')


###################################
# function in backup module
###################################

def sort_cluster_by_backup_status(clusters):
    if not clusters:
        return None
    sorted_cluster = {}
    nonbackup = {}
    warningbackup = {}
    goodbackup = {}
    for buss,cluster in clusters.items():
        null_count = 0
        success_count = 0
        other_count = 0
        for ip,server in cluster.items():
            if server['status'] is None:
                null_count += 1
            elif server['status'] == u'成功':
                success_count += 1
            else:
                other_count += 1
            if type(server['port']) is int:
                server['status'] = str(server['status'])

        if success_count == 0 and other_count == 0:
            nonbackup[buss] = cluster
        elif success_count == 1 and other_count == 0:
            goodbackup[buss] = cluster
        else:
            warningbackup[buss] = cluster

    sorted_cluster['nonbackup'] = nonbackup
    sorted_cluster['warningbackup'] = warningbackup
    sorted_cluster['goodbackup'] = goodbackup
    return sorted_cluster


@app.route("/old_backup_center")
def old_backup_center():
    if not have_accessed():
        return redirect(url_for('login'))
    try:
        backup_list = BackupList()
        backup_info = backup_list.mha()
        backup_instance = backup_list.backup_report()

        if not backup_info.has_key('mmm'):
            backup_info['mmm'] = ''
        #mmm = sort_cluster_by_backup_status(backup_info['mmm'])
        mha = sort_cluster_by_backup_status(backup_info['mha'])
        #data = {'mmm':mmm, 'mha':mha}
        data = {'mha':mha}
        data['page_name']="备份中心"
        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
        data['user_priv'] = flask.session['USER_PRIV'] if flask.session and flask.session['USER_PRIV'] else ''
        data['nonbackup']="尚未备份"
        data['warningbackup']="警告备份"
        data['goodbackup']="成功备份"
        return render_template('old_backup_center.html', data=data, data_instance=backup_instance)
    except Exception,e:
        app.logger.error(str(e))
        flash(e,'danger')
        return render_template('blank.html')


@app.route("/set_backup_config, methods=['GET', 'POST']")
def set_backup_config():
    """
    Description: set backukup configure
    Example:
    ### portal.dba.dp//set_backup_config/10.1.1.111/3306
    """

    if not have_accessed():
        return redirect(url_for('login'))
    try:
        if request.method == 'POST':
            supported_query_key = ['server_id', 'server_ip', 'mirror', 'comment']
            query_condition = get_parameters_from_url(request,supported_query_key)
            server_list = ServerList()
            result = server_list.init_system_with_mirror(query_condition)
            flash('System initial request sent', 'success')
        else:
            if not server_id or server_id == 0:
                page_data = ''

        supported_query_key = ['id','ip','time','port']
        query_condition = dict()
        query_condition = get_parameters_from_url(request,supported_query_key)

# query_condition = add_authority_parameters(query_condition)

        # if not query_condition['ip'] or not query_condition['port']:
        #     return redirect('/backup_report')
        # backup_list =BackupList()
        # backup_list.switch_flag(data=query_condition)

        return redirect(url_for('backup_center'))
    except Exception,e:
        app.logger.error(str(e))
        flash(e,'danger')
        return render_template('blank.html')


@app.route("/backup_config/<ip>/<port>")
def backup_config(ip=None, port=None):
    if not have_accessed():
        return redirect(url_for('login'))
    try:
        if not (ip and port):
            flash('缺少IP或端口', 'danger')
            return redirect(url_for('backup_center'))

        backup_list = BackupList()
        backup_configure = backup_list.backup_configure()

        data = {'backup_configure':backup_configure}
        data['page_name']="配置备份参数"
        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
        data['user_priv'] = flask.session['USER_PRIV'] if flask.session and flask.session['USER_PRIV'] else ''
        return render_template('blank.html')
        #return render_template('backup_config.html', data=data)
    except Exception,e:
        app.logger.error(str(e))
        flash(e,'danger')
        return render_template('blank.html')


@app.route("/backup_history", methods=['GET', 'POST'])
def backup_history():
    """
    Description: get backukup history
    Example:
    ### portal.dba.dp/backup_history?buss=zabbix&db_type=mysql
    ### portal.dba.dp/backup_history?ip=10.1.101.125&port=3306
    """

    if not have_accessed():
        return redirect(url_for('login'))
    try:
        supported_query_key = ['buss','db_type','ip','port']
        query_condition = dict()
        query_condition = get_parameters_from_url(request,supported_query_key)
        query_condition = add_authority_parameters(query_condition)
        if not (query_condition['db_type'] and (query_condition['buss'] or
                (query_condition['ip'] and query_condition['port']))):
            flash("parameters error: pass (buss, db_type) or (ip,port,dbtype)", 'danger')
            return redirect('/backup_center')

        backup_list = BackupList()
        backup_history = backup_list.history(query_condition)
        #print backup_history
        return json.dumps(backup_history)
    except Exception,e:
        app.logger.error(str(e))
        flash(e,'danger')
        return render_template('blank.html')


@app.route("/backup_center")
def backup_center():
#    if not have_accessed():
#        return redirect(url_for('login'))
    try:
        backup_list = BackupList()
        #dba_portal_redis = DBAPortalRedis()
        #backup_mha = dba_portal_redis.get_json('backup_mha')
        #backup_single_instance = dba_portal_redis.get_json('backup_single_instance')
        #backup_configure = dba_portal_redis.get_json('backup_configure')
        #backup_mongo = dba_portal_redis.get_json('backup_mongo')
        #backup_history_bu = dba_portal_redis.get_json('backup_history_bu')

        backup_mha = backup_list.mha()
        backup_mongo = backup_list.mongo()
        backup_single_instance = backup_list.single_instance()
        backup_configure = backup_list.configure()
        backup_history_bu = backup_list.history({"buss":"tgtp","dbtype":"mysql"})

        mha = sort_cluster_by_backup_status(backup_mha['mha'])
        mongo = sort_cluster_by_backup_status(backup_mongo['mongo'])
        data = {'mha':mha, 'mongo':mongo}
        data['page_name']="备份中心"
        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
        data['user_priv'] = flask.session['USER_PRIV'] if flask.session and flask.session['USER_PRIV'] else ''
        data['nonbackup']="尚未备份"
        data['warningbackup']="警告备份"
        data['goodbackup']="成功备份"
        return render_template('backup_center.html', data=data, backup_configure=backup_configure, backup_single_instance=backup_single_instance)
    except Exception,e:
        app.logger.error(str(e))
        flash(e,'danger')
        return render_template('blank.html')


def email_backup_format(result, which_page):
    info_sorted = {"MongoDB":[],"MySQL_cluster":[],"MySQL_single":[],"File_Backup":[]}
    for cluster_type in ['MongoDB', 'MySQL_cluster', 'MySQL_single']:
        cluster_info = eval("result['%s']" % cluster_type)
        if cluster_info:
            cluster_info['data_size'] = byte2humanread(cluster_info['data_size'])
            tmp_success = {}
            tmp_failed = {}
            for bu in cluster_info['info']:
                for cluster_name in cluster_info['info'][bu]:
                    if cluster_info['info'][bu][cluster_name]:
                        cluster_info['info'][bu][cluster_name]['backup_size'] = byte2humanread(cluster_info['info'][bu][cluster_name]['backup_size'])
                        if which_page == 'email_backup_report':
                            cluster_info['info'][bu][cluster_name]['buss'] = ignore_overflow_buss(cluster_info['info'][bu][cluster_name]['buss'])
                        if cluster_info['info'][bu][cluster_name]['status'] == "成功":
                            if not tmp_success.has_key(bu):
                                tmp_success[bu] = {}
                            tmp_success[bu][cluster_name] = cluster_info['info'][bu][cluster_name]
                        elif cluster_info['info'][bu][cluster_name]['status'] == "失败":
                            if not tmp_failed.has_key(bu):
                                tmp_failed[bu] = {}
                            tmp_failed[bu][cluster_name] = cluster_info['info'][bu][cluster_name]

            for key in tmp_failed:
                tmp = {key:tmp_failed[key]}
                info_sorted[cluster_type].append(tmp)
            for key in tmp_success:
                tmp = {key:tmp_success[key]}
                info_sorted[cluster_type].append(tmp)

#backup important files
    result['File_Backup']['data_size'] = byte2humanread(result['File_Backup']['data_size'])
    file_backup = result['File_Backup']['info']
    for f_backup in file_backup:
        f_backup['file_size'] = byte2humanread(f_backup['file_size'])
        info_sorted['File_Backup'].append(f_backup)

    result['MongoDB']['info'] = info_sorted['MongoDB']
    result['MySQL_cluster']['info'] = info_sorted['MySQL_cluster']
    result['MySQL_single']['info'] = info_sorted['MySQL_single']
    result['MongoDB']['title'] = 'MongoDB'
    result['MySQL_cluster']['title'] = 'MySQL集群'
    result['MySQL_single']['title'] = 'MySQL单实例'
    result['File_Backup']['info'] = info_sorted['File_Backup']
    result['File_Backup']['title'] = '重要文件'
    return result


@app.route("/backup_report")
def backup_report():
    # if not have_accessed():
    #     return redirect(url_for('login'))
    try:
        active = request.values.get('active','MySQL')

        dba_portal_redis = DBAPortalRedis()
        backup_email_backup_report = dba_portal_redis.get_json('backup_email_backup_report')
        backup_list = BackupList()
        if not backup_email_backup_report:
            backup_email_backup_report = backup_list.email_backup_report()
            dba_portal_redis.set_json_with_expire('backup_email_backup_report',backup_email_backup_report,3600*6)

        for backup_type in ["MySQL_cluster", "MongoDB", "MySQL_single"]:
            if backup_email_backup_report and backup_email_backup_report[backup_type] and backup_email_backup_report[backup_type]['bak_server_infos']:
                backup_email_backup_report[backup_type]['bak_servers'] = []
                backup_email_backup_report[backup_type]['disk_uses'] = []
                for server in backup_email_backup_report[backup_type]['bak_server_infos']:
                    backup_email_backup_report[backup_type]['bak_servers'].append(server)
                    backup_email_backup_report[backup_type]['disk_uses'].append(backup_email_backup_report[backup_type]['bak_server_infos'][server]['disk_use'])

        # for backup_type in ["MySQL_cluster", "MongoDB", "MySQL_single"]:
        #     print backup_type,backup_email_backup_report[backup_type]['bak_servers']
        #     print backup_type,backup_email_backup_report[backup_type]['disk_uses']
        result = backup_email_backup_report
        file_backup = FileBackup()
        result['File_Backup'] = file_backup.get_file_backup_info()
        result['File_Backup']['disk_uses'] = []
        for server in file_backup._file_backup_servers:
            server_use = file_backup.get_latest_server_use(server)
            if server_use:
                result['File_Backup']['disk_uses'].append(server_use['DiskUse'])

        result = email_backup_format(result,'backup_report')
        result['page_name'] = '数据库备份日报'
        result['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
        result['user_priv'] = flask.session['USER_PRIV'] if flask.session and flask.session['USER_PRIV'] else ''
        result['active'] = active

        backup_date = request.args.get('backup_date', False)
        if not (backup_date and check_date(backup_date)):
            backup_date = datetime.date.today()
            backup_date = backup_date.strftime("%Y-%m-%d")
        return render_template('backup_report.html',data=result,backup_date=backup_date)
    except Exception,e:
        app.logger.error(str(e))
        flash(e,'danger')
        return render_template('blank.html')

@app.route("/email_backup_report")
def email_backup_report():
    try:
        active = request.values.get('active','MySQL')
        backup_list = BackupList()
        backup_email_backup_report = backup_list.email_backup_report()
        for backup_type in ["MySQL_cluster", "MongoDB", "MySQL_single"]:
            if backup_email_backup_report and backup_email_backup_report[backup_type] and backup_email_backup_report[backup_type]['bak_server_infos']:
                backup_email_backup_report[backup_type]['bak_servers'] = []
                backup_email_backup_report[backup_type]['disk_uses'] = []
                for server in backup_email_backup_report[backup_type]['bak_server_infos']:
                    backup_email_backup_report[backup_type]['bak_servers'].append(server)
                    backup_email_backup_report[backup_type]['disk_uses'].append(backup_email_backup_report[backup_type]['bak_server_infos'][server]['disk_use'])
        result = backup_email_backup_report
        file_backup = FileBackup()
        result['File_Backup'] = file_backup.get_file_backup_info()
        result['File_Backup']['disk_uses'] = []
        for server in file_backup._file_backup_servers:
            server_use = file_backup.get_latest_server_use(server)
            if server_use:
                result['File_Backup']['disk_uses'].append(server_use['DiskUse'])
        result = email_backup_format(result,'email_backup_report')
        result['page_name'] = '邮件备份报告'
        result['active'] = active
        return render_template('email_backup_report.html',data=result)
    except Exception,e:
        app.logger.error(str(e))
        flash(e,'danger')
        return render_template('blank.html')

@app.route("/del_backup",methods=['POST','GET'])
def del_backup():
    if not have_accessed():
        return redirect(url_for('login'))

    try:
        supported_query_key = ['id','ip','port']
        query_condition = get_parameters_from_url(request,supported_query_key)
        query_condition = add_authority_parameters(query_condition)
        backup_list = BackupList()
        result = backup_list.del_backup(data=query_condition)
        templates = ['backup','backup_report','instance_list']
        template = request.values.get('template','blank')
        template = template if template in templates else 'blank'
        flash(query_condition['ip']+':'+query_condition['port']+' '+result,'danger')
        return redirect('/'+template)
    except CmdbApiCallException, e:
        flash(e.detail_msg(), 'danger')
        return render_template('blank.html')
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')

@app.route('/add_backup',methods=["POST","GET"])
def add_backup():
    if not have_accessed():
        return redirect(url_for('login'))
    try:
        supported_query_key = ['buss','ip','port','type']
        query_condition = get_parameters_from_url(request,supported_query_key)
        if request.values.get('submit',None) == 'submit':
            back_list = BackupList()
            query_condition = add_authority_parameters(query_condition)
            result = back_list.add_backup(query_condition)
            flash(result,'danger')
            return redirect(url_for('backup'))
        else:
            instance = InstanceList()
            query_condition['type'] = 'MySQL'
            query_condition['server_ip'] = query_condition.pop('ip')
            insts = instance.list_all(query_condition)
            buss = []
            ips = []
            ports = []
            types = []
            for inst in insts:
                buss += [inst['buss']]
                ips +=[inst['server_ip']]
                ports +=[inst['port']]
                types +=[inst['type']]
            buss = sorted({}.fromkeys(buss).keys())
            ips = sorted({}.fromkeys(ips).keys())
            ports = sorted({}.fromkeys(ports).keys())
            types = sorted({}.fromkeys(types).keys())
            return json.dumps({'buss':buss,'ips':ips,'ports':ports,'types':types})
            backup_form = fill_backup_form(buss=buss,ip=ips,port=ports,type=types)
            query_condition['page_name'] = '添加备份'
            query_condition['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
            query_condition['backup_form'] = backup_form
            return render_template('addbackup.html',data=query_condition)
    except (CmdbApiCallException, requests.ConnectionError), e:
        app.logger.error(str(e))
        flash(e.message, 'danger')
        return render_template('blank.html')
    except Exception, e:
        app.logger.error(str(e))
        msg = "[%s]: %s" % (type(e).__name__, e.message)
        flash(msg, 'danger')
        return render_template('blank.html')

@app.route('/switch_flag')
def switch_flag():
    if not have_accessed():
        return redirect(url_for('login'))

    try:
        supported_query_key = ['id','ip','time','port']
        query_condition = dict()
        query_condition = get_parameters_from_url(request,supported_query_key)
        query_condition = add_authority_parameters(query_condition)

        if not query_condition['ip'] or not query_condition['port']:
            return redirect('/backup_report')
        backup_list =BackupList()
        backup_list.switch_flag(data=query_condition)
        return redirect('/backup_report')
    except (CmdbApiCallException, requests.ConnectionError), e:
        app.logger.error(str(e))
        flash(e.message, 'danger')
        return render_template('blank.html')
    except Exception, e:
        msg = "[%s]: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')


@app.route("/migration_center")
def migration_center():
    if not have_accessed():
        return redirect(url_for('login'))
    try:
        message_list = ({'from': 'admin', 'time': '2015-08-07', 'content': 'MySQL Recovery And Migration Tool Center '},)
        task_list = ({'name': 'task 1', 'progress': 10},)

        data = dict({'page_name': 'MySQL Migration Center'})
        data['message_list'] = message_list
        data['task_list'] = task_list
        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
        return render_template('migration_center.html', data=data)
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')


@app.route("/metrics")
def metrics():
    if not have_accessed():
        return redirect(url_for('login'))
    try:
        data = dict({'page_name': 'Metrics'})
        return render_template('blank.html', data=data)
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')

@app.route("/slowlog")
def slowlog():
    if not have_accessed():
        return redirect(url_for('login'))
    try:
        data = dict({'page_name': 'Slow Query'})
        return render_template('blank.html', data=data)
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')

###################################
# function in monitor module
###################################
@app.route("/archive917_dashboard",methods=['POST','GET'])
def archive917_dashboard():
#    if not have_accessed():
#        return redirect(url_for('login'))
    try:
        supported_query_key = ['date','monitor_type']
        query_condition = get_parameters_from_url(request,supported_query_key)
        monitor_type = query_condition['monitor_type'] if query_condition.has_key('monitor_type') else 'questions'
        date = query_condition['date'] if query_condition.has_key('date') else '2015-09-17'
        monitor_archive = MonitorArchive()
        rows = monitor_archive.archive_dashboard(date, monitor_type)
        data = {'page_data':rows,'date':date,'monitor_type':monitor_type}
        data['monitor_type_list'] = ["questions","tps","io_util","iops","usr","sys","thds_run","network_out"]
        data['date_list'] = []
        for i in range(10,19): data['date_list'].append('2015-09-' + str(i))
        data['page_name'] = "917核心数据库概览"
#        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
#        data['user_priv'] = flask.session['USER_PRIV'] if flask.session and flask.session['USER_PRIV'] else ''
        return render_template('archive917_dashboard.html', data=data)
    except Exception,e:
        app.logger.error(str(e))
        flash(e,'danger')
        return render_template('blank.html')

@app.route("/archive917_instance",methods=['POST','GET'])
def archive917_instance():
#    if not have_accessed():
#        return redirect(url_for('login'))
    try:
        supported_query_key = ['instance','date','mtype_range']
        query_condition = get_parameters_from_url(request,supported_query_key)
        date = query_condition['date'] if query_condition.has_key('date') else '2015-09-17'
        instance = query_condition['instance'] if query_condition.has_key('instance') else '10.1.125.14'
        mtype_range = query_condition['mtype_range'] if query_condition.has_key('mtype_range') else 'Part'
        monitor_archive = MonitorArchive()
        hcs = monitor_archive.archive_instance(instance, date)
        hcs = json.dumps(hcs)
        mtype_list = monitor_archive.get_mtype_list() if mtype_range == 'All' else ["questions","tps","io_util","iops","usr","sys","thds_run","network_out"]
        data = {'mtype_list':mtype_list,'date':date,'instance':instance,'mtype_range':mtype_range,'mtype_range_list':['All','Part']}
        data['date_list'] = []
        for i in range(10,19): data['date_list'].append('2015-09-' + str(i))
        data['page_name'] = "917核心数据库详细"
#        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
#        data['user_priv'] = flask.session['USER_PRIV'] if flask.session and flask.session['USER_PRIV'] else ''
        return render_template('archive917_instance.html', data=data, hc_configs=hcs)
    except Exception,e:
        app.logger.error(str(e))
        flash(e,'danger')
        return render_template('blank.html')

@app.route("/rtm_dashboard",methods=['POST','GET'])
def rtm_dashboard():
#    if not have_accessed():
#        return redirect(url_for('login'))
    try:
        data = {}
        data['page_name'] = "秒级监控－大盘"
        rtmredis = RTMRedis()
        pipeline = rtmredis._redis.pipeline()
        mtype_threshold = {'io_reads':142557,'io_writes':44236,'iops':300,'diskUsedRatio':90,'io_util':1474914,'diskAvail':1442350}
        data['mtype_threshold'] = json.dumps(mtype_threshold)
        return render_template('rtm_dashboard.html',data=data)
    except Exception,e:
        app.logger.error(str(e))
        flash(e,'danger')
        return render_template('blank.html')

@app.route("/rtm_dashboard_update",methods=['POST','GET'])
def rtm_dashboard_update():
#    if not have_accessed():
#        return redirect(url_for('login'))
    try:
        rtmredis = RTMRedis()
        pipeline = rtmredis._redis.pipeline()
        supported_mtypes = ['io_reads','io_writes','iops','diskUsedRatio','io_util','diskAvail']
        for mtype in supported_mtypes:
            redis_key = 'rtm:dashboard:' + str(mtype)
            pipeline.zrevrange(redis_key,0,11,withscores=True)
        response = pipeline.execute()
        i = 0
        result = {}
        for mtype in supported_mtypes:
            result[mtype] = response[i]
            i += 1
        print result
        return json.dumps(result)
    except Exception,e:
        app.logger.error(str(e))
        return json.dumps([])

@app.route("/rtm_optional",methods=['POST','GET'])
def rtm_optional():
#    if not have_accessed():
#        return redirect(url_for('login'))
    try:
        data = {}
        data['page_name'] = "秒级监控－自选"
        return render_template('rtm_optional.html',data=data)
    except Exception,e:
        app.logger.error(str(e))
        return render_template('blank.html')

# @app.route("/query_monitor",methods=['POST','GET'])
# def query_monitor():
# #    if not have_accessed():
# #        return redirect(url_for('login'))
#     try:
#         supported_query_key = ['type', 'timeRange', 'monitor_range', 'date']
#         query_condition = get_parameters_from_url(request,supported_query_key)
#         monitor_type = query_condition['type'] if query_condition.has_key('type') else ''
#         print query_condition
#         if not monitor_type:
#             monitor_type = "questions"
#         query_condition['type'] = monitor_type

#         product_list = []
#         not_in_cat = ("10.1.110.145")
#         for ip in ("10.1.125.16"):
#             tmp_product = 'db-mysql-' + ip + '-3306'
#             product_list.append(tmp_product)
#         query_condition['product'] = product_list

#         monitor_list = Monitor()
#         hcs = None
#         if query_condition.has_key('monitor_range'):
#             hcs = monitor_list.monitor_all_mha(query_condition)
#         else:
#             hcs = monitor_list.monitor_subclass(query_condition)
#         hc_configs = json.dumps(hcs)
#         tmp_config= ''
#         for key in query_condition:
#             if key != 'timeRange':
#                 tmp_config += (key + '=' + str(query_condition[key]) + '&')
#         data = {'page_data': hcs}
#         if query_condition.has_key('date'):
#             data['date'] = query_condition['date']
#         else:
#             data['date'] = time.strftime('%Y%m%d%H',time.localtime(time.time()))
#         data['page_name'] = "917重点监控"
#         data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''
#         data['user_priv'] = flask.session['USER_PRIV'] if flask.session and flask.session['USER_PRIV'] else ''
#         return render_template('query_monitor.html', data=data, hc_configs=hc_configs, tmp_config=tmp_config)
#     except Exception,e:
#         app.logger.error(str(e))
#         flash(e,'danger')
#         return render_template('blank.html')

@app.route("/flush_cache",methods=['POST','GET'])
def flush_cache():
    if not have_accessed():
        return redirect(url_for('login'))

    try:
        supported_query_key = ['keys', 'page']
        query_condition = get_parameters_from_url(request,supported_query_key)
        #query_condition = add_authority_parameters(query_condition)

        keys = parse_comment_string(query_condition['keys'])
        page = query_condition['page']
        if not page:
            flash("404: Contact handsome, clever, creative dfcao!", 'danger')
            return render_template('blank.html')

        dba_portal_redis = DBAPortalRedis()
        for key in keys:
            if dba_portal_redis._redis.exists(keys[key]):
                dba_portal_redis._redis.delete(keys[key])

        flash("刷新缓存成功", 'success')
        return render_template('blank.html')
    #return redirect(url_for(page))
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')


@app.route("/blank")
def blank():
    try:
        data = dict({'page_name': 'DashBoard'})
        return render_template('blank.html', data=data)
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')

@app.route("/")
def index():
    try:
        return redirect(url_for('login'))
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')


###################################
# function in login logout module
###################################

@app.route("/login")
def login():
    """
    This route has two purposes. First, it is used by the user
    to login. Second, it is used by the CAS to respond with the
    `ticket` after the user logs in successfully.

    When the user accesses this url, they are redirected to the CAS
    to login. If the login was successful, the CAS will respond to this
    route with the ticket in the url. The ticket is then validated.
    If validation was successful the logged in username is saved in
    the user's session under the key `CAS_USERNAME_SESSION_KEY`.
    """

    try:
        app.config.setdefault('CAS_TOKEN_SESSION_KEY', AppConfig.CAS_TOKEN_SESSION_KEY)
        app.config.setdefault('CAS_USERNAME_SESSION_KEY', AppConfig.CAS_USERNAME_SESSION_KEY)
        app.config.setdefault('CAS_LOGIN_ROUTE', AppConfig.CAS_LOGIN_ROUTE)
        app.config.setdefault('CAS_LOGOUT_ROUTE', AppConfig.CAS_LOGOUT_ROUTE)
        app.config.setdefault('CAS_VALIDATE_ROUTE', AppConfig.CAS_VALIDATE_ROUTE)
        app.config.setdefault('CAS_SERVER', AppConfig.CAS_SERVER)
        app.config.setdefault('CAS_AFTER_LOGIN', flask.url_for('archive917_dashboard'))

        cas_token_session_key = current_app.config['CAS_TOKEN_SESSION_KEY']
        redirect_url = create_cas_login_url(
            current_app.config['CAS_SERVER'],
            current_app.config['CAS_LOGIN_ROUTE'],
            flask.url_for('login', _external=True),
            )

        if 'ticket' in flask.request.args:
            flask.session[cas_token_session_key] = flask.request.args['ticket']
        if cas_token_session_key in flask.session:
            if validate(flask.session[cas_token_session_key]):
                redirect_url = current_app.config['CAS_AFTER_LOGIN']
                all_servers = ServerList()
                privilege = all_servers.list_user_privilege(real_name=flask.session['CAS_NAME'],domain_name=flask.session['CAS_USERNAME'])
                flask.session['USER_PRIV'] = privilege
            else:
                del flask.session[cas_token_session_key]

        current_app.logger.debug('Redirecting to: {0}'.format(redirect_url))
        return flask.redirect(redirect_url)
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')


@app.route('/logout')
def logout():
    """
    When the user accesses this route they are logged out.
    """
    try:
        cas_username_session_key = current_app.config['CAS_USERNAME_SESSION_KEY']

        if cas_username_session_key in flask.session:
            del flask.session[cas_username_session_key]

        redirect_url = create_cas_logout_url(
            current_app.config['CAS_SERVER'],
            current_app.config['CAS_LOGOUT_ROUTE'],
            flask.url_for('login', _external=True))

        current_app.logger.debug('Redirecting to: {0}'.format(redirect_url))
        return flask.redirect(redirect_url)
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        app.logger.error(str(e))
        flash(msg, 'danger')
        return render_template('blank.html')

def validate(ticket):
    """
    Will attempt to validate the ticket. If validation fails, then False
    is returned. If validation is successful, then True is returned
    and the validated username is saved in the session under the
    key `CAS_USERNAME_SESSION_KEY`.
    """

    try:
        cas_username_session_key = current_app.config['CAS_USERNAME_SESSION_KEY']
        current_app.logger.debug("validating token {0}".format(ticket))
        cas_validate_url = create_cas_validate_url(
            current_app.config['CAS_SERVER'],
            current_app.config['CAS_VALIDATE_ROUTE'],
            flask.url_for('login', _external=True),
            ticket)
        current_app.logger.debug("Making GET request to {0}".format(cas_validate_url))

        response = urlopen(cas_validate_url).read()
        ticketid = _parse_tag(response, "cas:user")
        strs = [s.strip() for s in ticketid.split('|') if s.strip()]
        if len(strs) == 4:
            username = strs[0]
            number = strs[2]
            name = strs[3]
            isValid = True
        else:
            isValid = False
        #(isValid, username) = urlopen(cas_validate_url).readlines()
        #isValid = True if isValid.strip() == b'yes' else False
        #username = username.strip().decode('utf8', 'ignore')
    except ValueError:
        current_app.logger.error("CAS returned unexpected result")
        isValid = False

    if isValid:
        current_app.logger.debug("valid")
        flask.session[cas_username_session_key] = username
        flask.session['CAS_NAME'] = name
        flask.session['CAS_NUMBER'] = number
    else:
        current_app.logger.debug("invalid")

    return isValid

def _parse_tag(string, tag):
    """
    Used for parsing xml.  Search string for the first occurence of <tag>.....</tag> and return text (stripped
    of leading and tailing whitespace) between tags.  Return "" if tag not found.
    """
    soup = bs4.BeautifulSoup(string)

    if soup.find(tag) is None:
        return ''
    return soup.find(tag).string.strip()

@app.route('/my_workflow')
def my_workflow():
    """
    Display status of servers and instances I applied.
    """
    try:
        user = dict()
        user['realname'] = flask.session['CAS_NAME']
        user['userid'] = flask.session['CAS_NUMBER']
        instances = InstanceList()
        instances_status = instances.my_instance_workflow(user)
        data = dict()
        data['page_data'] = instances_status
        message_list = ({'from': 'admin', 'time': '2013-01-01', 'content': 'This is a test message'},)
        task_list = ({'name': 'task 1', 'progress': 10},)
        data['message_list'] = message_list
        data['task_list'] = task_list
        data['page_name'] = '我发起的流程'
        data['cas_name'] = flask.session['CAS_NAME']
        return render_template('my_workflow.html',data=data)
    except (CmdbApiCallException, requests.ConnectionError), e:
        app.logger.error(str(e))
        flash(e.message, 'danger')
        return render_template('blank.html')
    except Exception, e:
        app.logger.error(str(e))
        msg = "[%s]: %s" % (type(e).__name__, e.message)
        flash(msg, 'danger')
        return render_template('blank.html')


@app.route("/dashboard")
def dashboard():
    if not have_accessed():
        return redirect(url_for('login'))

    try:
        data = dict()
        message_list = ({'from': 'admin', 'time': '2013-01-01', 'content': 'This is a test message'},)
        task_list = ({'name': 'task 1', 'progress': 10},)
        data['message_list'] = message_list
        data['task_list'] = task_list
        data['page_name'] = 'Dash Board'
        data['cas_name'] = flask.session['CAS_NAME'] if flask.session and flask.session['CAS_NAME'] else ''

        dba_portal_redis = DBAPortalRedis()
        server_total_count = dba_portal_redis.get_json('server_total_count')
        instance_total_count = dba_portal_redis.get_json('instance_total_count')
        server_list = ServerList()
        instance_list = InstanceList()
        if not server_total_count:
            server_total_count = server_list.get_total_count()
            dba_portal_redis.set_json_with_expire('server_total_count', server_total_count, dba_portal_redis._expire_server_total_count)
        if not instance_total_count:
            instance_total_count = instance_list.get_total_count()
            dba_portal_redis.set_json_with_expire('instance_total_count', instance_total_count, dba_portal_redis._expire_instance_total_count)

        data['page_data'] = dict()
        data['page_data']['server_cnt'] = server_total_count
        data['page_data']['instance_cnt'] = instance_total_count
        return render_template('dashboard.html', data=data)

    except (CmdbApiCallException, requests.ConnectionError), e:
        app.logger.error(str(e))
        flash(e.message, 'danger')
        return render_template('dashboard.html', data=data)
    except Exception, e:
        app.logger.error(str(e))
        msg = "[%s]: %s" % (type(e).__name__, e.message)
        flash(msg, 'danger')
        return render_template('blank.html')

if __name__ == "__main__":
    dba_portal_redis = DBAPortalRedis()
    #dba_portal_redis.reset_dba_portal_redis()
    app.jinja_env.cache = None
    app.run(host='0.0.0.0', port=AppConfig.PORTAL_PORT, threaded=True)
