#!/bin/bash
#nohup ./server_m.py poj.conf log/poj.log > /dev/null 2> log/poj.nohup.out &
nohup ./server_m.py poj.conf log/poj.log > log/poj.nohup.out 2>&1 &
#./server_m.py poj.conf log/poj.log 

