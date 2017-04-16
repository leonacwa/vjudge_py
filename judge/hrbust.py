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
#traceback.print_exc()

#def wf(suf, page) :
#    name = "%010d_%s.html" % (time.time(), suf)
#    f = open(name,'w')
#    f.write(page)
#    f.close()

def print_cookie(cj) :
    for c in cj :
        print c #, cj[c]


class Judge(object):
    """Judge  http://poj.org/ Judger
    """
    __slots__ = ("cj", "opener", "username", "password", "pid", "lang", "src", "last_runid", "status", "last_judge_time", "logined")

    JudgeInterval = 2 # seconds
    UrlSite = r"http://acm.hrbust.edu.cn/"
    UrlLogin = UrlSite + "index.php?m=User&a=login"
    UrlSubmit = UrlSite + "index.php?m=ProblemSet&a=postCode"
    UrlStatus = UrlSite + "index.php?jumpUrl=&m=Status&a=showStatus&"
    UrlCeInfo = UrlSite + "index.php?m=Status&a=showCompileError&run_id="

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
        "G++":"2", "GCC":"1", "JAVA":"3", "PHP":"4", 
        "Python2":"5", "Haskell":"7", 
    }
    EndStatus = ["Accepted", "Presentation Error", "Time Limit Exceeded", 
                "Memory Limit Exceeded", "Wrong Answer", "Runtime Error", 
                "Output Limit Exceeded", "Compile Error", "System Error"]
    StatusCode = {"Accepted":oj.Judge_AC, "Presentation Error":oj.Judge_PE, 
            "Time Limit Exceeded":oj.Judge_TLE, "Memory Limit Exceeded":oj.Judge_MLE,
            "Wrong Answer":oj.Judge_WA, "Runtime Error":oj.Judge_RE, 
            "Output Limit Exceeded":oj.Judge_OLE, "Compile Error":oj.Judge_CE, "System Error" : oj.Judge_JE,
            "Judging":oj.Judge_JG, "Compiling":oj.Judge_JG,
            "Waiting":oj.Judge_JG}
    # POJ Status Column, Db Column
    # Column = ['RunID','User','Problem','Result','Memory','Time','Language','CodeLength','SubmitTime']
    Column = ['origin_runid', '_username', 'origin_pid', 'result',
                 'memory', 'time', 'display_language', 'source_code_len', '_submit_time']
    ResultTableStart = r'<TABLE cellSpacing=0 cellPadding=0 width=100% border=1 class=a bordercolor=#FFFFFF><tr class=in><td width=8%>Run ID</td><td width=10%>User</td><td width=6%>Problem</td><td width=20%>Result</td><td width=7%>Memory</td><td width=7%>Time</td><td width=7%>Language</td><td width=7%>Code Length</td><td width=17%>Submit Time</td></tr>'
    ResultTableEnd = r'</td></tr>'
    LoginInvalidStr = 'Username or password is not correct!'
    SubmitErrorStr = 'You can\'t submit code, please login!</td></tr>'

    # Init
    def __init__(self, username, password) :
        super(Judge, self).__init__()
        self.username = username
        self.password = password
        self.pid = None
        self.last_runid = 0
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
        # raise oj.LoginFailedException("test Exception")
        self.cj.clear()
        self.logined = False
        data = {
            "user_name" : self.username,
            "password" : self.password,
        }
        logging.info("open_url %s" % Judge.UrlLogin)
        post_data = urllib.urlencode(data)
        req = urllib2.Request(Judge.UrlLogin, data=post_data, headers=Judge.Headers)
        rsp = self.opener.open(req)
        if not rsp :
            return False
        res = rsp.read()
        self.logined = (res.find(Judge.LoginInvalidStr) == -1) # Login is valid?
        return self.logined

    def CheckLogin(self) :
        """
        CheckLogin(), and record last_submit_time
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
        return res and res.find(Judge.LoginInvalidStr) == -1

    def __open_submit_page(self, pid) :
        url = 'http://acm.hrbust.edu.cn/index.php?m=ProblemSet&a=submitCode&problem_id=' + pid
        logging.info("open_url %s" % url)
        req = urllib2.Request(url, headers=Judge.Headers)
        rsp = self.opener.open(req)
        #logging.debug("__open_submit_page :\nurl:%s\n%s\n",rsp.geturl(), rsp.read())
        return rsp.geturl()

    # Submit
    def Submit(self, pid, lang, src) :
        self.pid = pid
        submit_data = {
            "problem_id" : pid,
            "language" : lang,
            "source_code" : src, #src.replace('\r\n', '\n'),
            #"submit" : 'Submit',
            #"encoded" : '0',
            #"reset" : "Reset",
            #"url" : Judge.UrlSubmit
        }
        headers = copy.copy(Judge.Headers)

        ref_url = Judge.UrlSubmit + '&problem_id=' + pid
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

        logging.info("open_url %s" % Judge.UrlSubmit)
        req = urllib2.Request(Judge.UrlSubmit, data=post_data, headers=Judge.Headers)
        #req = urllib2.Request(ref_url, data=post_data, headers=Judge.Headers)
        rsp = self.opener.open(req)
        if not rsp :
            return False
        html = rsp.read()
        #wf("Submit_", html)
        ret = html.find(Judge.SubmitErrorStr) == -1 # check submit is ok
        if not ret :
            #logging.error("Submit check:\nurl:{0}\n{1}\n{2}\n".format(rsp.geturl(), rsp.info(), html))
            #logging.error("Submit check:\nurl:{0}\n{1}\n".format(rsp.geturl(), rsp.info())) #, html))
            logging.warning("Submit Warning! Found:" + Judge.SubmitErrorStr)

        if html.find('访问禁止') != -1 and html.find('检测到可疑访问，事件编号') != -1 :
            logging.error("Firewall Deny!!!")
            wf("Submit_Firewall", html)
            return False

        return ret

    def __extra_info(self, run_id) :
        url = Judge.UrlCeInfo + str(run_id)
        #print "url __extra_info ", url
        logging.info("open_url %s" % url)
        req = urllib2.Request(url, headers=Judge.Headers)
        rsp = self.opener.open(req)
        if not rsp :
            return None
        info = rsp.read()

        p1 = info.find('<td class="showcode_mod_info"')
        if -1 == p1 :
            return ""
        p1 = info.find('>', p1 + 10)
        p1 += 1
        p2 = info.find('</td></tr><tr><td><table>', p1)
        return  info[p1:p2].replace('<br />', "\n")

    def __parse_result(self, html, need_extra_info=True) :
        """
        __parse_result a status page, return the first row, or return None
        """
        #
        ret = {}
        ret['extra_info'] = ''
        p1 = html.find('<tr class="ojlist-row0" width="95%"><td>')
        if -1 == p1 :
            #print html
            raise oj.CommonException("Not Found ResultTableStart!")
            return None
            pass
        p2 = html.find('</td></tr>', p1 + 40)
        if p2 == -1 :
            #print html
            raise oj.CommonException("Not Found ResultTableStart!")
            return None
            pass
        status = html[(p1+40):p2]
        #p1 = status.find('title="Share your code">')
        p1 = status.find('<!-- 如果是自己的代码则显示去共享或者取消共享的按钮 -->')
        if -1 != p1 :
            p1 = status.find('</td><td>', p1 + 24)
            p1 += 9
            #print "find share code" , status[p1:]
        else:
            p1 = 0
        ## runid
        p2 = status.find('</td><td>', p1)
        ret['origin_runid'] = status[(p1):p2]
        
        if len(ret['origin_runid']) > 10 or len(ret['origin_runid']) < 4:
            print "status runid :", ret['origin_runid'], ":::::", status #[p1:p2]
            raise ""
            raise  sss
        status = status[(p2 + 9):]

        ## resulst
        p1 = status.find('<td class="')
        p1 = status.find('">', p1 + 11)
        status = status[(p1+2):]
        p1 = 0
        if 0 == cmp('<a href=', status[0:8]) : # Compile Error
            p1 = status.find('">', 8)
            p1 += 2
        p2 = status.find('<', p1)
        ret['result'] = status[p1:p2].strip()
        if Judge.StatusCode.has_key(ret['result']) :
            ret['result_id'] = Judge.StatusCode[ret['result']]
        else :
            #print status
            #print 'result::' , ret['result'], ':'
            #raise ""
            ret['result_id'] = oj.Judge_JG
            #ret['result'] = "Judge Error.parse_error"

        status = status[(p2+9):]
        #print "status result : ", status

        # time, memory
        p1 = status.find('</td><td>')
        p2 = status.find('</td><td>', p1 + 9)
        #print "status[(p1+9):p2]", status[(p1+9):p2]
        ret['time'] = (status[(p1+9):p2].strip())[:-2].strip()
        status = status[(p2+9):]
        #print "time :", status
        # memory
        p2 = status.find('</td><td')
        ret['memory'] = (status[:p2].strip())[:-1]
        #status = status[(p2+1):]
        
       # ret['extra_info'] = self.__extra_info(ret['origin_runid'])
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
            data['user_name'] = username
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
        
        yield {"result_id":oj.Judge_WT, "result":"VJudge Login", "extra_info":''}

        if not self.logined :
            logging.info("Judge CheckLogin pid:{0} language:{1} code_len:{2}".format(pid, lang, len(src)) )
            self.CheckLogin()
            if not self.Login() :
                raise oj.LoginFailedException("Vjudge login failed")
                return
                # time.sleep(1)

        logging.info("Judge Submit {0} {1} ".format(pid, lang))

        yield {"result_id":oj.Judge_WT, "result":"VJudge Submit 1", "extra_info":''}
        
        if not self.Submit(pid, lang, src) :
            logging.info("Judge Submit Failed! sleep {0}".format(1))
            #print "Cookie Begin"
            #print_cookie(self.cj)
            #print "Cookie End"
            self.cj.clear()
            if not self.Login() :
                logging.error("Login failed!")
                raise oj.LoginFailedException("login failed after submit 1")
                #return

            yield {"result_id":oj.Judge_WT, "result":"VJudge Submit 2", "extra_info":''}
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

        yield {"result_id":oj.Judge_WT, "result":"VJudge Get Result", "extra_info":''}

        while True :
            #logging.info("Judge Reulst {0} {1}".format(pid, lang))
            try :
                result = self.Result(pid, self.username)
            except Exception, e:
                err_cnt += 1
                if err_cnt > 3 :
                    raise Exception("Get result failed! err_cnt:" + str(err_cnt))
                result = None
            if result :
                #print "Judge status ", result
                print time.time(), "Judge Status", result["origin_runid"], last_runid
                print result
                #if result.has_key("origin_runid") and result["origin_runid"] > last_runid :
                if result.has_key("origin_runid") :
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

