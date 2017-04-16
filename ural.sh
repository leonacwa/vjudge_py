#!/bin/bash
#nohup ./server_m.py ural.conf log/ural.log > /dev/null 2> log/ural.nohup.out &
nohup ./server_m.py ural.conf log/ural.log > log/ural.nohup.out 2>&1 &
#./server_m.py ural.conf log/ural.log 

