#!/bin/bash
#nohup ./server_m.py uvalive.conf log/uvalive.log > /dev/null 2> log/uvalive.nohup.out &
nohup ./server_m.py uvalive.conf log/uvalive.log > log/uvalive.nohup.out 2>&1 &
#./server_m.py uvalive.conf log/uvalive.log 

