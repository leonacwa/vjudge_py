#!/bin/bash
ps -ef | grep server_m | grep -v grep | grep -o " [0-9]\{3,\} " | xargs -i echo "kill {}"

