#!/bin/sh
#
# Simple GUNICORN init.d script conceived to work on Linux systems
# as it does use of the /proc filesystem.

EXEC="cd /root/myblog; source bin/activate; cd /root/myblog/myblog; \
	/root/myblog/bin/gunicorn myblog.wsgi:application -c \
	/root/myblog/myblog/gunicorn.conf"
PIDFILE="/var/run/gunicorn.pid"
CONF="/root/myblog/myblog/gunicorn.conf"

start() 
	{
        if [ -f $PIDFILE ]
        then
                echo "$PIDFILE exists, process is already running or crashed"
                rm -rf $PIDFILE && sleep 5
		/bin/su -l root -c /bin/bash -c "$EXEC" &
        else
                echo "Starting GUNICORN server..."
		/bin/su -l root -c /bin/bash -c "$EXEC" &

        fi
	}
	
stop() 
	{
	if [ ! -f $PIDFILE ]
        then
                echo "Try to stop UWSGI"
		kill `ps aux | grep gunicorn | gawk '{print $2}'`
                /bin/sleep 10

        else
                echo "Stopping ..."
		kill `ps aux | grep gunicorn | gawk '{print $2}'`
                /bin/sleep 10
        fi
	}
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
	restart)
		stop
		sleep 10
		start
	;;
    *)
        echo "Please use start or stop as first argument"
        ;;
esac
