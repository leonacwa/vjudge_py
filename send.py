#!/usr/bin/env python2.7
#coding:utf-8
import socket
import json
import sys

def SendJudge(port, run_id) :
    HOST, PORT = "localhost", port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
        sock.sendall('S'+str(run_id))
    finally:
        sock.close()


if __name__ == "__main__":
    if len(sys.argv) < 2 :
        print "Param Invaild!", sys.argv[0], "oj_name runid1 runid2 ..."
        exit()

    conf_file = sys.argv[1] + '.conf'
    config = None
    with open(conf_file, 'r') as cf :
        config = json.loads(cf.read())

    port = int(config['port'])
    print sys.argv[1], port
    for run_id in sys.argv[2:] :
        print "Send ", run_id
        SendJudge(port, run_id)

