#!/bin/bash

# System
yum install epel-release -y
yum update -y
yum groupinstall "Development Tools" -y
yum install perl perl-devel make \
tcl-devel yum-utils nano wget iputils tar \
epel-release unzip gcc-c++ perl-ExtUtils-Embed \
perl-devel sqlite-devel glibc-devel gnupg\
geoip-devel gd-devel libxslt-devel make autoconf \
m4 coreutils glibc-devel openssl-devel git \
bzip2-devel tk-devel yum-utils xz-libs \
zlib-devel ncurses-devel readline-devel \
gdbm-devel db4-devel libpcap-devel xz-devel \
python-pip make gcc man -y

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
net.bridge.bridge-nf-call-ip6tables = 1 \n
net.bridge.bridge-nf-call-iptables = 1 \n
fs.inotify.max_user_watches=100000" > /etc/sysctl.conf
sysctl -p

# nginx
yum install pcre-devel nginx nginx-all-modules -y
mkdir -p /tmp/nginx/cache
pip install --upgrade pip
pip install virtualenv
#nginx -c /root/myblog/myblog/nginx_new.conf -g 'daemon off;'
# add ip tables exception

#redis
rpm -Uvh http://rpms.remirepo.net/enterprise/remi-release-6.rpm
yum --enablerepo="remi" install redis -y

# Python 3.5
yum-builddep python -y
wget -4 https://www.python.org/ftp/python/3.5.3/Python-3.5.3.tgz
tar -xvf Python-3.5.3.tgz
cd Python-3.5.3
#umask 0022
#./configure --prefix=/usr/local --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib"
#./configure --enable-optimizations
./configure
make
make altinstall

# Supervisor
mkdir -p /var/log/supervisor
mkdir -p /var/log/ginicorn
mkdir -p /var/log/redis
mkdir -p /root/myblog/tmp/redis/
mkdir -p /var/run/redis
/usr/bin/easy_install supervisor
chmod -R 777 /root/myblog/tmp
chmod -R 777 /root/.imageio/
chown -R nginx:nginx /root/
cp /root/myblog/myblog/supervisord.init /etc/init.d/supervisord
chmod +x /etc/init.d/supervisord
chkconfig --add /etc/init.d/supervisord
chkconfig supervisord on


cd /root/
virtualenv --always-copy --python=/usr/local/bin/python3.5 myblog
chown nginx:nginx -R /root
cd myblog
source/bin activate


# rabbitmq
wget -4 https://www.rabbitmq.com/releases/rabbitmq-server/v3.6.6/rabbitmq-server-3.6.6-1.el6.noarch.rpm
wget -4 https://packages.erlang-solutions.com/erlang/esl-erlang/FLAVOUR_1_general/esl-erlang_19.2~centos~6_i386.rpm
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

# django and modules
cd /root/myblog
git clone https://github.com/asmyshlyaev177/myblog.git
cd myblog
pip install --upgrade pip
pip install -r requirements_new3.txt
sed -i -e "s|patterns('',|[|g" -e "s|patterns, | |g" \
-e "s/^)/]/g" /root/myblog/lib/python3.5/site-packages/froala_editor/urls.py

# FFMPEG for conver gif
pip install imageio
python << EOT
import imageio
imageio.plugins.ffmpeg.download()
EOT



