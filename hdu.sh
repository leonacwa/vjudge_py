#!/bin/bash
#nohup ./server_m.py hdu.conf log/hdu.log > /dev/null 2> log/hdu.nohup.out &
nohup ./server_m.py hdu.conf log/hdu.log > log/hdu.nohup.out 2>&1 &
#./server_m.py hdu.conf log/hdu.log 

