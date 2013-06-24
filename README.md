MoePad User Guide
====
测试环境：
----
*  Python 2.7
*  Django 1.4.1
*  APScheduler 2.1.0
*  BeautifulSoup 3.2.1
*  pysqlite-2.6.3

Installation and Configuration:
----
1.  安装上面那一串依赖包，注意版本号，BeautifulSoup的使用由于参照了老程序的代码，暂时没法兼容最新的4.x版本。
2.  在选定路径执行`git clone ...`。
3.  进入MoePad目录（manage.py所在的那个目录），执行`python manage.py syncdb`，会执行数据库的创建，并建立一个** 管理员帐户**，这个可以用来管理屏蔽词数据库等。
4.  编辑同路径下的mpconfig.py文件，填写对应的参数。参数说明见文件注释。为说明方便，假设vps所在网站域名是`website.com`，同时，这个域名也是在新浪/腾讯后台指定的callback域名，如果非默认80端口，也加上端口号mpconfig.MoeWebsite应该是一个类似"http://website.com:8000 "的字符串（注意加上`http://`）。
5.  执行`screen -S bg`，创建一个后台环境用来运行django程序，在里面执行`python manage.py runserver 0.0.0.0:8000`。（端口号任意，如果服务器的80端口没被占用也可以用，保持和上一步中配置的一致即可，确保MoePad/settings.py里的DEBUG是True状态）
6.  此时django**测试环境**的服务已经可以访问了，按Ctrl+a+d从当前后台detach（Django仍在后台运行）。
7.  访问`website.com(:port)/admin`，用建立数据库时建立的管理员登录。可以看到一些数据库的情况。点击`Forbidden wiki itemss`可以进行屏蔽词列表的管理。如果有大量词汇的话可以我手动进行批量导入。
8.  访问`website.com`有三个链接：1是清除所有数据库里保存的授权信息。2是授权新浪帐户。3是授权腾讯帐户。
9.  授权好帐户后可以在vps后台执行`screen -S cron`创建一个后台环境来执行定时任务（包括定时发送微博，定时清除数据库无效数据，定时发送重新授权帐户的邮件给指定帐户等）。在此后台环境里运行`python cron.py`，完成后也Ctrl+a+d退出。
10.  目前的一些策略：
	*  屏蔽的策略是全词匹配。
	*  发送更新词汇的策略是5分钟抓取一次feed，找一条过去12小时内没发过，并且不在屏蔽列表里的发送出去。
	*  图片抓取是按老程序中的做法，找到合适大小的发出去
	*  清除数据库中无用数据，是每24小时执行一次，清除执行时间12小时之前的所有数据（即保留近12小时的数据）
	*  新浪和腾讯的支持均已加入
11.  TODO
	*  目前使用了一些硬盘IO操作，以后有时间研究memcache就把这类优化一下
	*  新浪API有提供图片url形式的发送方式，这样可以减少发送图片微博的阻塞时间
	*  脚本化一些管理操作

注：step 5-6是测试环境的部署配置，生产环境的配置参见deployment.md。

测试环境要求MoePad/settings.py中DEBUG标识为`True`!

License: MIT