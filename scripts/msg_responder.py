#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Target:   Python 3.6

import os
import sys
import time
import syslog
import datetime

import diskcache as dc
from daemon import Daemon
from nanoservice import Responder

from node_tools import state_data as st

from node_tools.helper_funcs import get_cachedir
from node_tools.msg_queues import handle_announce_msg
from node_tools.msg_queues import valid_announce_msg


pid_file = '/tmp/responder.pid'
stdout = '/tmp/responder.log'
stderr = '/tmp/responder_err.log'

node_q = dc.Deque(directory=get_cachedir('node_queue'))
reg_q = dc.Deque(directory=get_cachedir('reg_queue'))
wait_q = dc.Deque(directory=get_cachedir('wait_queue'))


def timerfunc(func):
    """
    A timer decorator
    """
    def function_timer(*args, **kwargs):
        """
        A nested function for timing other functions
        """
        start = time.process_time()
        value = func(*args, **kwargs)
        end = time.process_time()
        runtime = end - start
        msg = "{func} took {time} seconds to process msg"
        print(msg.format(func=func.__name__,
                         time=runtime))
        return value
    return function_timer


@timerfunc
def echo(msg):
    """
    Process valid node msg/queues, ie, msg must be a valid node ID.
    :param node ID: zerotier node identity
    :return node ID: zerotier node identity
    """
    if valid_announce_msg(msg):
        syslog.syslog(syslog.LOG_INFO, "Got valid msg: {}".format(msg))
        handle_announce_msg(node_q, reg_q, wait_q, msg)
        # print("Echoing message: {}".format(msg))
        return msg
    else:
        syslog.syslog(syslog.LOG_ERROR, "Bad msg recieved!")


# Inherit from Daemon class
class rspDaemon(Daemon):
    # implement run method
    def run(self):

        self.sock_addr = 'ipc:///tmp/service.sock'
        self.tcp_addr = 'tcp://0.0.0.0:9443'

        s = Responder(self.tcp_addr, timeouts=(None, None))
        s.register('echo', echo)
        s.start()


if __name__ == "__main__":

    daemon = rspDaemon(pid_file, stdout=stdout, stderr=stderr, verbose=1)
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            syslog.syslog(syslog.LOG_INFO, "Starting")
            daemon.start()
        elif 'stop' == sys.argv[1]:
            syslog.syslog(syslog.LOG_INFO, "Stopping")
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            syslog.syslog(syslog.LOG_INFO, "Restarting")
            daemon.restart()
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: {} start|stop|restart".format(sys.argv[0]))
        sys.exit(2)
