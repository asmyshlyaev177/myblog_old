#!/bin/sh
#
# Simple GUNICORN init.d script conceived to work on Linux systems
# as it does use of the /proc filesystem.

EXEC="/root/myblog/bin/python3.5 /root/myblog/myblog/manage.py \
		runworker --only-channels=websocket.*"
#PIDFILE="/var/run/gunicorn.pid"
#CONF="/root/myblog/myblog/gunicorn.conf"

start() 
	{
                echo "Starting Worker..."
                cd /root/myblog; source bin/activate; cd /root/myblog/myblog; \
		sleep 15; $EXEC &> /var/log/worker.log > /dev/null &
	}
	
stop() 
	{
                echo "Stopping ..."
		kill `ps aux | grep runworker | head -n 1 | gawk '{print $2}'` && sleep 3
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
