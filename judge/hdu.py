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
   name = "hdu_%010d_%s.html" % (time.time(), suf)
   f = open(name,'w')
   f.write(page)
   f.close()

def print_cookie(cj) :
    for c in cj :
        print c #, cj[c]

class Judge(object):
    """Judge  http://poj.org/ Judger
    """
    __slots__ = ("cj", "opener", "username", "password", "pid", "lang", "src", "last_runid", "status", "last_judge_time", "logined")

    JudgeInterval = 3 # seconds
    UrlSite = r"http://acm.hdu.edu.cn/"
    UrlLogin = r"http://acm.hdu.edu.cn/userloginex.php?action=login"
    UrlSubmit = r"http://acm.hdu.edu.cn/submit.php?action=submit"
    UrlStatus = r"http://acm.hdu.edu.cn/status.php?first=" #"http://acm.hdu.edu.cn/status.php?first=&pid=" + bott->Getvid() + "&user=" + info->GetUsername() + "&lang=&status=0"
    #"http://acm.hdu.edu.cn/status.php?first=&pid=&user=" + info->GetUsername() + "&lang=&status=0"
    UrlCeInfo = r"http://acm.hdu.edu.cn/viewerror.php?rid="

    Headers = { 
        #"Cache-Control" : "max-age=0",
        "Accept" : r"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        #"Origin" : r"http://poj.org",
        "User-Agent": r"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36",
        "Referer" : UrlSite,
        #"Accept-Language" : "zh-CN,zh;q=0.8,en;q=0.6",
        #"Accept-Encoding" : "deflate,sdch",
    }
    Language = {
        "G++":"0", "GCC":"1", "JAVA":"5", "Pascal":"4", 
        "C#":"6", "C++":"2", "C":"3"
    }
    # EndStatus = ["Accepted", "Presentation Error", "Time Limit Exceeded", 
    #             "Memory Limit Exceeded", "Wrong Answer", "Runtime Error", 
    #             "Output Limit Exceeded", "Compile Error", "Compilation Error", "System Error"]
    # # 不同OJ有不同的状态字符串，但是可以对应到唯一的judge result id
    # StatusCode = {"Accepted":oj.Judge_AC, "Presentation Error":oj.Judge_PE, 
    #         "Time Limit Exceeded":oj.Judge_TLE, "Memory Limit Exceeded":oj.Judge_MLE,
    #         "Wrong Answer":oj.Judge_WA, "Runtime Error":oj.Judge_RE, 
    #         "Output Limit Exceeded":oj.Judge_OLE, "Compile Error" : oj.Judge_CE, "Compilation Error" : oj.Judge_CE, "System Error" : oj.Judge_JE,
    #         "Judging":oj.Judge_JG, "Compiling":oj.Judge_JG, "Linking" : oj.Judge_JG, "Running" : oj.Judge_JG,
    #         "Queuing":oj.Judge_JG}
    # POJ Status Column, Db Column
    # Column = ['RunID','User','Problem','Result','Memory','Time','Language','CodeLength','SubmitTime']
    Column = ['origin_runid', '_username', 'origin_pid', 'result',
                 'memory', 'time', 'display_language', 'source_code_len', '_submit_time']
    
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
        self.logined = False
        #self.cj = cookielib.LWPCookieJar()
        #self.opener =urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        #httpHandler = urllib2.HTTPHandler(debuglevel=1)
        httpHandler = urllib2.HTTPHandler()
        self.opener =urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj), httpHandler)

    # Login
    def Login(self) :
        self.cj.clear()
        self.logined = False
        data = {
            "username" : self.username,
            "userpass" : self.password,
            "login" : "Sign+In",
        }
        logging.info("open_url %s" % Judge.UrlLogin)
        post_data = urllib.urlencode(data)

        headers = copy.copy(Judge.Headers)

        ref_url = Judge.UrlStatus #'http://acm.hdu.edu.cn/'
        headers["Referer"] = ref_url
        #headers["Accept"] = "*/*"
        #headers["POST"] = ref_url

        req = urllib2.Request(Judge.UrlLogin, data=post_data, headers=headers)
        rsp = self.opener.open(req)
        if not rsp :
            logging.error("open url login failed!")
            # raise oj.LoginFailedException("open url login failed!")
            return False
        html = rsp.read()
        if (html.find("No such user or wrong password.") != -1 or \
            html.find("<b>One or more following ERROR(s) occurred.") != -1 or \
            html.find("<h2>The requested URL could not be retrieved</h2>") != -1 or \
            html.find("<H1 style=\"COLOR: #1A5CC8\" align=center>" \
                          "Sign In Your Account</H1>") != -1 or \
            html.find("PHP: Maximum execution time of") != -1) :
            if html.find(r'><a href="/userloginex.php?action=logout" style="text-decoration: none"><img src="/images/signout.png" alt="Sign Out" border=0 height=18 width=18> Sign Out</a>') == -1 :
                wf("login_failed", html)
                return False
        self.logined = True
        return True

    def CheckLogin(self) :
        """
        CheckLogin(), and record last_submit_time
        """
        # "http://acm.hdu.edu.cn/status.php?first=&pid=&user=" + info->GetUsername() + "&lang=&status=0").c_str());
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
        try :
            src_en = src.encode('gbk')
            src = src_en
        except :
            logging.error("Submit src.encode('gbk') failed! use original src")
        
        self.pid = pid
        submit_data = {
            "check" : '0',
            "problemid" : pid,
            "language" : lang,
            "usercode" : src, #src.replace('\r\n', '\n'),
            #"submit" : 'Submit',
            #"encoded" : '0',
            #"reset" : "Reset",
            #"url" : Judge.UrlSubmit
        }
        headers = copy.copy(Judge.Headers)

        ref_url = 'http://acm.hdu.edu.cn/submit.php?pid=' + pid
        headers["Referer"] = ref_url
        #headers["Accept"] = "*/*"

        post_data = urllib.urlencode(submit_data)

        logging.info("open_url %s" % Judge.UrlSubmit)
        req = urllib2.Request(Judge.UrlSubmit, data=post_data, headers=headers) #Judge.Headers)
        #req = urllib2.Request(ref_url, data=post_data, headers=Judge.Headers)
        rsp = self.opener.open(req)
        if not rsp :
            return False
        html = rsp.read()

        if html.find('访问禁止') != -1 and html.find('检测到可疑访问，事件编号') != -1 :
            logging.error("Firewall Deny!!!")
            wf("Submit_Firewall", html)
            raise oj.FirewallDenyOJException('Firewall deny! Please check source code!')
            return False

        #wf("Submit_", page)
        if (html.find("Connect(0) to MySQL Server failed.") !=  -1 or \
            html.find("<b>One or more following ERROR(s) occurred.") !=  -1 or \
            html.find("<h2>The requested URL could not be retrieved</h2>") !=  -1 or \
            html.find("<H1 style=\"COLOR: #1A5CC8\" align=center>"
                          "Sign In Your Account</H1>") !=  -1 or \
            html.find("PHP: Maximum execution time of") !=  -1 or \
            html.find("<DIV>Exercise Is Closed Now!</DIV>") != -1) :
            #logging.error("Submit check:\nurl:{0}\n{1}\n{2}\n".format(rsp.geturl(), rsp.info(), page))
            #logging.error("Submit check:\nurl:{0}\n{1}\n".format(rsp.geturl(), rsp.info())) #, page))
            if html.find(r'<li>Code length is improper! Make sure your code length is longer than') != -1 :
                logging.error("raise oj.CodeLengthInvalidException")
                raise oj.CodeLengthInvalidException("Code length is improper! Make sure your code length is longer than 50 and not exceed 65536 Bytes.")

            wf("submit_failed", html)
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
        if (result.find("Runtime Error") != -1) : return (oj.Judge_RE, result)
        if (result.find("Time Limit Exceeded") != -1) : return (oj.Judge_TLE, result)
        if (result.find("Presentation Error") != -1) : return (oj.Judge_PE, result)
        if (result.find("Memory Limit Exceeded") != -1) : return (oj.Judge_MLE, result)
        if (result.find("Output Limit Exceeded") != -1) : return (oj.Judge_OLE, result)
        
        if result.find("Running") != -1 or result.find("Waiting") != -1 or result.find("Compiling") != -1 \
                or result.find("Queuing") != -1 :
            return (oj.Judge_JG, result)
        
        return (0, result)

    def __extra_info(self, run_id) :
        url = Judge.UrlCeInfo + str(run_id)
        #print "url __extra_info ", url
        logging.info("open_url %s" % url)
        req = urllib2.Request(url, headers=Judge.Headers)
        rsp = self.opener.open(req)
        if not rsp :
            return None
        html = rsp.read()
        try :
            html_en = html.decode('gbk')
            html = html_en#.encode('utf-8')
        except :
            logging.error("__extra_info html.decode('gbk') failed! use original html")
        #if (!RE2::PartialMatch(buffer, "(?s)<pre>(.*?)</pre>", &result)) :
        ce_m = re.match(r".+<pre>(.*?)</pre>", html, re.DOTALL)
        if not ce_m :
            return ""
        return ce_m.group(1)

    def __parse_result(self, html, need_extra_info=True) :
        """
        __parse_result a status page, return the first row, or return None
        """
        #
        ret = {}
        
        # get first row
        found_invalid = (html.find("Connect(0) to MySQL Server failed.") !=  -1 or \
            html.find("<b>One or more following ERROR(s) occurred.") !=  -1 or \
            html.find("<h2>The requested URL could not be retrieved</h2>") !=  -1 or \
            html.find("PHP: Maximum execution time of") !=  -1 or \
             html.find("<H1 style=\"COLOR: #1A5CC8\" align=center>"
                             "Sign In Your Account</H1>") !=  -1 or \
            html.find("<DIV>Exercise Is Closed Now!</DIV>") !=  -1)
        if found_invalid :
            if html.find(r'<li>Code length is improper! Make sure your code length is longer than') != -1 :
                raise oj.CodeLengthInvalidException("Code length is improper! Make sure your code length is longer than 50 and not exceed 65536 Bytes.")

        status_m = None
        if not found_invalid :
            #!RE2::PartialMatch(html, "(?s)<table.*?(<tr align=center.*?</tr>)", &status)) :
            status_m = re.match(r".+<table.*?(</form></td></tr><tr align=center ><td.*?</tr><)", html, re.DOTALL)
        if not status_m :
            return None
        status = status_m.group(1)
        #print status
        # get result
        # if (!RE2::PartialMatch(status, "(?s)<td.*?>([0-9]*)</td>.*?<font.*?>(.*)</font>", &runid, &result))
        result_m = re.match(r"</form></td></tr><tr align=center ><td.*?>([0-9]*)</td>.*?<font.*?>(.*?)</font>", status, re.DOTALL)
        if not result_m :
            wf("status", status)
            wf("html", html)
            # print status
            # print html
            raise Exception("re.match failed!")
            return None
        ret['origin_runid'] = result_m.group(1).strip()
        result = result_m.group(2).strip()
        
        # if Judge.StatusCode.has_key(ret['result']) :
        #     ret['result_id'] = Judge.StatusCode[ret['result']]
        # else :
        #     ret['result_id'] = oj.Judge_JG
        
        cvtRes = Judge.ConvertResult(result)
        ret['result_id'] = cvtRes[0]
        ret['result'] = cvtRes[1]

        #print "ret:", ret
        #raise ""
        if (Judge.IsFinalResult(ret['result'])) :
            # result is the final one, get details
            #if (!RE2::PartialMatch(status, "(?s)([0-9]*)MS.*?([0-9]*)K", &time_used, &memory_used)) 
            # print status
            tm_m = re.match(r".+?([0-9]*)MS.*?([0-9]*)K", status, re.DOTALL)
            if tm_m :
                ret['time'] = tm_m.group(1)
                ret['memory'] = tm_m.group(2)
            else :
                ret['time'] = ''
                ret['memory'] = ''
        else :
            ret['time'] = ''
            ret['memory'] = ''
        
        # ret['extra_info'] = self.__extra_info(ret['origin_runid'])
        if True == need_extra_info and ret['result_id'] == oj.Judge_CE :
            extra_info = self.__extra_info( ret['origin_runid'] )
            if extra_info :
                ret['extra_info'] = extra_info
            else :
                ret['extra_info'] = ''
        # print ret
        # raise ""
        ret['_is_end'] = Judge.IsFinalResult(ret['result'])
        return ret

    def Result(self, pid=None, username=None) :
        data = {}
        if pid :
            data['pid'] = pid
        if username :
            data['user'] = username
        if data :
            url = Judge.UrlStatus + urllib.urlencode(data) + '&lang=&status=0'
        else :
            url = Judge.UrlStatus
        #print "url Result ", url
        logging.info("open_url %s" % url)
        req = urllib2.Request(url, headers=Judge.Headers)
        rsp = self.opener.open(req)
        if not rsp :
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
            time.sleep(j_diff)

        result = {"result_id":oj.Judge_WT, "result":"VJudge Login", "extra_info":''}
        yield result

        if not self.logined :
            self.CheckLogin()
            logging.info("Judge Login pid:{0} language:{1} code_len:{2}".format(pid, lang, len(src)) )
            if not self.Login() :
                result = {"result_id":oj.Judge_WT, "result":"VJudge Login 2", "extra_info":''}
                yield result

                time.sleep(2)
                if not self.Login() :
                    raise oj.LoginFailedException("login 2 times, but failed!")
                    return
            self.logined = True
            # time.sleep(0.5)
            result = self.Result()
            if result :
                self.last_runid = result['origin_runid']
                logging.info("last_runid : %s" % self.last_runid)

        logging.info("Judge Submit {0} {1} ".format(pid, lang))

        result = {"result_id":oj.Judge_WT, "result":"VJudge Submit 1", "extra_info":''}
        yield result

        if not self.Submit(pid, lang, src) :
            logging.info("Judge Submit Failed! sleep {0}".format(1))
            #print "Cookie Begin"
            #print_cookie(self.cj)
            #print "Cookie End"
            self.logined = False
            self.cj.clear()
            yield {"result_id":oj.Judge_WT, "result":"VJudge Login 3", "extra_info":''}
            if not self.Login() :
                logging.error("Login failed!")
                raise oj.LoginFailedException("login failed after submit 1")
                #return
            self.logined = True
            result = {"result_id":oj.Judge_WT, "result":"VJudge Submit 2", "extra_info":''}
            yield result

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

        result = {"result_id":oj.Judge_WT, "result":"VJudge Get Result", "extra_info":''}
        yield result

        while True :
            #logging.info("Judge Reulst {0} {1}".format(pid, lang))
            try :
                result = self.Result(pid, self.username)
            except oj.JudgeException as e:
                raise e
            except Exception as e:
                logging.error("Exception " + str(err_cnt) + " " + str(e))
                err_cnt += 1
                if err_cnt > 3 :
                    raise e
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
                        logging.info(result['result'] + " is not final result!")
            yield result
            time.sleep(1)
        # end
        self.status = "end"
        if not result :
            raise Exception("no Result")
        yield result
        return

