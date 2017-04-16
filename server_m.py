#!/usr/bin/env python2.7
#coding:utf-8
import threading
import SocketServer
import Queue
import logging
import traceback
import json
import os

from submission_db import SubmissionDB
import judge.oj as oj
import judge.poj as poj
import judge.hrbust as hrbust 
import judge.hdu as hdu 
import judge.sgu as sgu 
import judge.spoj as spoj 
import judge.ural as ural
import judge.uva as uva
import judge.uvalive as uvalive
import judge.zoj as zoj

class SafeSet(object) :
    def __init__(self) :
        self.__lock = threading.Lock()
        self.__s = set()

    def has(self, item) :
        ok = False
        if self.__lock.acquire() :
            ok = item in self.__s
            self.__lock.release()
        return ok

    def add(self, item) :
        h = False
        if self.__lock.acquire() :
            h = item in self.__s
            if not h :
                self.__s.add(item)
            self.__lock.release()
        return (not h)

    def remove(self, item) :
        if self.__lock.acquire() :
            self.__s.remove(item)
            self.__lock.release()

    def size(self) :
        s = 0
        if self.__lock.acquire() :
            s = len(self.__s)
            self.__lock.release()
        return s

# Gobal Data
g_QueueMaxSize = 1000
g_Queue = Queue.Queue(g_QueueMaxSize)
g_WorkerPool = None
g_Set = SafeSet()
# End.

def GetJudgeClass(oj_name) :
    if oj_name == "POJ" :
        return poj.Judge
    elif oj_name == "HRBUST" :
        return hrbust.Judge
    elif oj_name == "HDU" :
        return hdu.Judge
    elif oj_name == "SGU" :
        return sgu.Judge
    elif oj_name == "SPOJ" :
        return spoj.Judge
    elif oj_name == "URAL" :
        return ural.Judge
    elif oj_name == "UVA" :
        return uva.Judge
    elif oj_name == "UVALive" :
        return uvalive.Judge
    elif oj_name == "ZOJ" :
        return zoj.Judge
    else :
        raise NotFoundOJException("Can'nt find " + oj_name)

class JudgeHandle(object) :
    """JudgeHandle, control the jduge thread, pass parameter """
    __slots__ = ("queue", "is_stop", "thread", "name")
    
    def __init__(self, name, queue):
        super(JudgeHandle, self).__init__()
        self.queue = queue
        self.is_stop = False
        self.thread = None
        self.name = name

    def StopAndWait(self, timeout=None) :
        self.is_stop = True
        if not self.queue.full() :
            self.queu.put(None)
        if self.thread and self.thread.isAlive() :
            self.thread.join(timeout)

    def IsAlive(self) :
        if self.thread :
            return self.thread.is_alive()
        return False

def JudgeThread(judge, db, queue, qset, handle) :
    """ JudgeThread, runing until stop"""
    while not handle.is_stop :
        try :
            item = queue.get() #timeout=7)
            if not item :
                break
            data = db.Get(item)
            #print data, "\n"
            try :
                t_result = {"result_id":oj.Judge_WT, "result":"VJudge Queueing", "extra_info":''}
                db.Update(item, t_result)

                result = judge.Judge(data['origin_pid'], data['language'], data['source_code'])
                is_end = False
                for ret in result :
                    if ret :
                        if db.Update(item, ret) :
                            logging.info( "Update Ok! runid:{0}, status:{1}".format(item, ret) )
                        else :
                            logging.error( "Update failed! status:{0}".format(ret) )

                        is_end = ret.has_key('_is_end') and ret['_is_end']
                        if is_end : break

                if not is_end :
                    logging.error("Can't get final result! runid:%d" % int(item))
                    err_result = {"result_id":oj.Judge_JE, "result":"Judge Error(no result)", "extra_info":"Can't get final result!"}
                    db.Update(item, err_result)

            except oj.FirewallDenyOJException as e:
                err_result = {"result_id":oj.Judge_JE, "result":"Judge Error(Firewall Deny)", "extra_info":str(e)}
                db.Update(item, err_result)

            except oj.CodeLengthTooShortException as e:
                err_result = {"result_id":oj.Judge_SUBMIT_ERROR, "result":"code length too short!", "extra_info":str(e)}
                db.Update(item, err_result)

            except oj.CodeLengthTooLongException as e:
                err_result = {"result_id":oj.Judge_SUBMIT_ERROR, "result":"code length too long!", "extra_info":str(e)}
                db.Update(item, err_result)

            except oj.CodeLengthInvalidException as e:
                err_result = {"result_id":oj.Judge_SUBMIT_ERROR, "result":"code length is invalid!", "extra_info":str(e)}
                db.Update(item, err_result)

            except oj.LoginFailedException as e:
                err_result = {"result_id":oj.Judge_JE, "result":"Judge Error(Login Failed)", "extra_info":str(e)}
                db.Update(item, err_result)

            except oj.SubmitFailedException as e:
                err_result = {"result_id":oj.Judge_JE, "result":"Judge Error(Submit Failed)", "extra_info":str(e)}
                db.Update(item, err_result)

            except oj.ResultFailedException as e:
                err_result = {"result_id":oj.Judge_JE, "result":"Judge Error(Result Failed)", "extra_info":str(e)}
                db.Update(item, err_result)

            except oj.ParseResultException as e:
                err_result = {"result_id":oj.Judge_JE, "result":"Judge Error(Get Result Failed)", "extra_info":str(e)}
                db.Update(item, err_result)

            except oj.JudgeException as e:
                err_result = {"result_id":oj.Judge_JE, "result":"Judge Error(Judge)", "extra_info":str(e)}
                db.Update(item, err_result)

            except (Exception, oj.CommonException) as e:
                # judge failed
                logging.error("runid:{0} {1}\n{2}".format( item, e, traceback.format_exc() ))
                #logging.error("Update failed! result_id:{0},Judge_JE:{1}".format(item, e))
                err_result = {"result_id":oj.Judge_JE, "result":"Judge Error(Exception)", "extra_info":str(e)}
                db.Update(item, err_result)

            if item :
                logging.info("Judge run_id:%s end" % item)
                qset.remove(item)

        except Queue.Empty, e :
            logging.warning("Queue.Empty !! {0}, {1}".format(e, traceback.format_exc()))
            continue
        except Exception, e:
            #print traceback.format_exc()
            logging.error("{0}\n{1}".format( e, traceback.format_exc() ))
        finally:
            pass
    logging.info("{0} exit!".format( (handle.name,) ))


class JudgeWorkerPool(object):
    """JudgeWorkerPool, contains many judge thread """
    def __init__(self, config, JudgeClass, queue, qset, db):
        super(JudgeWorkerPool, self).__init__()
        self.config = config
        self.JudgeClass = JudgeClass
        self.db = db
        self.queue = queue
        self.qset = qset
        self.threads = None
    
    def Start(self) :
        """ Start multi judge thread
            Create JudgeThread, 
        """
        if self.threads :
            logging.warning("JudgeWorkerPool.threads not empty!")
            self.Stop()
        self.threads = []
        for cfg in self.config['accounts'] :
            judge = self.JudgeClass(cfg[0], cfg[1])
            handle = JudgeHandle("judge_thread %s" % cfg[0], self.queue)
            handle.thread = threading.Thread(name=handle.name, target=JudgeThread, args=(judge, self.db, self.queue, self.qset, handle))
            handle.thread.daemon  = True # set daemon
            handle.thread.start()
            self.threads.append(handle)
        return True

    def Stop(self) :
        for h in self.threads :
            t.StopAndWait()
        self.threads = None

    def ThreadCount(self) :
        return len(self.threads)

    def AliveThreadCount(self) :
        cnt = 0
        for h in self.threads :
            if h.IsAlive() :
                cnt += 1
        return cnt



def StartJudgeWorker(config, JudgeClass, queue, qset) :
    dcf = config['db']
    db = SubmissionDB(dcf['user'], dcf['password'], dcf['database'], dcf['charset'], dcf['host'], dcf['port'])
    pool = JudgeWorkerPool(config, JudgeClass, queue, qset, db)
    pool.Start()
    return pool

# Server Begin
# 实现一个 Server，除了本身的参数外，还会传入 queue 参数，用于将数据加入队列中
class JudgeTCPHandler(SocketServer.BaseRequestHandler):
    """ received a cmd, and push into queue """

    def insRunId(self, data) :
        try:
            run_id = int(data)
            logging.info( repr(run_id) )
        except Exception as e:
            logging.error( str(e) )
            raise Exception("ERROR! received invalid data:%s" % data)
        try :
            if g_Set.add(run_id) :
                g_Queue.put(run_id, timeout=1)
            else :
                logging.warning("g_Queue has run_id:%s" % run_id)
        except Queue.Full as e :
            try :
                g_Queue.get_nowait()
            except Exception as e:
                raise
            finally :
                g_Queue.put_nowait(run_id)

    def handle(self) :
        data = self.request.recv(32).strip()
        try :
            op = data[0:1]
            id = data[1:]
        except :
            logging.error("server recv invalied data !!! " + data)
            return

        #print self.client_address
        logging.info( "received from {0}:{1}".format(self.client_address, data) )
        print data
        try :
            if op == 'S':
                self.insRunId(id)
            else :
                try :
                    global g_Queue, g_QueueMaxSize
                    thread_count = g_WorkerPool.AliveThreadCount()
                    qs = g_Queue.qsize()
                    ss = g_Set.size()
                    rsp = "%06d%06d%06d%06d" %(thread_count, qs, g_QueueMaxSize, ss - qs)
                    logging.info("%s response:%s" %(op, rsp))
                    #rsp = "%06d%06d%06d" %(4, 100, 1000)
                    self.request.sendall(rsp)
                except Exception, e:
                    logging.error("send response failed! {0}".format(e))

        except Exception, e:
            logging.error( "insert run_id failed! {0}".format(e) )

def RunServer(host, port) :
    logging.info( "Server Run..." )
    server = SocketServer.TCPServer((host, port), JudgeTCPHandler)
    server.allow_reuse_address = True
    server.serve_forever()

# Server End.

def MainServer(config, lof_file) :
    LogFormat = r"%(asctime)s [%(process)d,%(thread)d] %(levelname)s (%(filename)s:%(lineno)d,%(funcName)s):%(message)s"
    logging.basicConfig(level=logging.DEBUG, filemode='a', format=LogFormat, filename=log_file)
    def run() :
        global g_WorkerPool
        judgeClass = GetJudgeClass(config['oj_name'])
        g_WorkerPool = StartJudgeWorker(config, judgeClass, g_Queue, g_Set)
        RunServer(config['host'], config['port'])
    return run

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3 :
        print "arg error!\n", sys.argv[0], "OJ_CONFIG", "OJ_LOG"

    if sys.getdefaultencoding() != 'utf-8' :
        reload(sys)
        sys.setdefaultencoding('utf-8')

    conf = ['oj.conf', 'log' + os.sep + 'oj.log']
    i = 0
    for v in sys.argv[1:] :
        if i >= len(conf) :
            break
        conf[i] = v
        i += 1

    print sys.argv, conf

    conf_file = conf[0]
    log_file = conf[1]
    config = None
    with open(conf_file, 'r') as cf :
        config = json.loads(cf.read())
    
    #print config
    #exit()
    #from lib.daemonize import Daemonize
    #pid = '/tmp/pojvjudge_py.pid'
    main = MainServer(config, log_file)
    main()
    #print pid, main
    #daemon = Daemonize(app="poj judge", pid=pid, action=main, verbose=True, logger=logging)
    #daemon.start()


