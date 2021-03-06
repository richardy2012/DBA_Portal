# coding: utf8
import json
import sys,time,re,datetime,os,random
import redis
from flask import Flask, request
sys.path.append("..")
from redispy.redispy import RTMRedis

app = Flask(__name__)

def get_parameters_from_url(request_url=request,query_key=None):
    """
    Description: get parameters from url.
    Parameters format:
    ### query_key: [key1,key2,key3]
    Example:
    ### url: http://portal.dba.dp/standbylist?cpu=16&ram_size=24GB
    ### ret_val = get_parameters_from_url(request, ['idc','cpu','ram_size'])
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


###################################
# router
###################################
@app.route("/dbmon/<instance>", methods=['GET', 'POST'])
def dbmon(instance=None):
    try:
        supported_query_key = ['port','timestamp','io_reads','io_writes','iops','diskUsedRatio','io_util','diskAvail']
        query_condition = get_parameters_from_url(request,supported_query_key)
        if instance and query_condition.has_key('port'):
            rtmredis = RTMRedis()
            pipeline = rtmredis._redis.pipeline()
            instance = instance + ':' + str(query_condition['port'])
            for mtype in query_condition:
                if mtype not in ['port','timestamp']:
                    #print mtype,query_condition[mtype],float(query_condition[mtype])
                    redis_key = 'rtm:dashboard:' + str(mtype)
                    pipeline.zadd(redis_key,float(query_condition[mtype]),instance)
            pipeline.execute()
        else:
            print '%s -- error: should have ip and port!' % time.strftime('%Y-%m-%d %H-%M-%S')
        return 'OK'
    except Exception, e:
        msg = "%s: %s" % (type(e).__name__, e.message)
        print msg
        return 'NOK'


@app.route('/hello/<name>', methods=['GET', 'POST'])
def hello(name=None):
    supported_query_key = ['test']
    query_condition = get_parameters_from_url(request,supported_query_key)
    #test2()
    return 'Hello ' + query_condition['test']

@app.route('/hi')
def hi():
    test2()
    return 'Hi RTM!'

def test2():
    print 'run task (%s)...' % (os.getpid())
    start = time.time()
    time.sleep(10)
    end = time.time()
    print 'Task runs %0.2f seconds.' % (end - start)



if __name__ == "__main__":
    app.run(host='0.0.0.0')
