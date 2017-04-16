#!/bin/bash
#nohup ./server_m.py hrbust.conf log/hrbust.log > /dev/null 2> log/hrbust.nohup.out &
nohup ./server_m.py hrbust.conf log/hrbust.log > log/hrbust.nohup.out 2>&1 &
#./server_m.py hrbust.conf log/hrbust.log 

