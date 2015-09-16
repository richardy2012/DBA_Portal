# DBA Portal

---

**DBA Portal** 是一款用于数据库自动化运维的web应用。

###主要包含以下功能：

- 服务器管理：服务器的申请和管理；

- 数据库管理：MySQL、MongoDB、Memcached数据库的部署安装与下线；

- DB实例管理：MySQL、MongoDB、Memcached实例的上下线；

- DB集群管理：MHA集群信息的查询；

- 备份中心：MySQL集群、MongoDB集群、MySQL单实例的备份配置，备份管理，备份日报；

- 实时监控：大盘实时、自选库实时、历史分析；



###DBA Portal 基本架构：

- Python Web 开发框架[Flask](http://flask.pocoo.org/);

- 前端模板来自[startbootstrap.com/](http://startbootstrap.com/template-overviews/sb-admin-2/);

- Python虚拟环境[virtualenv](https://virtualenv.pypa.io/);

- 数据库 MySQL 5.6.24-72.2, 客户端MySQLdb;

- 缓存层 Redis 3.0.3，客户端[redis-py](https://github.com/andymccurdy/redis-py);


