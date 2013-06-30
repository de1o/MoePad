# -*- coding:utf-8 -*-
import memcache

SinaAppKey = "255208104"  # 新浪的appkey
SinaAppSecret = "c146e4d5772bf6a3363d9c804ed2c126"  # 新浪的密钥
TencentAppKey = ""
TencentAppSecret = ""
MoeWebsite = "http://local.pythonik.com:8000"  # vps服务器的域名（在新浪和腾讯的后台填的callback也应该是这个）+运行django时指定的端口号，如果用80端口端口号可以省略，注意加上http://前缀
feedurl = "http://zh.moegirl.org/index.php?title=Special:%E6%9C%80%E8%BF%91%E6%9B%B4%E6%94%B9&feed=atom&namespace=0"
mail_from = ""  # 用来发送提醒重新授权帐号的邮件相关 发件人
mail_to = ""	 # 收件人
smtpserver = ""		# smtp服务器
mail_user = ""		# 发件人帐户名称
mail_passwd = ""			# 发件人密码
mc = memcache.Client(['127.0.0.1:11211'], debug=0)
