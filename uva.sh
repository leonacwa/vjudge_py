#!/bin/bash
#nohup ./server_m.py uva.conf log/uva.log > /dev/null 2> log/uva.nohup.out &
nohup ./server_m.py uva.conf log/uva.log > log/uva.nohup.out 2>&1 &
#./server_m.py uva.conf log/uva.log 

