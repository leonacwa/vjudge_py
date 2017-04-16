#!/bin/bash
#nohup ./server_m.py spoj.conf log/spoj.log > /dev/null 2> log/spoj.nohup.out &
nohup ./server_m.py spoj.conf log/spoj.log > log/spoj.nohup.out 2>&1 &
#./server_m.py spoj.conf log/spoj.log 

