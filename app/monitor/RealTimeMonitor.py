# coding: utf8
import requests,json
import sys,time,re,datetime,os,random
import redis
from flask import Flask, request

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
        supported_query_key = ['ip']
        query_condition = get_parameters_from_url(request,supported_query_key)
        if query_condition.has_key('ip'):
            print query_condition['ip']
        else:
            print 'error'
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