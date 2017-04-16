#!/bin/bash

old_path=`pwd`
cd /server/virtualjudge/py/vjudge/

./poj.sh
./hrbust.sh
./hdu.sh
./sgu.sh
./uva.sh
./uvalive.sh
./spoj.sh
./ural.sh

#ps -ef | grep server_m

cd $old_path

