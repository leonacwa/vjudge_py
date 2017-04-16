#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include<fcntl.h>
#include<sys/types.h>
#include<unistd.h>
#include<sys/wait.h>
#include <sys/stat.h>
#include <string>
using namespace std;

string judge[8] = {"poj.conf", "hrbust.conf", "hdu.conf", "sgu.conf", "spoj.conf", "ural.conf", "uva.conf", "uvalive.conf"};

void sigterm_handler(int arg);
volatile sig_atomic_t _running = 1;

int main(){
	pid_t pc, pid;//准备创建守护进程
	pc = fork();//先创建子进程，退出父进程
	if(pc < 0){
		exit(1);
	}
	else if(pc > 0){
		sleep(1);
		//printf("exit");
		exit(0);
	}
	pid = setsid();//在子进程中创建新会话
	if(pid < 0){
		perror("setsid error");
	}
	//chdir("/");//改变当前工作目录
	umask(0);//改变文件访问
	for(int i = 0; i < 3; i++){
		close(i);
	}//关闭文件描述符
	signal(SIGTERM, sigterm_handler);//设置响应

	string comm = "ps -ef | grep ";
	string redir = " > /dev/null";
	while(_running){
		sleep(30);
		for(int i = 0; i < sizeof(judge)/sizeof(judge[0]); i++){
	//	printf("%s\n", (comm+judge[i]).c_str());
			if(system((comm + judge[i] + redir).c_str())){
	//		printf("%d\n", i);
				system("./run.sh");
				break;
			}
		}
	}
	return 0;
}

void sigterm_handler(int arg){
	_running = 0;
}
