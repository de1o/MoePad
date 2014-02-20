在服务器上部署nginx+django环境
----
**生产环境下把settings.py里的DEBUG置为False**

1.  安装nginx和django
2.  安装python-flup，我在debian下直接apt安装有报错，下载源码编译安装吧
3.  取代`python manage.py runserver`的运行方式(接README.md里的step 5)，改为运行`python manage.py runfcgi host=127.0.0.1 port=8080`
4.  为moepad工程创建一个nginx配置文件
	
		sudo touch /etc/nginx/sites-available/moepad.conf
	
		sudo ln -s /etc/nginx/sites-available/moepad.conf /etc/nginx/sites-enabled/moepad.conf


5.	编辑配置文件 `vi moepad.conf`

		server {
		    listen 80;  # 修改这里为在新浪/腾讯后台填写的callback url端口，默认80
		    server_name myhostname.com;
		    access_log /var/log/nginx/moepad.access.log;
		    error_log /var/log/nginx/moepad.error.log;
		
		    location /static/ { # STATIC_URL for admin
		        alias /usr/local/lib/python2.7/site-packages/django/contrib/admin/static/;
		        expires 30d;
		    }
		
		    location / {
		        include fastcgi_params;
		        fastcgi_pass 127.0.0.1:8080; # 注意这里的端口要和第3步里的一致
				fastcgi_split_path_info ^()(.*)$;
		    }
		} 

		注意检查一下admin static的路径是否存在，不正确的话admin后台没法正常显示。

6.  重载nginx: `sudo /etc/init.d/nginx reload`
	
7.  在settings.py里修改ALLOWED_HOST，加上你使用的域名，否则会被拒绝服务。
8.	关闭服务的话我用比较土的ps -ef|grep cgi，找到django fastcgi的主进程（ppid=1）杀掉，应该做成脚本的，这个TODO吧。
9.  后接README.md的step 7.
10.  settings.py 里的ADMIN字段的作用（目前）是，当以生产环境运行django程序时，后台无法看到错误输出，但通过配置可以把错误信息发送到管理员的邮箱，这里可以留一个我的，以后出了bug好修。Email的配置在settings.py的`EMAIL_*`字段里。目前测试使用gmail的smtp服务可以通过，163的非SSL加密方式失败。暂时不管了，请在此处配置一个gmail邮箱。

