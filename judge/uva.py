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
   name = "uva_%010d_%s.html" % (time.time(), suf)
   f = open(name,'w')
   f.write(page)
   f.close()

def print_cookie(cj) :
    print "\nprint_cookie", cj
    for c in cj :
        print c.name, ":", c.value #, ":", cj[c]
    print "print_cookie end.\n"

class Judge(object):
    """Judge  uva Judger
    """
    __slots__ = ("cj", "opener", "username", "password", "pid", "lang", "src", "last_runid", "status", "last_judge_time", "logged_in", "runid", "author_id") # spoj need runid

    SUBMIT_INVALID_LANGUAGE = -2
    SUBMIT_OTHER_ERROR = -1
    SUBMIT_NORMAL = 0

    JudgeInterval = 11 # seconds
    UrlSite = r"https://uva.onlinejudge.org/"
    UrlLogin = r"https://uva.onlinejudge.org/index.php?option=com_comprofiler&task=login"
    UrlSubmit = r"https://uva.onlinejudge.org/index.php?option=com_onlinejudge&Itemid=25&page=save_submission"
    UrlStatus = r"https://uva.onlinejudge.org/index.php?option=com_onlinejudge&Itemid=9"
    UrlCeInfo = r"https://uva.onlinejudge.org/index.php?option=com_onlinejudge&Itemid=9&page=show_compilationerror&submission="

    Headers = { 
        #"Cache-Control" : "max-age=0",
        #"Accept" : r"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        #"Origin" : UrlSite,
        "User-Agent": r"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36",
        "Referer" : "",
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

    def parse_login_hidden_params(self, html) :
        p_m = re.match(r'.+?<form.*?mod_loginform.*?>(.+?)</form>', html, re.DOTALL)
        if not p_m :
            wf("parse_login_params", html)
            logging.error("Failed to get hidden params.")
            return None
        form = p_m.group(1)
        wf("form", form)
        params = ""
        hm = re.compile(r'<input type="hidden" name="(.*?)" value="(.*?)"', re.DOTALL)
        for m in hm.finditer(form) :
            key = m.group(1)
            value = m.group(2)
            #params[key] = value
            params += urllib.quote(key) + '=' + urllib.quote(value) + '&'
        #print params
        return params

    def get_login_hidden_params(self) :
        logging.info("get_login_hidden_params open url %s" % Judge.UrlSite)
        req = urllib2.Request(Judge.UrlSite, headers=Judge.Headers)
        rsp = self.opener.open(req)
        if not rsp :
            return None
        html = rsp.read()
        del rsp
        return self.parse_login_hidden_params(html)
        
    # Login
    def Login(self) :
        user_data = {
            "username" : self.username,
            "passwd" : self.password,
            }
        tail_data = {
            "remember" : "yes",
            "Submit" : "Login"
            }

        params = self.get_login_hidden_params()
        print_cookie(self.cj)
        if not params :
            return False
        cnt = 0
        ref_url = Judge.UrlSite
        while cnt < 2 :
            cnt += 1
            print params
            #data = dict(user_data, **params)
            #data.update(tail_data)
            #print data
            
            logging.info("open_url %s" % Judge.UrlLogin)

            #url_opt = r'option=com_comprofiler&task=login&'
            #post_data = urllib.urlencode(data)
            #post_data = urllib.urlencode(user_data) + '&' + urllib.urlencode(params) + '&' + urllib.urlencode(tail_data)
            #post_data = urllib.urlencode(user_data) + '&' + params + urllib.urlencode(tail_data)
            #post_data = url_opt + urllib.urlencode(user_data) + '&' + params + urllib.urlencode(tail_data)
            post_data = params + urllib.urlencode(user_data) + '&' + urllib.urlencode(tail_data)
            head = copy.copy(Judge.Headers)
            head['Referer'] = ref_url

            print post_data
            login_url = r'https://uva.onlinejudge.org/index.php?option=com_comprofiler&task=login'
            req = urllib2.Request(Judge.UrlLogin, data=post_data, headers=head)
            #req = urllib2.Request(url=login_url, data=post_data)#, headers=head)
            rsp = self.opener.open(req)
            if not rsp :
                return False
            html = rsp.read()
            if html.find("<td>No account yet? ") != -1 or \
                html.find("<div class='error'>") != -1  or \
                html.find("You are not authorized to view this page!") != -1 :
                    wf("Login", html)
                    print_cookie(self.cj)
                    logging.error("Login failed!\n")
                    params = self.parse_login_hidden_params(html)
                    ref_url = Judge.UrlLogin
                    continue

            return True
        return False

    # Submit
    def Submit(self, pid, lang, src) :
        # TODO : translate src from GBK to UTF8
        self.pid = pid
        submit_data = {
            "localid" : pid,
            "language" : lang,
            "code" : src
            }
        headers = copy.copy(Judge.Headers)

        ref_url = r'https://uva.onlinejudge.org/index.php?option=com_onlinejudge&Itemid=8&page=submit_problem'
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
        # check submit status
        if html.find("You have to select a programming language.") != -1 or \
                html.find("The selected problem ID does not exist.") != -1 or \
                html.find("You have to paste or upload some source code.") != -1 or \
                html.find(" You are not authorised to view this resource.") != -1 :
            return Judge.SUBMIT_OTHER_ERROR
        # html has 'Submission received with ID 18177550'
        if html.find("Submission received with ID ") != -1 :
            return Judge.SUBMIT_NORMAL
        return Judge.SUBMIT_OTHER_ERROR

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
        if (result.find("Compilation error") != -1) : return (oj.Judge_CE, "Compilation error");
        if (result.find("Time limit exceeded") != -1) : return (oj.Judge_TLE, result) # "Time Limit Exceed");
        if (result.find("Memory limit exceeded") != -1) : return (oj.Judge_MLE, result) # "Memory Limit Exceed");
        if (result.find("Output limit exceeded") != -1) : return (oj.Judge_OLE, result) # "Output Limit Exceed");
        if (result.find("Wrong answer") != -1) : return (oj.Judge_WA, result) # "Wrong Answer");
        if (result.find("Wrong Answer") != -1) : return (oj.Judge_WA, result) # "Wrong Answer");
        if (result.find("System Error") != -1) : return (oj.Judge_SYSTEM_ERROR, result) 
        if (result.find("System error") != -1) : return (oj.Judge_SYSTEM_ERROR, result) 
        if (result.find("Submission Error") != -1) : return (oj.Judge_SUBMIT_ERROR, result) # "Restricted function")
        if (result.find("Submission error") != -1) : return (oj.Judge_SUBMIT_ERROR, result) # "Restricted function")
        if (result.find("Presentation Error") != -1) : return (oj.Judge_PE, result) # "Restricted function")
        if (result.find("Presentation error") != -1) : return (oj.Judge_PE, result) # "Restricted function")

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
        ce_m = re.match(r'.+?<pre>(.*)</pre>', html, re.DOTALL)
        if ce_m :
            return ce_m.group(1)
        return ""

    def __parse_result(self, html, need_extra_info=True) :
        """
        __parse_result a status page, return the first row, or return None
        """
        ret = {}
        # get first row
        if html.find("<b>One or more following ERROR(s) occurred.") != -1 or \
                html.find("The page is temporarily unavailable") != -1 :
            logging.error('Failed to get status row.')
            return None
        status_m = re.match(r'.+?(<tr class="sectiontableentry1">.*?</tr>)', html, re.DOTALL)
        if not status_m :
            wf("status", html)
            logging.error("Failed to get status row.");
            return None
        status = status_m.group(1)
        # get result
        rr_m = re.match(r'.+?(?s)<td>([0-9]*?)</td>.*?<td>.*?<td>(.*?)</td>', status, re.DOTALL)
        if not rr_m :
            wf("result", status)
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
            # &runid, &result, &time_used, &memory_used
            tm_m = re.match(r'.+?<td>([0-9]*?)</td>.*?<td>.*?<td>(.*?)</td>.*?<td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>',
                                status, re.DOTALL)
            if not tm_m :
                wf("parse_result", status)
                logging.error("Failed to parse details from status row.")
                return None

            print tm_m.group(3).strip(), tm_m.group(4).strip()
            ret['time'] = str(int(float(tm_m.group(3).strip()) * 1000 + 0.001))
            tm_memory = tm_m.group(4).strip()
            if '' != tm_memory :
                ret['memory'] = str(int(tm_memory))
            else :
                ret['memory'] = '0'
        else :
            ret['time'] = '0'
            ret['memory'] = '0'

        if need_extra_info and oj.Judge_CE == ret['result_id'] :
            ret['extra_info'] = self.__extra_info(ret['origin_runid'])
        
        return ret

    def Result(self, need_extra_info=True) :
        data = {}

        url = Judge.UrlStatus

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

    def judge(self, pid, lang, src) :
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
            result = self.Result(False)
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

            self.cj.clear()
            self.logged_in = False
            if not self.Login() :
                logging.error("Login failed!")
                return
            self.logged_in = True
            
            time.sleep(2)
            jret = self.Submit(pid, lang, src)
            if Judge.SUBMIT_OTHER_ERROR == jret :
                logging.warning("Submit error. Assume should sleep for a while, sleeping " + str(Judge.JudgeInterval) + " seconds.")
                result = {"_is_end" : False, "result_id": oj.Judge_WT, 
                    "result":"Submiting..." }
                yield result
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
                result = self.Result()
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

    def Judge(self, pid, lang, src) :
        cnt = 0
        while 1 :
            cnt += 1
            try :
                return self.judge(pid, lang, src)
            except urllib2.URLError as e :
                exc = traceback.format_exc()
                logging.error( exc )
                print(exc)
                if cnt >= 3 :
                    raise e
                continue

