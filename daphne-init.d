#!/bin/sh
#
# Simple DAPHNE init.d script conceived to work on Linux systems
# as it does use of the /proc filesystem.

EXEC="cd /root/myblog ; source bin/activate ;  \
	cd /root/myblog/myblog ; \
	/root/myblog/bin/daphne myblog.asgi:channel_layer \
	-u /tmp/daphne.sock --root-path /root/myblog/myblog"

start() 
	{
                echo "Starting Daphne"
		#/bin/su -l root -c "$EXEC" &
		$EXEC & #> /var/log/daphne.log > /dev/null &
	}
	
stop() 
	{
                echo "Try to stop Daphne"
		kill `ps aux | grep daphne | gawk '{print $2}'`\
		 ; sleep 10 ; killall daphne
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
		sleep 5
		start
	;;
    *)
        echo "Please use start or stop as first argument"
        ;;
esac
