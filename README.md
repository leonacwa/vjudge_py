# vjudge_py

vjudge 使用的Python版本为 2.7.x ， 3.x 版本未经过测试，可能会有语法的问题。    

## submission 数据库表
有两个字段 : result 字符串, result_id 数字    

### 使用nohup命令提交作业    
如果使用nohup命令提交作业，那么在缺省情况下该作业的所有输出都被重定向到一个名为nohup.out的文件中，除非另外指定了输出文件：    
nohup command > myout.file 2>&1 &    
在上面的例子中，输出被重定向到myout.file文件中。    
使用 jobs 查看任务。    
使用 fg %n　关闭。    
另外有两个常用的ftp工具ncftpget和ncftpput，可以实现后台的ftp上传和下载，这样就可以利用这些命令在后台上传和下载文件了。    


### sample.conf 
样例配置，使用方式参考 poj.sh 脚本里的命令，

### send.py 
向vjudge server发送评测命令

### judge_monitor.cpp
用于监控进程存活，这里没改成使用 python。

## judge 目录
