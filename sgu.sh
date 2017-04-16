#!/bin/bash
#nohup ./server_m.py sgu.conf log/sgu.log > /dev/null 2> log/sgu.nohup.out &
nohup ./server_m.py sgu.conf log/sgu.log > log/sgu.nohup.out 2>&1 &
#./server_m.py sgu.conf log/sgu.log 

