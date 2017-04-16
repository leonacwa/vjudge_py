#!/bin/bash
ps -eo pid,pcpu,rss,vsz,cmd | grep server_m | grep -v grep

