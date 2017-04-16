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
   name = "zoj_%010d_%s.html" % (time.time(), suf)
   f = open(name,'w')
   f.write(page)
   f.close()

def print_cookie(cj) :
    for c in cj :
        print c #, cj[c]

class Judge(object):
    """Judge  http://poj.org/ Judger
    """
    __slots__ = ("cj", "opener", "username", "password", "pid", "lang", "src", "last_runid", "status", "last_judge_time", "logined", "runid") # zoj need runid

    SUBMIT_INVALID_LANGUAGE = -2
    SUBMIT_OTHER_ERROR = -1
    SUBMIT_NORMAL = 0

    JudgeInterval = 7 # seconds
    UrlSite = r"http://acm.zju.edu.cn/"
    UrlLogin = r"http://acm.zju.edu.cn/onlinejudge/login.do"
    UrlSubmit = r"http://acm.zju.edu.cn/onlinejudge/submit.do"
    UrlStatus = r"http://acm.zju.edu.cn/onlinejudge/showRuns.do?"
    UrlCeInfo = r"http://acm.zju.edu.cn/onlinejudge/showJudgeComment.do?"

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
        self.logined = False
        self.runid = '0'

    # Login
    def Login(self) :
        self.cj.clear()
        self.logined = False
        data = {
            "handle" : self.username,
            "password" : self.password
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
        if html.find("Handle or password is invalid.") != -1 :
            #wf('login', html)
            logging.error("Login failed! username:" + self.username)
            return False
        self.logined = True
        return True

    def CheckLogin(self) :
        """
        CheckLogin(), and record last_submit_time
        """
        url = Judge.UrlStatus + 'contestId=1&search=true&firstId=-1&lastId=-1&handle=' + self.username
        logging.info("open_url %s" % url)
        req = urllib2.Request(url, headers=Judge.Headers)
        rsp = self.opener.open(req)
        res = None
        if rsp :
            res = rsp.read()
            #wf("CheckLogin_", res)
            result = self.__parse_result(None, res, need_extra_info=False)
            if result and result.has_key('origin_runid') :
                #print "CheckLogin last_submit_time{%s}END" %  result['_submit_time']
                self.last_runid = result['origin_runid']
        return res and res.find(r'<a href="/onlinejudge/login.do">Login</a>') == -1


    # Submit
    def Submit(self, pid, lang, src) :
        self.pid = pid
        submit_data = {
            "problemCode" : pid,
            "languageId" : lang,
            "source" : src,
        }
        headers = copy.copy(Judge.Headers)

        post_data = urllib.urlencode(submit_data)

        logging.info("open_url %s" % Judge.UrlSubmit)
        req = urllib2.Request(Judge.UrlSubmit, data=post_data, headers=headers)
        rsp = self.opener.open(req)
        if not rsp :
            return False
        html = rsp.read()

        if html.find(r"<td>&nbsp;<font color='red'>Submit too fast, please wait a while.</font></td>") != -1 :
            logging.warning("pid:%s lang:%s , Submit too fast, please wait a while." % (pid, lang) )
            j_now = time.time()
            j_diff =  Judge.JudgeInterval - (j_now - self.last_judge_time)

            time.sleep(max(3, j_diff))
            return self.Submit(pid, lang, src)

        if html.find('访问禁止') != -1 and html.find('检测到可疑访问，事件编号') != -1 :
            logging.error("Firewall Deny!!!")
            wf("Submit_Firewall", html)
            raise oj.FirewallDenyOJException('Firewall deny! Please check source code!')
            return Judge.SUBMIT_OTHER_ERROR

        if html.find(r'<div id="content_title">Submit Successfully</div>') == -1 :
            wf("Submit_", html)
            logging.error("Submit failed! not found: \"Submit Successfully</div>\" ");
            return Judge.SUBMIT_OTHER_ERROR

        #ce_m = re.match(".+?<small>(.*?)</small>", html, re.DOTALL)
        m = re.match(".+?The submission id is.*?>(.*?)<", html, re.DOTALL)
        if not m :
            wf("Submit_runid", html)
            return Judge.SUBMIT_OTHER_ERROR
        
        self.runid = m.group(1).strip()
        return Judge.SUBMIT_NORMAL

    @staticmethod
    def IsFinalResult(result) :
        result = result.strip()

        if (len(result) < 6) : return False

        if (result.find("Compilation Error") != -1) : return True
        if (result.find("Segmentation Fault") != -1) : return True
        if (result.find("Time Limit Exceeded") != -1) : return True
        if (result.find("Memory Limit Exceeded") != -1) : return True
        if (result.find("Non-zero Exit Code") != -1) : return True
        if (result.find("Floating Point Error") != -1) : return True
        if (result.find("Output Limit Exceeded") != -1) : return True
        if (result.find("Wrong Answer") != -1) : return True
        if (result.find("Accepted") != -1) : return True
        if (result.find("Presentation Error") != -1) : return True

        return False

    @staticmethod
    def ConvertResult(result) :
        #"""
        #if (result.find("compilation error") != -1) : return (oj.Judge_CE, result)
        if (result.find("Compilation Error") != -1) : return (oj.Judge_CE, "Compilation Error")
        if (result.find("Segmentation Fault") != -1) : return (oj.Judge_RE, "Segmentation Fault")
        if (result.find("Time Limit Exceeded") != -1) : return (oj.Judge_TLE, "Time Limit Exceeded")
        if (result.find("Memory Limit Exceeded") != -1) : return (oj.Judge_MLE, "Memory Limit Exceeded")
        if (result.find("Non-zero Exit Code") != -1) : return (oj.Judge_RE, "Non-zero Exit Code")
        if (result.find("Floating Point Error") != -1) : return (oj.Judge_RE, "Floating Point Error")
        if (result.find("Output Limit Exceeded") != -1) : return (oj.Judge_OLE, "Output Limit Exceeded")
        if (result.find("Wrong Answer") != -1) : return (oj.Judge_WA, "Wrong Answer")
        if (result.find("Accepted") != -1) : return (oj.Judge_AC, "Accepted")
        if (result.find("Presentation Error") != -1) : return (oj.Judge_PE, "Presentation Error")

        if result.find("Running") != -1 or result.find("Waiting") != -1 or result.find("Compiling") != -1 or \
           result.find("running") != -1 or result.find("waiting") != -1 or result.find("compiling") != -1 :
            return (oj.Judge_JG, result)
        #"""
        return (0, result)

    def __extra_info(self, run_id) :
        url = Judge.UrlCeInfo + 'submissionId=' + str(run_id)
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

    def __parse_result(self, runid, html, need_extra_info=True) :
        """
        __parse_result a status page, return the first row, or return None
        """
        ret = {}
        ret['origin_runid'] = runid

        # get first row
        status_m = re.match(".+?(<tr class=\"rowOdd\">.*?</tr>)", html, re.DOTALL)
        if not status_m :
            logging.error("Failed to get status row.")
            return None
        status = status_m.group(1)

        # get result
        result_m = re.match(r'.+?<td class="runId">(\d+)</td>.*?<td class="runJudgeStatus".*?<span.*?>(.*?)</span>.*?<td class="runTime".*?>(.*?)</td>.*<td class="runMemory".*?>(.*?)</td>', status, re.DOTALL)
        if not result_m :
            wf("parse_result_status", status)
            logging.error("Failed to get current result.")
            return None
        ret['origin_runid'] = result_m.group(1).strip()

        if None != runid and runid != ret['origin_runid'] :
            return None

        result = result_m.group(2).strip()
        cvtRes = Judge.ConvertResult(result)
        ret['result_id'] = cvtRes[0]
        ret['result'] = cvtRes[1]

        ret['time'] = str(int(result_m.group(3).strip()))
        ret['memory'] = str(int(result_m.group(4).strip()))

        ret['_is_end'] = Judge.IsFinalResult(result)

        if need_extra_info and oj.Judge_CE == ret['result_id'] :
            ce_m = re.match(r'.+?showJudgeComment\.do\?submissionId=([0-9]*)', status, re.DOTALL) 
            if ce_m :
                ce_id = ce_m.group(1).strip()
                ret['ce_id'] = ce_id
                ret['extra_info'] = self.__extra_info(ce_id)
            else :
                ret['extra_info'] = "No CE ID"

        return ret

    def Result(self, runid, need_extra_info=True) :
        data = {}

        if runid :
            url = Judge.UrlStatus + "contestId=1&idStart=" + runid + "&idEnd=&handle=" + self.username
        else :
            url = Judge.UrlStatus + 'contestId=1&search=true&firstId=-1&lastId=-1&handle=' + self.username

        #print "url Result ", url
        logging.info("open_url %s" % url)
        req = urllib2.Request(url, headers=Judge.Headers)
        rsp = self.opener.open(req)
        if not rsp :
            logging.error("Can't open url %s" % url)
            return None
        page = rsp.read()
        #wf("Result", page)
        result = self.__parse_result(runid, page, need_extra_info=need_extra_info )
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
 
        result = {"result_id":oj.Judge_WT, "result":"VJudge Login", "extra_info":''}
        yield result

        if not self.logined :
            logging.info("Judge CheckLogin pid:{0} language:{1} code_len:{2}".format(pid, lang, len(src)) )
            self.CheckLogin()
            self.logined = False
            if not self.Login() :
                raise oj.LoginFailedException("Vjudge login failed")
                return
            # time.sleep(1)
        else :
            self.logined = True

        if not self.logined :
            logging.info("Judge Login pid:{0} language:{1} code_len:{2}".format(pid, lang, len(src)) )
            if not self.Login() :
                raise oj.LoginFailedException("Vjudge login failed")
                return
            self.logined = True
            time.sleep(0.5)
            result = self.Result(None, need_extra_info=False)
            if result :
                self.last_runid = result['origin_runid']
                logging.info("last_runid : %s" % self.last_runid)

        logging.info("Judge Submit {0} {1} ".format(pid, lang))

        result = {"result_id":oj.Judge_WT, "result":"VJudge Submit 1", "extra_info":''}
        yield result


        jret = self.Submit(pid, lang, src)
        if Judge.SUBMIT_OTHER_ERROR == jret :
            logging.info("Judge Submit Failed! sleep {0}".format(Judge.JudgeInterval))
            # time.sleep(Judge.JudgeInterval)
            #print "Cookie Begin"
            #print_cookie(self.cj)
            #print "Cookie End"
            self.cj.clear()
            self.logined = False
            if not self.Login() :
                logging.error("Login failed!")
                raise oj.LoginFailedException("login failed after submit 1")
                return
            self.logined = True

            result = {"result_id":oj.Judge_WT, "result":"VJudge Submit 2", "extra_info":''}
            yield result

            time.sleep(1)
            jret = self.Submit(pid, lang, src)
            if Judge.SUBMIT_OTHER_ERROR == jret :
                result = {"result_id":oj.Judge_WT, "result":"VJudge Submit 3", "extra_info":''}
                yield result

                logging.warning("Submit error. Assume should sleep for a while, sleeping " + str(Judge.JudgeInterval) + " seconds.")
                time.sleep(Judge.JudgeInterval)
                jret = self.Submit(pid, lang, src)
                if jret != Judge.SUBMIT_NORMAL :
                    raise oj.SubmitFailedException("submit 3 times, but failed")

        if jret != Judge.SUBMIT_NORMAL and jret != Judge.SUBMIT_INVALID_LANGUAGE:
            logging.error("Judge Submit jret:{0}, failed! \n{1} {2} \n{3}\n ".format(jret, pid, lang, src) )
            raise Exception("no Submit")
            return 
        elif jret == Judge.SUBMIT_INVALID_LANGUAGE :
            result = {"_is_end" : True, "result_id": oj.Judge_WT, 
                    "result":"No language for this problem.", 
                    "extra_info":lang}
            yield result
            return

        self.last_judge_time = time.time()

        self.status = "run"
        last_runid = self.last_runid
        result = None
        err_cnt = 0
        try_cnt = 0
        logging.info("Judge Result {0} {1}, last_runid {2} runid {3} ".format(pid, lang, last_runid, self.runid))

        result = {"result_id":oj.Judge_WT, "result":"VJudge Get Result", "extra_info":''}
        yield result

        while True :
            #logging.info("Judge Reulst {0} {1}".format(pid, lang))
            try_cnt += 1
            if try_cnt > 10 :
                break
            try :
                result = self.Result(self.runid)
            except oj.JudgeException as e :
                raise e
            except Exception as e:
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
                        logging.info("not final result! \"" + result['result'] + "\" is not final result!")

            yield result
            if result and ((result['result'].find("Waiting") != -1 or result['result'].find("waiting") != -1)) :
                time.sleep(2)
            else :
                time.sleep(1)
        # end
        self.status = "end"
        if not result :
            raise oj.JudgeException("no Result")
        yield result
        return

