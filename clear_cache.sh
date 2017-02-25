#python manage.py clearsessions
#python manage.py cleanfilecache
#python manage.py clear_cache

cd /root/myblog/myblog
find /root/myblog -name "*.pyc" -type f -delete
/root/myblog/bin/python manage.py clean_pyc

#clear cache from redis
rpass="Qvjuzowu177Qvjuzowu177Qvjuzowu177"
keys=("*taglist*" "*cat_list*" "*post_*" "*comment*" "*page_*"\
 "*list*" "*single*") 
for i in ${keys[@]} ; 
  do 
    /usr/bin/redis-cli -a $rpass --scan --pattern $i\
    | /usr/bin/xargs /usr/bin/redis-cli -a $rpass del	 

#echo $i
done
