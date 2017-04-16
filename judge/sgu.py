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
   name = "sgu_%010d_%s.html" % (time.time(), suf)
   f = open(name,'w')
   f.write(page)
   f.close()

def print_cookie(cj) :
    for c in cj :
        print c #, cj[c]

class Judge(object):
    """Judge  http://poj.org/ Judger
    """
    __slots__ = ("cj", "opener", "username", "password", "pid", "lang", "src", "last_runid", "status", "last_judge_time", "logged_in", "runid") # sgu need runid

    JudgeInterval = 31 # seconds
    UrlSite = r"http://acm.sgu.run/"
    UrlLogin = r"http://acm.sgu.ru/login.php"
    UrlSubmit = r"http://acm.sgu.ru/sendfile.php?contest=0"
    UrlStatus = r"http://acm.sgu.ru/status.php?"
    #"http://acm.sgu.ru/status.php?id=" + escapeURL(info->GetUsername()) + "&problem=" + escapeURL(bott->Getvid())
    UrlCeInfo = r"http://acm.sgu.ru/cerror.php?id="

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
        self.opener =urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj), httpHandler)
        self.logged_in = False
        self.runid = '0'

    # Login
    def Login(self) :
        data = {
            "try_user_id" : self.username,
            "try_user_password" : self.password,
            "type_log" : "login"
        }
        logging.info("open_url %s" % Judge.UrlLogin)
        post_data = urllib.urlencode(data)
        req = urllib2.Request(Judge.UrlLogin, data=post_data, headers=Judge.Headers)
        rsp = self.opener.open(req)
        if not rsp :
            return False
        html = rsp.read()
        if html.find("<h4>Wrong ID or PASSWORD</h4>") != -1 :
            logging.error("Login failed! username:" + self.username)
            return False
        return True

    def CheckLogin(self) :
        """
        CheckLogin(), and record last_submit_time
        """
        # "http://acm.sgu.edu.cn/status.php?first=&pid=&user=" + info->GetUsername() + "&lang=&status=0").c_str());
        #url = Judge.UrlStatus + "&pid=&user=" self.username + "&lang=&status=0"
        url = Judge.UrlStatus #+ '&user=zwyzwy&status=12'
        logging.info("open_url %s" % url)
        req = urllib2.Request(url, headers=Judge.Headers)
        for x in xrange(2) :
            rsp = self.opener.open(req)
            html = None
            status_m = None
            ret = False
            if rsp :
                html = rsp.read()
                #wf("CheckLogin_", res)
                found_invalid = (html.find("Connect(0) to MySQL Server failed.") != -1 or \
                    html.find("<b>One or more following ERROR(s) occurred.") != -1 or \
                    html.find("<h2>The requested URL could not be retrieved</h2>") != -1 or \
                    html.find("PHP: Maximum execution time of") != -1 or \
                    html.find("<DIV>Exercise Is Closed Now!</DIV>") != -1 )
                status_m = None
                if not found_invalid :
                    #!RE2::PartialMatch(html, "(?s)<table.*?(<tr align=center.*?</tr>)", &status)) {
                    status_m = re.match(r".+<table.*?(<tr align=center.*?</tr>)", html, re.DOTALL)
                if not status_m :
                    time.sleep(1)
                    continue
                #print rsp.info()
                result = self.__parse_result(html, need_extra_info=False)
                if result and result.has_key('origin_runid') :
                    self.last_runid = result['origin_runid']
                    ret = True
                    break
                else :
                    logging.warning("CheckLogin get last_runid failed!")
        return ret

    # Submit
    def Submit(self, pid, lang, src) :
        # TODO : translate src from GBK to UTF8
        self.pid = pid
        submit_data = {
            "id" : self.username,
            "pass" : self.password,
            "problem" : pid,
            "elang" : lang,
            "source" : src,
        }
        headers = copy.copy(Judge.Headers)

        ref_url = r'http://acm.sgu.ru/index.php'
        headers["Referer"] = ref_url
        headers["Accept"] = "*/*"
        headers["POST"] = ref_url

        post_data = urllib.urlencode(submit_data)

        logging.info("open_url %s" % Judge.UrlSubmit)
        req = urllib2.Request(Judge.UrlSubmit, data=post_data, headers=Judge.Headers)
        #req = urllib2.Request(ref_url, data=post_data, headers=Judge.Headers)
        rsp = self.opener.open(req)
        if not rsp :
            return False
        html = rsp.read()
        #wf("Submit_", page)
        if html.find("Your solution was successfully submitted.") == -1 :
            antispam_str = r"ERROR : You can't send your solution now. Try later (30 seconds). This is antispam protection. Sorry."
            antispam_str_p = r"ERROR : You can't send your solution now. Try later (\d+ seconds). This is antispam protection. Sorry."
            if html.find(antispam_str) != -1 or None != re.match(antispam_str_p, html, re.DOTALL) :
                logging.warning(r'Found antispam_str:"%s", ' % antispam_str)
                return False
            #logging.error("Submit check:\nurl:{0}\n{1}\n{2}\n".format(rsp.geturl(), rsp.info(), html))
            logging.error("Submit check:\nurl:{0}\n{1}\n".format(rsp.geturl(), rsp.info()))
            #wf('submit', html)
            return False

        if html.find('访问禁止') != -1 and html.find('检测到可疑访问，事件编号') != -1 :
            logging.error("Firewall Deny!!!")
            wf("Submit_Firewall", html)
            return False

        return True

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
        if (result.find("Compilation Error") != -1) : return (oj.Judge_CE, result)
        if (result.find("Accepted") != -1) : return (oj.Judge_AC, result)
        if (result.find("Wrong Answer") != -1) : return (oj.Judge_WA, result)
        if (result.find("Wrong answer") != -1) : return (oj.Judge_WA, result)
        if (result.find("wrong answer") != -1) : return (oj.Judge_WA, result)
        if (result.find("Runtime Error") != -1) : return (oj.Judge_RE, result)
        if (result.find("Time Limit Exceeded") != -1) : return (oj.Judge_TLE, result)
        if (result.find("Presentation Error") != -1) : return (oj.Judge_PE, result)
        if (result.find("Memory Limit Exceeded") != -1) : return (oj.Judge_MLE, result)
        if (result.find("Output Limit Exceeded") != -1) : return (oj.Judge_OLE, result)
        
        if result.find("Running") != -1 or result.find("Waiting") != -1 or result.find("Compiling") != -1: 
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
        ce_m = re.match(r".*?<pre>(.*)</pre>", html, re.DOTALL)
        if not ce_m :
            return ""

        ce = ce_m.group(1).replace("<br>", "\n")
        return ce

    def __parse_result(self, html, need_extra_info=True) :
        """
        __parse_result a status page, return the first row, or return None
        """
        ret = {}
        # get first row
        status_m = re.match(r'.*?(<TR class=st1.*?</TR>)', html, re.DOTALL)
        if not status_m :
            #print html
            logging.error("Parse html failed! Failed to get status row.")
            return None
        status = status_m.group(1)
        # get result
        result_m = re.match(r'.*?<TD>([0-9]*?)</TD>.*<TD class=btab>(.*?)</TD>', status, re.DOTALL)
        if not result_m :
            #wf('result_m', status + "\n\nhtml:\n" + html)
            logging.error("Parse result failed! Failed to get current result.")
            return None
        result = result_m.group(2).strip()
        res_font_m = re.match(r'<font.*?>(.*?)</font>', result, re.DOTALL)
        if res_font_m :
            result = res_font_m.group(1).strip()
        ret['origin_runid'] = result_m.group(1)
        ret['result'] = result
        
        cvtRes = Judge.ConvertResult(result)
        ret['result_id'] = cvtRes[0]
        ret['result'] = cvtRes[1]

        #print "ret:", ret
        #raise ""
        if (Judge.IsFinalResult(ret['result'])) :
            # result is the final one, get details
            tm_m = re.match(r'.*?<TD>([0-9]*?)</TD>.*<TD class=btab>(.*?)</TD>.*?<TD>([0-9]*) ms.*?<TD>([0-9]*) kb', status, re.DOTALL)
            # &runid, &result, &time_used, &memory_used
            if not tm_m :
                logging.error("Failed to parse details from status row.")
                return None
            runid = tm_m.group(1)
            result = tm_m.group(2)
            ret['time'] = tm_m.group(3)
            ret['memory'] = tm_m.group(4)
        
        # ret['extra_info'] = self.__extra_info(ret['origin_runid'])
        if True == need_extra_info and ret['result_id'] == oj.Judge_CE :
            extra_info = self.__extra_info( ret['origin_runid'] )
            if extra_info :
                ret['extra_info'] = extra_info
            else :
                ret['extra_info'] = ''
        # print ret
        # raise ""
        return ret

    def Result(self, pid) :
        data = {}

        url = Judge.UrlStatus + 'id=' + self.username
        if pid :
            url += '&problem=' + pid
        #print "url Result ", url
        logging.info("open_url %s" % url)
        req = urllib2.Request(url, headers=Judge.Headers)
        rsp = self.opener.open(req)
        if not rsp :
            logging.error("Can't open url %s" % url)
            return None
        page = rsp.read()
        #wf("Result", page)
        result = self.__parse_result( page )
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
            result = self.Result(None)
            if result :
                self.last_runid = result['origin_runid']
                logging.info("last_runid : %s" % self.last_runid)

        logging.info("Judge Submit {0} {1} ".format(pid, lang))
        
        if not self.Submit(pid, lang, src) :
            logging.info("Judge Submit Failed! sleep {0}".format(Judge.JudgeInterval))
            time.sleep(Judge.JudgeInterval)
            #print "Cookie Begin"
            #print_cookie(self.cj)
            #print "Cookie End"
            self.logged_in = False
            if not self.Login() :
                logging.error("Login failed!")
                return
            self.logged_in = True
            time.sleep(1)
            if not self.Submit(pid, lang, src) :
                logging.error("Judge Submit 2 times, but failed! \n{0} {1} \n{2}\n ".format(pid, lang, src) )
                raise Exception("no Submit")
                return

        self.last_judge_time = time.time()

        self.status = "run"
        last_runid = self.last_runid
        result = None
        err_cnt = 0
        logging.info("Judge Result {0} {1}, last_runid {2} ".format(pid, lang, last_runid))
        while True :
            #logging.info("Judge Reulst {0} {1}".format(pid, lang))
            try :
                result = self.Result(pid)
            except Exception, e:
                err_cnt += 1
                if err_cnt > 3 :
                    raise
                result = None
            if result :
                #print "Judge status ", result
                print time.time(), "Judge Status", result["origin_runid"], last_runid
                print result
                result['_is_end'] = False
                if result.has_key("origin_runid") and result["origin_runid"] > last_runid :
                    #logging.debug(" check submit_time OK! {0} {1}".format(result["origin_runid"], last_runid) )
                    if Judge.IsFinalResult(result['result']) :
                        result['_is_end'] = True
                        self.last_runid = result["origin_runid"]
                        break
                    else :
                        logging.info(result['result'] + " is not final result!")

            yield result
            time.sleep(1)
        # end
        self.status = "end"
        if not result :
            raise Exception("no Result")
        yield result
        return

