#!/usr/bin/env python2.7
#coding:utf-8
# -*- coding: utf-8 -*- 

# Attention: it must run in 2.7 or higher, 3.x isn't tested

import urllib
import urllib2
import cookielib
import copy
import string
import logging
import oj
import time
import traceback 
import re
#traceback.print_exc()

def wf(suf, page) :
   name = "ural_%010d_%s.html" % (time.time(), suf)
   f = open(name,'w')
   f.write(page)
   f.close()

def print_cookie(cj) :
    for c in cj :
        print c #, cj[c]

class Judge(object):
    """Judge  http://poj.org/ Judger
    """
    __slots__ = ("cj", "opener", "username", "password", "pid", "lang", "src", "last_runid", "status", "last_judge_time", "logged_in", "runid", "author_id") # spoj need runid

    SUBMIT_INVALID_LANGUAGE = -2
    SUBMIT_OTHER_ERROR = -1
    SUBMIT_NORMAL = 0

    JudgeInterval = 11 # seconds
    UrlSite = r"http://acm.timus.ru"
    UrlLogin = r"http://acm.timus.ru"
    UrlSubmit = r"http://acm.timus.ru/submit.aspx?space=1"
    UrlStatus = r"http://acm.timus.ru/status.aspx?author="
    UrlCeInfo = r"http://acm.timus.ru/ce.aspx?id="

    Headers = { 
        #"Cache-Control" : "max-age=0",
        "Accept" : r"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        #"Origin" : r"http://poj.org",
        "User-Agent": r"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36",
        "Referer" : UrlSite,
        #"Accept-Language" : "zh-CN,zh;q=0.8,en;q=0.6",
        #"Accept-Encoding" : "deflate,sdch",
    }
    
    # Init
    def __init__(self, username, password) :
        super(Judge, self).__init__()
        self.username = username
        self.password = password
        self.pid = None
        self.last_runid = 0
        self.last_judge_time = 0
        self.status = "end"
        self.cj = cookielib.CookieJar()
        #self.cj = cookielib.LWPCookieJar()
        #self.opener =urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        #httpHandler = urllib2.HTTPHandler(debuglevel=1)
        httpHandler = urllib2.HTTPHandler()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj), httpHandler)
        self.logged_in = False
        self.runid = '0'
        self.author_id = ''
        un_m = re.match("([0-9]*)", username, re.DOTALL)
        if un_m :
            self.author_id = un_m.group(1)

    # Login
    def Login(self) :
        """
        data = {
            "login_user" : self.username,
            "password" : self.password,
            "submit" : "Log+In"
        }
        logging.info("open_url %s" % Judge.UrlLogin)
        post_data = urllib.urlencode(data)
        headers = copy.copy(Judge.Headers)
        headers['Referer'] = Judge.UrlLogin

        req = urllib2.Request(Judge.UrlLogin, data=post_data, headers=headers)
        rsp = self.opener.open(req)
        if not rsp :
            return False
        html = rsp.read()
        if html.find("Authentication failed! <br/><a href=\"/forgot\">") != -1 :
            #wf('login', html)
            logging.error("Login failed! username:" + self.username)
            return False
        """
        return True

    # Submit
    def Submit(self, pid, lang, src) :
        # TODO : translate src from GBK to UTF8
        self.pid = pid
        submit_data = {
            "Action" : 'submit',
            "spaceID" : 1,
            "JudgeID" : self.username,
            "ProblemNum" : pid,
            "Language" : lang,
            "Source" : src
            }
        headers = copy.copy(Judge.Headers)

        ref_url = r'http://www.spoj.com/'
        headers["Referer"] = ref_url

        post_data = urllib.urlencode(submit_data)

        logging.info("open_url %s" % Judge.UrlSubmit)
        req = urllib2.Request(Judge.UrlSubmit, data=post_data, headers=headers)
        #req = urllib2.Request(ref_url, data=post_data, headers=Judge.Headers)
        rsp = self.opener.open(req)
        if not rsp :
            return False
        html = rsp.read()
        #wf("Submit_", page)
        if html.find(r'<TD ALIGN="CENTER" STYLE="padding-bottom:16px; color:Red;">Unknown language</TD>') != -1 :
            return Judge.SUBMIT_INVALID_LANGUAGE
        if (html.find("<H2 CLASS=\"title\">Solutions judgement results</H2>") == -1) :
            wf("submit", html)
            return Judge.SUBMIT_OTHER_ERROR

        if html.find('访问禁止') != -1 and html.find('检测到可疑访问，事件编号') != -1 :
            logging.error("Firewall Deny!!!")
            wf("Submit_Firewall", html)
            return Judge.SUBMIT_OTHER_ERROR

        return Judge.SUBMIT_NORMAL

    @staticmethod
    def IsFinalResult(result) :
        result = result.strip()
        # Minimum length result is "Accept"
        if (len(result) < 6) : return False
        if (result.find("Waiting") != -1) : return False
        if (result.find("waiting") != -1) : return False
        if (result.find("Running") != -1) : return False
        if (result.find("running") != -1) : return False
        if (result.find("Judging") != -1) : return False
        if (result.find("judging") != -1) : return False
        if (result.find("Sent") != -1) : return False
        if (result.find("Queuing") != -1) : return False
        if (result.find("queue") != -1) : return False
        if (result.find("Compiling") != -1) : return False
        if (result.find("compiling") != -1) : return False
        if (result.find("Linking") != -1) : return False
        if (result.find("linking") != -1) : return False
        if (result.find("Received") != -1) : return False
        if (result.find("Pending") != -1) : return False
        if (result.find("pending") != -1) : return False

        return True

    @staticmethod
    def ConvertResult(result) :
        if (result.find("Accepted") != -1) : return (oj.Judge_AC, result) #"Accepted")
        if (result.find("Compilation error") != -1) : return (oj.Judge_CE, "Compile Error");
        if (result.find("Time limit exceeded") != -1) : return (oj.Judge_TLE, result) # "Time Limit Exceed");
        if (result.find("Memory limit exceeded") != -1) : return (oj.Judge_MLE, result) # "Memory Limit Exceed");
        if (result.find("Output limit exceeded") != -1) : return (oj.Judge_OLE, result) # "Output Limit Exceed");
        if (result.find("Wrong answer") != -1) : return (oj.Judge_WA, result) # "Wrong Answer");
        if (result.find("Crash") != -1) : return (oj.Judge_RE, result) # "Runtime Error");
        if (result.find("Restricted function") != -1) : return (oj.Judge_RE, result) # "Restricted function")

        if result.find("Running") != -1 or result.find("Waiting") != -1 or \
                result.find("Compiling") != -1: 
            return (oj.Judge_JG, result)

        return (0, result)

    def __extra_info(self, run_id) :
        # TODO translate html from GBK  UTF8
        url = Judge.UrlCeInfo + str(run_id)
        #print "url __extra_info ", url
        logging.info("open_url %s" % url)
        req = urllib2.Request(url, headers=Judge.Headers)
        rsp = self.opener.open(req)
        if not rsp :
            return None
        html = rsp.read()
        if not html :
            logging.error("Failed to get CE info, use empty one instead. url:%s" % url)
            return ""
        return html

    def __parse_result(self, html, need_extra_info=True) :
        """
        __parse_result a status page, return the first row, or return None
        """
        ret = {}
        # get first row
        status_m = re.match(r'.+?(<TR class="even">.*?</TR>)', html, re.DOTALL)
        if not status_m :
            wf("result", html)
            logging.error("Failed to get status row.");
            return None
        status = status_m.group(1)
        # get result
        rr_m = re.match(r'.+?<TD class="id"><A.*?>([0-9]+)</A>.*<TD class="verdict.*?>(.*?)</TD>', status, re.DOTALL)
        if not rr_m :
            rr_m = re.match(r'.+?<TD class="id">([0-9]+).*<TD class="verdict.*?>(.*?)</TD>', status, re.DOTALL)
        if not rr_m :
            wf("status", status)
            logging.error("Failed to get current result.")
            return None
        ret['origin_runid'] = rr_m.group(1).strip()
        result = rr_m.group(2)
        cvtRes = Judge.ConvertResult(result)
        ret['result_id'] = cvtRes[0]
        ret['result'] = cvtRes[1]
        ret['_is_end'] = Judge.IsFinalResult(result)

        if ret['_is_end'] :
            # result is the final one
            if ret['result_id'] != oj.Judge_CE :
                # no details for CE results
                tm_m = re.match(r'.+?<TD class="id"><A.*?>([0-9]+)</A>.*<TD class="runtime.*?>(.*?)</TD>.*<TD class="memory.*?>(.*?) KB</TD>', \
                        status, re.DOTALL)
                if not tm_m :
                    tm_m = re.match(r'.+?<TD class="id">([0-9]+).*<TD class="runtime.*?>(.*?)</TD>.*<TD class="memory.*?>(.*?) KB</TD>', \
                        status, re.DOTALL)
                if not tm_m :
                    logging.error("Failed to parse details from status row.")
                    wf("status_row", status)
                    return None

                ret['time'] = str(int(float(tm_m.group(2).strip()) * 1000 + 0.001))
                ret['memory'] = str(int(tm_m.group(3).strip()))
            else :
                ret['time'] = '0'
                ret['memory'] = '0'

        if need_extra_info and oj.Judge_CE == ret['result_id'] :
            ret['extra_info'] = self.__extra_info(ret['origin_runid'])
        
        return ret

    def Result(self, author_id, need_extra_info=True) :
        data = {}

        url = Judge.UrlStatus + author_id

        #print "url Result ", url
        logging.info("open_url %s" % url)
        req = urllib2.Request(url, headers=Judge.Headers)
        rsp = self.opener.open(req)
        if not rsp :
            logging.error("Can't open url %s" % url)
            return None
        page = rsp.read()
        #wf("Result", page)
        result = self.__parse_result( page , need_extra_info)
        return result

    def Judge(self, pid, lang, src) :
        """ Judge and Get Result
        """
        j_now = time.time()
        j_diff =  Judge.JudgeInterval - (j_now - self.last_judge_time)
        if j_diff > 0 :
            logging.info("Judge sleep %d seconds" % j_diff)
            result = {"result" : "Wait for %d seconds" % j_diff}
            yield result
            time.sleep(j_diff)
        
        if not self.logged_in :
            logging.info("Judge Login pid:{0} language:{1} code_len:{2}".format(pid, lang, len(src)) )
            if not self.Login() :
                return
            self.logged_in = True
            time.sleep(0.5)
            result = self.Result("", False)
            if result :
                self.last_runid = result['origin_runid']
                logging.info("last_runid : %s" % self.last_runid)
        
        logging.info("Judge Submit {0} {1} ".format(pid, lang))
        
        jret = self.Submit(pid, lang, src)
        if Judge.SUBMIT_OTHER_ERROR == jret :
            logging.info("Judge Submit Failed! sleep {0}".format(Judge.JudgeInterval))
            time.sleep(Judge.JudgeInterval)
            #print "Cookie Begin"
            #print_cookie(self.cj)
            #print "Cookie End"

            # URAL no login action
            """
            self.cj.clear()
            self.logged_in = False
            if not self.Login() :
                logging.error("Login failed!")
                return
            self.logged_in = True
            """
            time.sleep(2)
            jret = self.Submit(pid, lang, src)
            if Judge.SUBMIT_OTHER_ERROR == jret :
                logging.warning("Submit error. Assume should sleep for a while, sleeping " + str(Judge.JudgeInterval) + " seconds.")
                time.sleep(Judge.JudgeInterval)
                jret = self.Submit(pid, lang, src)
                # logging.error("Judge Submit 2 times, but failed! \n{0} {1} \n{2}\n ".format(pid, lang, src) )
                # raise Exception("no Submit")
                # return
        if jret != Judge.SUBMIT_NORMAL and jret != Judge.SUBMIT_INVALID_LANGUAGE:
            logging.error("Judge Submit jret:{0}, failed! \n{1} {2} \n{3}\n ".format(jret, pid, lang, src) )
            raise Exception("no Submit")
            return 
        elif jret == Judge.SUBMIT_INVALID_LANGUAGE :
            result = {"_is_end" : True, "result_id": oj.Judge_RE, 
                    "result":"Unknown language",
                    "extra_info":"lang"}
            yield result
            return

        self.last_judge_time = time.time()

        self.status = "run"
        last_runid = self.last_runid
        result = None
        err_cnt = 0
        try_cnt = 0
        logging.info("Judge Result {0} {1}, last_runid {2} ".format(pid, lang, last_runid))
        while True :
            #logging.info("Judge Reulst {0} {1}".format(pid, lang))
            try_cnt += 1
            if try_cnt > 10 :
                break
            try :
                if try_cnt != 1:
                    time.sleep(5)
                result = self.Result(self.author_id)
            except Exception, e:
                err_cnt += 1
                if err_cnt > 3 :
                    raise
                result = None
            if result :
                #print "Judge status ", result
                print time.time(), "Judge Status", result["origin_runid"], last_runid
                print result
                if result.has_key("origin_runid") and result["origin_runid"] > last_runid :
                    #logging.debug(" check submit_time OK! {0} {1}".format(result["origin_runid"], last_runid) )
                    if Judge.IsFinalResult(result['result']) :
                        self.last_runid = result["origin_runid"]
                        break
                    else :
                        logging.info("not final result!" + result['result'] + " is not final result!")

            yield result
            if result and ((result['result'].find("Waiting") != -1 or result['result'].find("waiting") != -1)) :
                time.sleep(10);
        # end
        self.status = "end"
        if not result :
            raise Exception("no Result")
        yield result
        return

