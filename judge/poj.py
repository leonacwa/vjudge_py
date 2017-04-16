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
import base64
#traceback.print_exc()

def wf(suf, page) :
    name = "poj_%s_%010d.html" % (suf, time.time())
    f = open(name,'w')
    f.write(page)
    f.close()

def print_cookie(cj) :
    for c in cj :
        print c #, cj[c]


def poj_urlencode(src) :
    la = len(src)
    lb = len(bytes(src))
    _txt = src.replace('%', '%25')
    _txt = _txt.replace('&', '%26')
    _txt = _txt.replace('#', '%23')
    _txt = _txt.replace('/', '%2F')
    _txt = _txt.replace('\\', '%5C')
    _txt = _txt.replace('+', '%2B')
    _txt = _txt.replace('=', '%3D')
    _txt = _txt.replace('\r', '%0D')
    _txt = _txt.replace('\n', '%0A')
    _txt = _txt.replace('\t', '%09')
    _txt = _txt.replace(' ', '+')
    print la, lb, lb - la
    if la < lb : _txt = _txt + ' '*int(443)
    return _txt

    ls = []
    print 'poj_urlencode', len(bytes(src))
    for b in src :
        if b == '+' : 
            b = '%2B'
        elif b == ' ' : 
            b = '+'
        elif b.isalnum() : 
            b = b
        #elif b in ['.', '-', '*', '_'] : 
        #    b = b
        elif b in ['%', '&', '#', '/', '\\', '+', '=', '\r', '\n', '\t'] :
            b = (hex(ord(b)).upper())[2:]
            if len(b) == 1:
                b = '%0' + b
            else :
                b = '%' + b
        ls.append(b)
    return ''.join(ls)

class Judge(object):
    """Judge  http://poj.org/ Judger
    """
    __slots__ = ("cj", "opener", "username", "password", "pid", "lang", "src", "last_runid", "status", "last_judge_time", "logined", "runid")

    SUBMIT_NORMAL = 0
    SUBMIT_OTHER_ERROR = -1
    SUBMIT_INVALID_LANGUAGE = -2
    SUBMIT_CODE_LENGTH_ERROR = -3

    JudgeInterval = 2 # seconds
    UrlSite = r"http://poj.org/"
    UrlLogin = UrlSite + "login?"
    UrlSubmit = UrlSite + "submit?"
    UrlStatus = UrlSite + "status?"
    UrlCeInfo = UrlSite + "showcompileinfo?"

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
        "G++":"0", "GCC":"1", "JAVA":"2", "PASCAL":"3", 
        "C++":"4", "C":"5", "FORTRAN":"6",
    }
    EndStatus = ["Accepted", "Presentation Error", "Time Limit Exceeded", 
                "Memory Limit Exceeded", "Wrong Answer", "Runtime Error", 
                "Output Limit Exceeded", "Compile Error"]
    StatusCode = {"Accepted":oj.Judge_AC, "Presentation Error":oj.Judge_PE, 
            "Time Limit Exceeded":oj.Judge_TLE, "Memory Limit Exceeded":oj.Judge_MLE,
            "Wrong Answer":oj.Judge_WA, "Runtime Error":oj.Judge_RE, 
            "Output Limit Exceeded":oj.Judge_OLE, "Compile Error":oj.Judge_CE, 
            "Running & Judging":oj.Judge_JG, "Compiling":oj.Judge_JG,
            "Waiting":oj.Judge_JG}
    # POJ Status Column, Db Column
    # Column = ['RunID','User','Problem','Result','Memory','Time','Language','CodeLength','SubmitTime']
    Column = ['origin_runid', '_usernane', 'origin_pid', 'result',
                 'memory', 'time', 'display_language', 'source_code_len', '_submit_time']
    ResultTableStart = r'<TABLE cellSpacing=0 cellPadding=0 width=100% border=1 class=a bordercolor=#FFFFFF><tr class=in><td width=8%>Run ID</td><td width=10%>User</td><td width=6%>Problem</td><td width=20%>Result</td><td width=7%>Memory</td><td width=7%>Time</td><td width=7%>Language</td><td width=7%>Code Length</td><td width=17%>Submit Time</td></tr>'
    ResultTableEnd = r'</td></tr>'
    LoginValidStr = '<a href=loginlog>Login Log</a>'
    SubmitOkStr = 'Problem Status Lis'

    # Init
    def __init__(self, username, password) :
        super(Judge, self).__init__()
        self.username = username
        self.password = password
        self.pid = None
        self.last_runid = None
        self.last_judge_time = 0
        self.logined = False
        self.status = "end"
        self.cj = cookielib.CookieJar()
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
            "user_id1" : self.username,
            "password1" : self.password,
            "B1" : "login",
            "url" : "/"
        }
        logging.info("open_url %s" % Judge.UrlLogin)
        post_data = urllib.urlencode(data)
        req = urllib2.Request(Judge.UrlLogin, data=post_data, headers=Judge.Headers)
        rsp = self.opener.open(req)
        if not rsp :
            return False
        res = rsp.read()
        self.logined = res.find(Judge.LoginValidStr) > 0
        return self.logined

    def CheckLogin(self) :
        """
        CheckLogin(), and record last_runid
        """
        logging.info("open_url %s" % Judge.UrlStatus)
        req = urllib2.Request(Judge.UrlStatus, headers=Judge.Headers)
        rsp = self.opener.open(req)
        res = None
        if rsp :
            res = rsp.read()
            #wf("CheckLogin_", res)
            result = self.__parse_result(res, need_extra_info=False)
            if result and result.has_key('origin_runid') :
                #print "CheckLogin last_submit_time{%s}END" %  result['_submit_time']
                self.last_runid = result['origin_runid']
        return res and res.find(Judge.LoginValidStr) > 0

    def __open_submit_page(self, pid) :
        url = Judge.UrlSubmit + 'problem_id=' + pid
        logging.info("open_url %s" % url)
        req = urllib2.Request(url, headers=Judge.Headers)
        rsp = self.opener.open(req)
        #logging.debug("__open_submit_page :\nurl:%s\n%s\n",rsp.geturl(), rsp.read())
        return rsp.geturl()

    # Submit
    def Submit(self, pid, lang, src) :
        self.pid = pid
        submit_data = {
            "source" : base64.b64encode(src.replace('\r\n', '\n')),
            "problem_id" : pid,
            "language" : lang,
            "submit" : 'Submit',
            "encoded" : '1',
            #"reset" : "Reset",
            #"url" : Judge.UrlSubmit
        }
        headers = copy.copy(Judge.Headers)

        ref_url = Judge.UrlSubmit + 'problem_id=' + pid
        headers["Referer"] = ref_url
        headers["Accept"] = "*/*"
        headers["POST"] = ref_url

        post_data = urllib.urlencode(submit_data)
        #post_data = urllib.urlencode(submit_data).replace('%2A', '*')
        #post_pid = urllib.urlencode({"problem_id" : pid})
        #post_language = urllib.urlencode({"language" : lang})
        #post_source = urllib.urlencode({"source" : src}).replace('%2A', '*')
        #post_other = urllib.urlencode( {"submit" : 'Submit', "reset" : "Reset"} )
        #post_data = "&".join((post_pid, post_language, post_source, post_other))

        #post_data = urllib.urlencode(submit_data) + '&source=' + poj_urlencode(src)

        logging.info("open_url %s" % Judge.UrlSubmit)
        req = urllib2.Request(Judge.UrlSubmit, data=post_data, headers=Judge.Headers)
        #req = urllib2.Request(ref_url, data=post_data, headers=Judge.Headers)
        rsp = self.opener.open(req)
        if not rsp :
            return False
        html = rsp.read()
        #wf("Submit_", html)
        ret = html.find(Judge.SubmitOkStr) > 0 # check submit is ok
        if not ret :
            logging.error("Submit check:\nurl:{0}\n{1}\n{2}\n".format(rsp.geturl(), rsp.info(), html))
            if html.find(r'<li>Source code too long or too short,submit FAILED;if you really need submit this source please contact administrator</li>') > 0 :
                return Judge.SUBMIT_CODE_LENGTH_ERROR
            return Judge.SUBMIT_OTHER_ERROR

        if html.find('访问禁止') != -1 and html.find('检测到可疑访问，事件编号') != -1 :
            logging.error("Firewall Deny!!!")
            wf("Submit_Firewall", html)
            return Judge.SUBMIT_OTHER_ERROR

        return Judge.SUBMIT_NORMAL

    def __extra_info(self, run_id) :
        url = Judge.UrlCeInfo + 'solution_id=' + str(run_id)
        #print "url __extra_info ", url
        logging.info("open_url %s" % url)
        req = urllib2.Request(url, headers=Judge.Headers)
        rsp = self.opener.open(req)
        if not rsp :
            return None
        page = rsp.read()
        p1 = page.find('<pre>')
        if p1 == -1 :
            return None
        p1 += len('<pre>')
        p2 = page.find('</pre>', p1)
        if p2 == -1 :
            return None
        return page[p1:p2]

    def __find_be(self, page, b, e) :
        p1 = 0
        p2 = 0
        while 1 :
            p1 = page.find(b, p2)
            if p1 == -1 :
                return
            p1 += len(b)
            p2 = page.find(e, p1)
            if p2 == -1 :
                return
            yield page[p1:p2]

    def __strip_tags(self, s) :
        li = []
        start = 0
        while 1 :
            p1 = s.find('<', start)
            if p1 == -1 :
                break
            t = s[start:p1]
            if t and len(t) > 0 :
                li.append(t)
            p2 = s.find('>', p1 + 1)
            if p2 == -1 :
                break
            start = p2 + 1
        t = s[start:]
        if t and len(t) > 0 :
            li.append(s[start:])
        return ''.join(li)

    def __parse_result(self, page, need_extra_info=True) :
        """
        __parse_result a status page, return the first row, or return None
        """
        p1 = page.find(Judge.ResultTableStart)
        if p1 == -1 :
            wf("parse_result", page)
            #print page
            raise oj.CommonException("Not Found ResultTableStart!")
        p1 += len(Judge.ResultTableStart)
        p2 = page.find(Judge.ResultTableEnd, p1)
        if p2 == -1 :
            raise oj.CommonException("Not Found ResultTableEnd!")
        p2 += len(Judge.ResultTableEnd) # match end
        table = page[p1:p2]
        #print "table", table, " end"
        it = self.__find_be(table, '<td>', '</td>')
        i = 0
        ret = {}
        for x in it :
            ret[Judge.Column[i]] = self.__strip_tags(x)
            i += 1
            if i >= len(Judge.Column) :
                break
        if len(ret) != len(Judge.Column) :
            raise oj.CommonException("Columns is not enough \n{0} \n {1}".format(result, ret))
        if Judge.StatusCode.has_key(ret['result']) :
            ret['result_id'] = Judge.StatusCode[ret['result']]
        else :
            ret['result_id'] = oj.Judge_JE
            ret['result'] = "Judge Error"
        show_lang = ret['display_language'].upper()
        if Judge.Language.has_key(show_lang) :
            ret['language'] = Judge.Language[show_lang]
        #print "__parse_result", ret
        ret['extra_info'] = ""
        if True == need_extra_info and ret['result_id'] == oj.Judge_CE :
            extra_info = self.__extra_info( ret['origin_runid'] )
            if extra_info :
                ret['extra_info'] = extra_info
        ret['_is_end'] = (ret['result'] in Judge.EndStatus)
        return ret

    def Result(self, pid=None, username=None) :
        data = {}
        if pid :
            data['problem_id'] = pid
        if username :
            data['user_id'] = username
        if data :
            url = Judge.UrlStatus + urllib.urlencode(data)
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
            logging.info("Judge CheckLogin pid:{0} language:{1} code_len:{2}".format(pid, lang, len(src)) )
            self.CheckLogin()
            if not self.Login() :
                raise oj.LoginFailedException("loing 2 times, but failed")
                return
        # time.sleep(1)
        logging.info("Judge Submit {0} {1} ".format(pid, lang))
        
        result = {"result_id":oj.Judge_WT, "result":"VJudge Submit 1", "extra_info":''}
        yield result

        sret = self.Submit(pid, lang, src) 
        if sret == Judge.SUBMIT_OTHER_ERROR :
            logging.info("Judge Submit Failed! sleep {0}".format(Judge.JudgeInterval))
            #print "Cookie Begin"
            #print_cookie(self.cj)
            #print "Cookie End"
            self.cj.clear()
            if not self.Login() :
                logging.error("Login failed!")
                raise oj.LoginFailedException("login failed after submit 1")
                return

            result = {"result_id":oj.Judge_WT, "result":"VJudge Submit 2", "extra_info":''}
            yield result

            time.sleep(Judge.JudgeInterval)
            sret = self.Submit(pid, lang, src)

        if sret == Judge.SUBMIT_OTHER_ERROR :
            logging.error("Judge Submit 2 times, but failed! pid:{0} lang:{1} len_src:{2} ".format(pid, lang, len(src)) )
            raise oj.SubmitFailedException("submit 2 times, but failed!")
            return
        if sret == Judge.SUBMIT_CODE_LENGTH_ERROR :
            logging.error("Judge Submit jret:{0}, failed! Submit FAILED! code length is invalid.pid:{1} lang:{2} len_src:{3} ".format(sret, pid, lang, len(src)) )
            result = {"_is_end" : True, "result_id": oj.Judge_SUBMIT_ERROR, 
                    "result":"code length is invalid!" }
            yield result
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
                err_cnt += 1
                if err_cnt > 3 :
                    raise
                result = None
            if result :
                #print "Judge status ", result
                #print result["_submit_time"], last_submit_time
                if result.has_key("origin_runid") and result["origin_runid"] > last_runid :
                    #logging.debug(" check submit_time OK! {0} {1}".format(result["origin_runid"], last_runid) )
                    if (result['result'] in Judge.EndStatus) :
                        self.last_runid = result["origin_runid"]
                        break
            yield result
            time.sleep(1)
        # end
        self.status = "end"
        if not result :
            raise Exception("no Result")
        yield result
        return

