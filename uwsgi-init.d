#!/bin/sh
#
# Simple UWSGI init.d script conceived to work on Linux systems
# as it does use of the /proc filesystem.

EXEC="/root/myblog/bin/uwsgi"
PIDFILE="/tmp/uwsgi.pid"
CONF="/root/myblog/myblog/uwsgi.ini"

start() 
	{
		cd /root/myblog && source bin/activate && sleep 3
        if [ -f $PIDFILE ]
        then
                echo "$PIDFILE exists, process is already running or crashed"
                rm -rf $PIDFILE
                $EXEC --module myblog.wsgi:application --ini $CONF
#--die-on-term --logto /var/log/uwsgi/uwsgi.log \
#                        --socket /root/myblog/myblog/uwsgi.sock \
#                        --vacuum --chdir /root/myblog/myblog \
#                        --home /root/myblog/myblog --stats 127.0.0.1:9191 \
#                        --venv /root/myblog --master --processes 2 \
#                        --threads 2 --uid nginx --buffer-size 32768 \
#                        --protocol http --harakiri 30 \
#                        --max-requests 10000 --pidfile /tmp/uwsgi.pid \
#                        --thunder-lock --listen 4000 --http-websockets \
#                        --enable-threads  --daemonize /var/log/uwsgi/uwsgi.log \
#                        --wsgi-file /root/myblog/myblog/myblog/wsgi.py /
#			--module myblog.wsgi:application

        else
                echo "Starting UWSGI server..."
                $EXEC --module myblog.wsgi:application --ini $CONF
        fi
	}
	
stop() 
	{
	if [ ! -f $PIDFILE ]
        then
                echo "Try to stop UWSGI"
                /root/myblog/bin/uwsgi --stop $PIDFILE 
		/usr/bin/kill -9 uwsgi \
		&& killall `pidof uwsgi` && /usr/bin/killall uwsgi \
		&& /usr/bin/killall uwsgi

        else
		/root/myblog/bin/uwsgi --stop $PIDFILE \
		&& kill -9 `pidof uwsgi` /usr/bin/killall uwsgi \
		&& /usr/bin/killall uwsgi && /usr/bin/killall uwsgi
                echo "Stopping ..."
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
