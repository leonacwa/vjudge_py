#!/bin/bash
#nohup ./server_m.py zoj.conf log/zoj.log > /dev/null 2> log/zoj.nohup.out &
nohup ./server_m.py zoj.conf log/zoj.log > log/zoj.nohup.out 2>&1 &
#./server_m.py zoj.conf log/zoj.log 

