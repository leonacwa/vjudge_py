#!/usr/bin/env python2.7
#coding:utf-8
from threading import Lock
import datetime
import mysql.connector
import traceback

class SubmissionDB(object):
    """docstring for SubmissionDB"""
    __slots__ = ("lock", "db", "database", "host", "port", "user", "password", "charset")

    # Use mysql.connector.connect() params
    def __init__(self, user, password, database, charset='utf8', host='127.0.0.1', port=3306) :
        """Use mysql.connector.connect() params"""
        super(SubmissionDB, self).__init__()
        
        self.lock = Lock()
        self.database = database
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.charset = charset

        self.db = mysql.connector.connect(user=self.user, password=self.password, database=self.database, charset=self.charset, host=self.host, port=self.port, autocommit=True)
        
    def __del__(self) :
        if self.db != None :
            self.__close()

    def __close(self) :
        """DB Close() """
        self.db.close()
        self.db = None

    def __ping(self) :
        if self.db.is_connected() :
            return True
        else :
            self.db.ping(reconnect=True, attempts=3, delay=3)

    def Get(self, run_id) :
        """Get Submission by run_id"""
        try :
            self.lock.acquire()
            self.__ping()

            cursor = self.db.cursor()
            sql = ("select id, language, source_code, origin_oj, origin_pid, result "
                  "from submission where id='%s' limit 1")
            cursor.execute(sql, (int(run_id),)) # auto escape
            row = dict(zip(cursor.column_names, cursor.fetchone()))
            cursor.close()
            return row
        except Exception, e:
            raise e
        finally:
            self.lock.release()

    def Update(self, run_id, arg) :
        """ Update Submission
            arg : dict()
        """
        try:
            self.lock.acquire()
            if not arg or len(arg) == 0 :
                return False
            self.__ping()

            up = ["origin_runid", "result_id", "result", "time", "memory", "extra_info"]
            cursor = self.db.cursor()
            sql = "update submission set "
            cnt = 0
            data = []
            for k in up :
                if not arg.has_key(k) :
                    continue
                cnt += 1
                data.append( arg[k] )
                uv = "`%s`=%s" % (k, '%s')
                #print uv
                if cnt == 1 :
                    sql = sql + uv
                else :
                    sql = sql + ", " + uv
            if cnt == 0 :
                return False
            sql = sql + " where id=%d" % run_id
            #print "sql:", sql
            #print "data:", data
            cursor.execute(sql, tuple(data)) # auto escape
            #print cursor.statement
            # self.db.commit() # has set autocommit
            cursor.close()
            return True
        except Exception, e:
            #print "Update", e
            raise e
        finally:
            #print cursor.statement
            self.lock.release()


