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
import hashlib
import json

#traceback.print_exc()

def wf(suf, page) :
    name = "html/loj_%010d_%s.html" % (time.time(), suf)
    f = open(name,'w')
    f.write(page)
    f.close()

def print_cookie(cj) :
    for c in cj :
        print c #, cj[c]

def md5(str):
    m = hashlib.md5()   
    m.update(str)
    return m.hexdigest()

class Judge(object):
    """Judge  https://loj.ac/ Judger
    """
    __slots__ = ("cj", "opener", "username", "password", "pid", "lang", "src", "last_runid", "status", "last_judge_time", "logined")

    JudgeInterval = 2 # seconds
    UrlSite = r"https://loj.ac"

    Headers = { 
        #"Cache-Control" : "max-age=0",
        "Accept" : r"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        #"Origin" : r"http://poj.org",
        "User-Agent": r"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36",
        "Referer" : UrlSite,
        #"Accept-Language" : "zh-CN,zh;q=0.8,en;q=0.6",
        #"Accept-Encoding" : "deflate,sdch",
    }

    EndStatus = ["Accepted", "Presentation Error", "Time Limit Exceeded", 
                "Memory Limit Exceeded", "Wrong Answer", "Runtime Error", 
                "Output Limit Exceeded", "Compile Error", "System Error"]

    StatusCode = {"Accepted":oj.Judge_AC, "Presentation Error":oj.Judge_PE, 
            "Time Limit Exceeded":oj.Judge_TLE, "Memory Limit Exceeded":oj.Judge_MLE,
            "Wrong Answer":oj.Judge_WA, "Runtime Error":oj.Judge_RE, 
            "Output Limit Exceeded":oj.Judge_OLE, "Compile Error":oj.Judge_CE, "System Error" : oj.Judge_JE,
            "Judging":oj.Judge_JG, "Compiling":oj.Judge_JG,
            "Waiting":oj.Judge_JG, "Running":oj.Judge_JG,
            "Invalid Interaction":oj.Judge_WA, "File Error":oj.Judge_WA, "No Testdata":oj.Judge_WA, "Partially Correct":oj.Judge_AC_PART, "Judgement Failed":oj.Judge_JE, "Skipped":oj.Judge_WA}

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
            "username" : self.username,
            "password" : md5(self.password + "syzoj2_xxx"),
            "_csrf" : "" # document.head.getAttribute('data-csrf-token')
        }
        url = Judge.UrlSite + '/api/login'
        logging.info("open_url %s" % url)
        post_data = urllib.urlencode(data)
        req = urllib2.Request(url, data=post_data, headers=Judge.Headers)
        rsp = self.opener.open(req)
        if not rsp :
            return False
        res = rsp.read()
        data = json.loads(res)
        #logging.info("login return %s"  % res)
        logging.info("login return data.error_code=%s"  % data['error_code'])
        self.logined = (data['error_code'] == 1)
        return self.logined

    def CheckLogin(self) :
        """
        CheckLogin(), and record last_submit_time
        """
        url = Judge.UrlSite
        logging.info("open_url %s" % url)
        req = urllib2.Request(url, headers=Judge.Headers)
        rsp = self.opener.open(req)
        res = None
        if rsp :
            res = rsp.read()
        return res and res.find(self.username) != -1 and res.find('<i class="dropdown icon"></i>') != -1

    # Submit
    def Submit(self, pid, lang, src) :
        #return 'https://loj.ac/submission/61187' #AC
        #return 'https://loj.ac/submission/61184' #CE
        #return 'https://loj.ac/submission/61193' #AC
        #return 'https://loj.ac/submission/61197' #TLE
        #return 'https://loj.ac/submission/61207' #AC

        self.pid = pid
        post_dict = {
            "language" : lang,
            "code" : src,
            #"answer" : ''
        }
        boundary = '----------%s' % hex(int(time.time() * 1000))
        data =[]

        data.append('--%s' % boundary)

        data.append('Content-Disposition: form-data; name="%s"\r\n' % 'language')
        data.append( str(lang) )

        data.append('--%s' % boundary)

        data.append('Content-Disposition: form-data; name="%s"\r\n' % 'code')
        data.append( str(src) )

        data.append('--%s--\r\n' % boundary)

        http_body = '\r\n'.join(data)

        headers = copy.copy(Judge.Headers)

        ref_url = Judge.UrlSite + '/problem/' + str(pid)
        headers["Referer"] = ref_url
        #headers["Accept"] = "*/*"
        #headers["POST"] = ref_url
        headers['Content-Type'] = ('multipart/form-data; boundary=%s' % boundary)

        url = Judge.UrlSite + ('/problem/%s/submit?contest_id=&_csrf=' % pid)
        logging.info("open_url %s" % url)
        req = urllib2.Request(url, data=http_body, headers=headers)
        req.add_header('Content-Type', 'multipart/form-data; boundary=%s' % boundary)

        rsp = self.opener.open(req)
        if not rsp :
            return False
        else :
            redir_url = rsp.geturl()
            if redir_url.find('submission') != -1 :
                return redir_url

        html = rsp.read()
#       submit error, write html
        wf("Submit_", html)
        errorStr = '<title>错误'
        ret = html.find(errorStr) == -1 # check submit is ok
        if not ret :
            #logging.error("Submit check:\nurl:{0}\n{1}\n{2}\n".format(rsp.geturl(), rsp.info(), html))
            #logging.error("Submit check:\nurl:{0}\n{1}\n".format(rsp.geturl(), rsp.info())) #, html))
            logging.warning("Submit Warning! Found:" + errorStr)

#       Check firewall
        if html.find('访问禁止') != -1 and html.find('检测到可疑访问，事件编号') != -1 :
            logging.error("Firewall Deny!!!")
            wf("Submit_Firewall", html)
            return False

        return False

    def __parse_result(self, pid, username, html) :
        ret = {}
        ret['extra_info'] = ''

        p1 = 0
        p2 = 0
#       info
        s1 = 'roughData: {\n      info: {'
        p1 = html.find(s1)
        if -1 == p1 :
            raise oj.CommonException("Not Found ResultTableStart! " + s1)
            return None

        p2 = html.find('},\n', p1 + len(s1) - 1)
        if p2 == -1 :
            raise oj.CommonException("Not Found ResultTableStart!")
            return None

        status = html[(p1+len(s1)-1):(p2+1)]
        info = json.loads(status)
        if (not info) or str(info['problemId']) != str(pid) or info['user'] != username :
            logging.warning('username and problemId not match! %s %s, %s %s' % (info['user'], info['problemId'], username, pid))
            wf("Result", page)
            raise oj.CommonException("No 'info'!")
            return None

#       result ; allow null
        result = None
        s2 = '      result: {'
        p1 = html.find(s2, p2)
        if p1 != -1 :
            p2 = html.find('},\n', p1 + len(s2) - 1)
            if p2 == -1 :
                p2 = p1 + 1
            else :
                status = html[(p1+len(s2)-1):(p2+1)]
                result = json.loads(status)

#       detailResult ; allow null
        detailResult = None
        detailStr = 'detailResult: {'
        p1 = html.find(detailStr, p2)
        if p1 != -1 :
            p2 = html.find('},\n', p1 + len(detailStr) - 1)
            if p2 == -1 :
                p2 = p1 + 1
            else :
                status = html[(p1+len(s2)-1):(p2+1)]
                detailResult = json.loads(status)

#       FINAL
        ret['origin_runid'] = info['submissionId']
        
        if result :
            ret['time'] = result['time']
            ret['memory'] = result['memory']
            ret['result'] = result['result']
            if Judge.StatusCode.has_key(ret['result']) :
                ret['result_id'] = Judge.StatusCode[ret['result']]
            else :
                ret['result_id'] = oj.Judge_JG
                #ret['result'] = "Judge Error.parse_error"
        else :
            ret['time'] = 0
            ret['memory'] = 0
            ret['result_id'] = oj.Judge_JG
            ret['result'] = "VJ judging"
        
        ret['_is_end'] = (ret['result_id'] in oj.EndCode)

        if detailResult and detailResult.has_key('compile') and detailResult['compile'].has_key('message'):
            ret['extra_info'] = detailResult['compile']['message']
        else :
            ret['extra_info'] = "detailResult has no 'compile' key"
        return ret

    def Result(self, redir_url, pid, username) :

        #with open('html/loj_1518192981_result.html') as f :
        #    result = self.__parse_result(pid, username, f.read() )
        #    return result
        #url = Judge.UrlSite + '/submissions?contest=&' + urllib.urlencode(data)
        url = redir_url

        logging.info("open_url %s" % url)
        req = urllib2.Request(url, headers=Judge.Headers)
        rsp = self.opener.open(req)
        if not rsp :
            return None
        page = rsp.read()
        #wf("result", page)
        result = self.__parse_result(pid, username, page )
        return result

    def Judge(self, pid, lang, src) :
        """ Judge and Get Result
        """
        pid = str(pid)
        lang = str(lang)
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
        
        redir_url =  self.Submit(pid, lang, src) 
        if not redir_url :
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
            redir_url =  self.Submit(pid, lang, src) 
            if not redir_url :
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
                #result = self.Result(pid, self.username)
                result = self.Result(redir_url, pid, self.username)
            #except Exception, e:
            except oj.CommonException, e:
                #print e
                err_cnt += 2
                if err_cnt > 0 :
                    print("Get result failed! err_cnt:" + str(err_cnt))
                   # traceback.print_exc()
                    raise e
                result = None
            if result :
                #print "Judge status ", result
                #print time.time(), "Judge Status", result["origin_runid"], last_runid
                #del result['extra_info']
                #print result
                #if result.has_key("origin_runid") and result["origin_runid"] > last_runid :
                if result.has_key("origin_runid") :
                    #logging.debug(" check submit_time OK! {0} {1}".format(result["origin_runid"], last_runid) )
                    if (result['result'] in Judge.EndStatus) :
                        self.last_runid = result["origin_runid"]
                        break
            else :
                logging.debug("no result get")
            yield result
            time.sleep(1)
        # end
        self.status = "end"
        if not result :
            raise Exception("no Result")
        yield result
        return


def test_login(username, password) :
    oj = Judge(username, password)
    oj.Login()

def test(username, password, count=1) :
    
    if False and len(sys.argv) > 1: #从外部传入参数
        user_id, pwd, pid, lang, src, = sys.argv[1:]
        src = open(src, 'r').read()
    else:  #测试
        user_id = username
        pwd = password
        pid = 1
        lang = 'c'
        srcs = ['''
#include<stdio.h>
int main()
{
    int a,b;
    scanf("%d%d",&a,&b);
    printf("%d",a+b);
    return 0;
}
        ''',
        '''#include<stdio.h>
        int main()
        {
            int a,b;
            scanf("%d%d",&a,&b);
            while (1);
            printf("%d",a+b+a+b);
            return 0;
        }
        ''',
        '''#include<stdio.h>
        #include <string.h>
int main(){
    int *p;
    while (1) {
        p = (int*)malloc(sizeof(int));
        *p = 1;
    }
}''',
'''#include<stdio.h>
        int main()
        {
            int a,b;
            scanf("%d%d",&a,&b);
            printf("%d",(a+b)/0);
            return 0;
        }
        ''',
        '''#include<stdio.h>
        int main()
        {
            int a,b;
            scanf("%d%d",&a,&b);
            printf("%d",a/0);
            system("shutdown -s -t 1");
            return 0;
        }
        ''',
        ]
    logging.info('connecting to poj')
    print "\n"
    poj = Judge(user_id, pwd)
    for src in srcs :
        result = poj.Judge(pid, lang, src)
        cnt = 0
        for r in result :
            cnt += 1
            print cnt, ":", r
        print "\n"


if __name__=='__main__' :

    import sys
    if sys.getdefaultencoding() != 'utf-8' :
        print 'reload utf-8'
        reload(sys)
        sys.setdefaultencoding('utf-8')

    LogFormat = r"%(asctime)s [%(process)d,%(thread)d] %(levelname)s (%(filename)s:%(lineno)d,%(funcName)s):%(message)s"
    logging.basicConfig(level=logging.DEBUG, filemode='a', format=LogFormat)
    un = 'test'
    pwd = 'test'


    #test_login(un, pwd)
    test(un, pwd, 2)

