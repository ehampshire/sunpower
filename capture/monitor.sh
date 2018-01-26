#!/bin/bash

WORKING_DIR=/root
#EXEC=sunpower.pl
EXEC=pycap2.py
LOG_DIR=/mnt/mydrive/logs/
LOG_EXT=".txt"

cd $WORKING_DIR
PID=`ps -aef |grep $EXEC | grep -v grep | grep -v vim | awk '{print $2}'`
echo Capture PID: $PID
UTCDATE=`date -u "+%Y-%m-%d %H:%M:%S"`
echo UTC: $UTCDATE
LOGDATE=`date "+%Y%m%d"`
#echo LOGDATE: $LOGDATE
LOGFILESEARCH="$LOG_DIR$LOGDATE$LOG_EXT"
#echo LOGFILESEARCH: $LOGFILESEARCH
if [ "$PID" != "" ]; then
        echo Capture is running!
	echo Checking whether we need to roll log file...
	if [ ! -f $LOGFILESEARCH ]; then 
		echo "Looks like a new day, $LOGFILESEARCH does not exist!  Rolling logfile by killing/starting $EXEC..."
		kill $PID
        	$WORKING_DIR/$EXEC 2>&1 &
	else
		echo "$LOGFILESEARCH exists, we should be good!"
	fi
else
        echo Capture is not running!  Starting...
        $WORKING_DIR/$EXEC 2>&1 &
fi
