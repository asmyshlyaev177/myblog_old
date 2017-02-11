#python manage.py clearsessions
#python manage.py cleanfilecache
#python manage.py clear_cache

find /root/myblog -name "*.pyc" -type f -delete
python manage.py clean_pyc

#clear cache from redis
rpass="Qvjuzowu177Qvjuzowu177Qvjuzowu177"
keys=("*taglist*" "*cat_list*" "*post_*" "*comment*") 
for i in ${keys[@]} ; 
  do 
    /usr/bin/redis-cli -a $rpass --scan --pattern $i\
    | /usr/bin/xargs /usr/bin/redis-cli -a $rpass del	 

#echo $i
done
