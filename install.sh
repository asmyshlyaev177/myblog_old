#!/bin/bash

# System
yum install epel-release -y
yum update -y
yum groupinstall "Development Tools" -y
yum install perl perl-devel make \
tcl-devel yum-utils nano wget iputils tar \
unzip gcc-c++ perl-ExtUtils-Embed \
perl-devel sqlite-devel glibc-devel gnupg\
geoip-devel gd-devel libxslt-devel autoconf \
m4 coreutils glibc-devel openssl-devel git \
bzip2-devel tk-devel yum-utils xz-libs \
zlib-devel ncurses-devel readline-devel \
gdbm-devel db4-devel libpcap-devel xz-devel \
python-pip make gcc man pcre-devel -y

sed -i "s/SELINUX=enforcing/SELINUX=disabled/g" /etc/selinux/config

echo -e "
* soft nofile 100000 \n
* hard nofile 1000000 \n
* soft nproc 100000 \n
* hard nproc 1000000" >> /etc/security/limits.conf
echo "session required pam_limits.so" >> /etc/pam.d/login

echo -e "
# Kernel sysctl configuration file for Red Hat Linux
#
# For binary values, 0 is disabled, 1 is enabled.  See sysctl(8) and
# sysctl.conf(5) for more details.
#
# Use '/sbin/sysctl -a' to list all possible parameters.  \n

# Controls IP packet forwarding
net.ipv4.ip_forward = 1 \n
# Controls source route verification
net.ipv4.conf.default.rp_filter = 1 \n
# Do not accept source routing
net.ipv4.conf.default.accept_source_route = 0 \n
# Controls the System Request debugging functionality of the kernel
kernel.sysrq = 0 \n
# Controls whether core dumps will append the PID to the core filename.
# Useful for debugging multi-threaded applications.
kernel.core_uses_pid = 1 \n
# Controls the use of TCP syncookies
net.ipv4.tcp_syncookies = 1 \n
# Controls the default maxmimum size of a mesage queue
kernel.msgmnb = 65536 \n
# Controls the maximum size of a message, in bytes
kernel.msgmax = 65536 \n
# Controls the maximum shared segment size, in bytes
kernel.shmmax = 12582912000 \n
# Controls the maximum number of shared memory segments, in pages
kernel.shmall = 3328000 \n
vm.swappiness = 1 \n
kernel.printk = 1 4 1 3 \n
net.ipv4.tcp_mem = 50576   64768   98152 \n
net.ipv4.tcp_rmem = 4096 87380 16777216 \n
net.ipv4.tcp_wmem = 4096 65536 16777216 \n
net.core.rmem_max = 16777216 \n
net.core.wmem_max = 16777216 \n
net.ipv4.tcp_congestion_control = htcp \n
#net.ipv4.tcp_tw_reuse = 1 \n
net.ipv4.tcp_window_scaling = 1 \n
net.ipv4.tcp_timestamps = 1 \n
net.ipv4.tcp_sack = 1 \n
net.ipv4.tcp_no_metrics_save = 1 \n
net.core.netdev_max_backlog = 3240000 \n
net.core.somaxconn = 65535 \n
net.ipv4.tcp_max_orphans = 65536 \n
vm.overcommit_ratio = 97 \n
vm.overcommit_memory = 2 \n
kernel.sched_migration_cost_ns=5000000 \n
kernel.sched_autogroup_enabled=0 \n
kernel.threads-max = 227351 \n
fs.file-max = 450000 \n
fs.inotify.max_user_watches=100000" > /etc/sysctl.conf
sysctl -p

# Python 3.5
yum-builddep python -y
wget -4 https://www.python.org/ftp/python/3.5.2/Python-3.5.2.tgz
tar -xvf Python-3.5.2.tgz
cd Python-3.5.2
#umask 0022
#./configure --prefix=/usr/local --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib"
./configure # --enable-optimizations
make
make altinstall

# nginx
#yum install pcre-devel nginx nginx-all-modules -y
mkdir -p /tmp/nginx/cache

wget -4 http://nginx.org/download/nginx-1.11.9.tar.gz
tar -xvf nginx-1.11.9.tar.gz
cd nginx-1.11.9
./configure --sbin-path=/usr/sbin/nginx \
 --prefix=/etc/nginx --lock-path=/var/run/nginx.lock \
 --conf-path=/etc/nginx/nginx.conf \
 --user=nginx --group=nginx \
 --pid-path=/var/run/nginx.pid \
 --with-pcre --with-pcre-jit\
 --with-http_ssl_module \
 --with-http_addition_module --with-http_sub_module \
 --with-http_dav_module --with-http_flv_module \
 --with-http_mp4_module --with-http_random_index_module \
 --with-http_secure_link_module --with-http_stub_status_module \
 --with-http_auth_request_module \
 --with-http_perl_module=dynamic --with-stream \
 --with-stream_ssl_module \
 --with-http_slice_module --with-mail_ssl_module \
 --with-http_v2_module \
 --with-mail=dynamic --with-file-aio \
 --with-threads --with-http_slice_module \
 --with-http_gzip_static_module --with-http_gunzip_module
 
 make && make install

#nginx -c /root/myblog/myblog/nginx_new.conf -g 'daemon off;'
# add ip tables exception

#redis
rpm -Uvh http://rpms.remirepo.net/enterprise/remi-release-6.rpm
yum --enablerepo="remi" install redis -y

# rabbitmq
cd /root
wget -4 https://www.rabbitmq.com/releases/rabbitmq-server/v3.6.6/rabbitmq-server-3.6.6-1.el6.noarch.rpm
wget -4 https://packages.erlang-solutions.com/erlang/esl-erlang/FLAVOUR_1_general/esl-erlang_19.2~centos~6_i386.rpm
#wget -4 https://packages.erlang-solutions.com/erlang/esl-erlang/FLAVOUR_1_general/esl-erlang_19.3-1~centos~6_amd64.rpm
wget -4 https://github.com/jasonmcintosh/esl-erlang-compat/releases/download/1.1.1/esl-erlang-compat-18.1-1.noarch.rpm
yum install esl-erlang_19.2~centos~6_i386.rpm -y
yum install -y esl-erlang-compat-18.1-1.noarch.rpm 
yum install rabbitmq-server-3.6.6-1.el6.noarch.rpm -y
mkdir -p /var/lib/rabbitmq/mnesia
rabbitmq-server -detached 
sleep 5
rabbitmqctl add_user django Qvjuzowu177Qvjuzowu177Qvjuzowu177
sleep 5
rabbitmqctl set_user_tags django administrator
sleep 5
rabbitmqctl set_permissions -p "/" django ".*" ".*" ".*"
sleep 5
rabbitmqctl stop && rabbitmqctl stop_app
chkconfig rabbitmq-server on

# virtualenv
pip install --upgrade pip
pip install virtualenv
cd /root/
virtualenv --always-copy --python=/usr/local/bin/python3.5 myblog
cd myblog
source bin/activate

# twisted from pip doesn't work
wget https://github.com/twisted/twisted/archive/twisted-16.2.0.tar.gz
tar -xvf twisted-16.2.0.tar.gz
cd twisted-twisted-16.2.0/
python setup.py install

# django and modules
cd /root/myblog
git clone https://github.com/asmyshlyaev177/myblog.git
cd myblog
git remote rm origin
git remote add origin https://asmyshlyaev177@github.com/asmyshlyaev177/myblog.git
pip install --upgrade pip
mkdir -p /root/myblog/tmp
pip install --no-index --find-links=pip -r requirements_new3.txt
#pip install -r requirements_new3.txt
sed -i -e "s|patterns('',|[|g" -e "s|patterns, | |g" \
-e "s/^)/]/g" /root/myblog/lib/python3.5/site-packages/froala_editor/urls.py

# FFMPEG for convert gif
pip install imageio
python << EOT
import imageio
imageio.plugins.ffmpeg.download()
EOT

deactivate
# Supervisor
mkdir -p /var/log/supervisor
mkdir -p /var/log/gunicorn
mkdir -p /var/log/redis
mkdir -p /var/run/redis
mkdir -p /var/log/celery/
mkdir -p /var/run/celery/
mkdir -p /var/log/gunicorn/
/usr/bin/easy_install supervisor
cp /root/myblog/myblog/supervisord.init /etc/init.d/supervisord
chmod +x /etc/init.d/supervisord
chkconfig --add /etc/init.d/supervisord
chkconfig supervisord on

service rabbitmq-server start

