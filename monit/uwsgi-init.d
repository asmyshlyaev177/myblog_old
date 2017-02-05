#!/bin/sh
#
# Simple UWSGI init.d script conceived to work on Linux systems
# as it does use of the /proc filesystem.

EXEC="cd /root/myblog; source bin/activate; cd /root/myblog/myblog; \
	/root/myblog/bin/uwsgi --module myblog.wsgi:application \
	-c /root/myblog/myblog/uwsgi.ini"
PIDFILE="/tmp/uwsgi.pid"
#CONF="/root/myblog/myblog/uwsgi.ini"

start() 
	{
		cd /root/myblog && source bin/activate && sleep 3
        if [ -f $PIDFILE ]
        then
                echo "$PIDFILE exists, process is already running or crashed"
                rm -rf $PIDFILE
                /bin/su -l root -c /bin/bash -c "$EXEC"
        else
                echo "Starting UWSGI server..."
                /bin/su -l root -c /bin/bash -c "$EXEC"
        fi
	}
	
stop() 
	{
	if [ ! -f $PIDFILE ]
        then
                echo "Try to stop UWSGI"
                /root/myblog/bin/uwsgi --stop $PIDFILE 
		kill `ps aux | grep gunicorn | gawk '{print $2}'`
        else
		/root/myblog/bin/uwsgi --stop $PIDFILE 
		kill `ps aux | grep gunicorn | gawk '{print $2}'`
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
