# -*- coding:utf-8 -*-
import memcache

SinaAppKey = "255208104"  # ���˵�appkey
SinaAppSecret = "c146e4d5772bf6a3363d9c804ed2c126"  # ���˵���Կ
TencentAppKey = ""
TencentAppSecret = ""
MoeWebsite = "http://local.pythonik.com:8000"  # vps�������������������˺���Ѷ�ĺ�̨���callbackҲӦ���������+����djangoʱָ���Ķ˿ںţ������80�˿ڶ˿ںſ���ʡ�ԣ�ע�����http://ǰ׺
feedurl = "http://zh.moegirl.org/index.php?title=Special:%E6%9C%80%E8%BF%91%E6%9B%B4%E6%94%B9&feed=atom&namespace=0"
mail_from = ""  # ������������������Ȩ�ʺŵ��ʼ���� ������
mail_to = ""	 # �ռ���
smtpserver = ""		# smtp������
mail_user = ""		# �������ʻ�����
mail_passwd = ""			# ����������
mc = memcache.Client(['127.0.0.1:11211'], debug=0)
