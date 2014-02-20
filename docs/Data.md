Data Design:
----

1.	配置信息：永久有效，考虑持久化问题
    
    存放在key：MoePadConf中。包括微博的App Key/Secret，MoePad程序所在域名，同一条目两次发送之间的间隔。

2.  Token信息：带过期时间，用登陆时返回的expires_in计算

    存放在key：WeiboAuth(original/retweet)中，分别保存发送原创微博，转推微博的OAuth授权信息。保存了access token, expires_in, user_type, uid。目前应该只使用了original。

3.  待发送条目池：带过期时间，一个条目如果长期轮不上发送就删除，定为24小时。

    分为三类，Verifying, Verified和Edited，分别是新创建的条目（待审核），通过审核的新条目以及编辑改动的 老条目，优先发送通过审核的新条目，只有当没有新条目时，才发送编辑导致更新的条目。同时，如果一个新创建的条目，24小时内没有审核的动作，就视为通过审核，移入Verified池中。
    
    各种条目池在redis中使用Hash来存放。所谓池也就是同一个池的条目其Hash Key的前缀相同。
    
    由于单纯根据Hash结构无法判定同一个池中的多个Key插入的先后顺序。（理想情况下倾向于FIFO方式来处理池中的数据。）其实是可以的，对每个Key考察其过期时间即可。但这样在每次决定待发送条目时都要遍历至少一个池的所有key。效率可能不高。
    
    尝试在redis中使用一个有序集合，用来保存各种需要过期的条目的key，排序依据就是他们的过期时间戳。每次在更新条目之前，都对这个集合进行处理，把已经过期的条目清除掉，并把将要过期的Verifying条目改为verified条目，同时改动条目池中的数据。

4.  禁止关键字池：永久有效，另外要考虑持久化问题。

    存放在key： ForbiddenItem 中，保存要过滤的关键词

5.  已发送条目池：带过期时间，根据MoePadConf里设置的发送间隔确定

    存放在key：SentItem中。