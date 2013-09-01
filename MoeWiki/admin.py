from django.contrib import admin
from MoeWiki.models import WikiItems, AlreadlyRetweeted, RecentUpdateItems, MoePadConfig

admin.site.register(WikiItems)
admin.site.register(AlreadlyRetweeted)
admin.site.register(RecentUpdateItems)
admin.site.register(MoePadConfig)