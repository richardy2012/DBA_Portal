# coding: utf-8

import requests as requests
import json
from monitor_config import MONITOR_API_ADDR


class MonitorApiCallException(Exception):
    def __init__(self, msg='', param=''):
        self.message = msg
        self.param = param

    def detail_msg(self):
        msg = "MONITOR API Error: Message: %s" self.message
        return msg


class MonitorApiBase:
    __api_addr = ""
    __last_error_msg = ''

    def __init__(self, __api_addr=MONITOR_API_ADDR):
        self.__api_addr = __api_addr

    def __call_interface__(self, json_obj=None,timeout=20):
        try:
            #query_obj = {"data": json.dumps(json_obj)} if json_obj else {"data": "{}"}
            json_obj['op'] = 'view'
            json_obj['forceDownload'] = 'json'
            query_obj = {"data": json.dumps(json_obj)}
            fp = requests.get(self.__api_addr, params=query_obj, timeout=timeout)
            if fp.status_code == requests.codes.ok:
                result = fp.json()
                if result:
                    return result
                else:
                    raise MonitorApiCallException(msg="Result from remote api is not a valid json str", param=json.dumps(json_obj))
            else:
                fp.raise_for_status()
        except Exception, e:
            msg = "Fail to call MONITOR service. %s: %s" % (type(e).__name__, e.message)
            raise Exception(msg)
