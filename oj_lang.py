#!/usr/bin/env python2.7
#coding:utf-8
import re
import sys

lang = open(sys.argv[1]).read()

m = re.findall(r'<option value="(\d+)" ?>(.*?)</option>', lang, re.M)
print len(m)
for l in m : 
    print "'%2s' => '%s'," %(l[0], l[1])
