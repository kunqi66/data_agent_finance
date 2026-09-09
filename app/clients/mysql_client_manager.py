import asyncio
from typing import Optional

from sqlalchemy import text, Select

from app.conf.app_config import DBConfig, app_config
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker

from app.models.mysql.table_info_mysql import TableInfoMySQL


class MysqlClientManager:
    def __init__(self, config: DBConfig):
        self.config = config
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None

    def _get_url(self):
        return f"mysql+asyncmy://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}?charset=utf8mb4"

    def init(self):
        # 创建引擎
        self.engine = create_async_engine(
            self._get_url(),
            pool_size=10, # 连接池的大小，初始创建的常驻连接数，用完后还回来，如果超过了只能创建临时连接，用完后自动断开
            max_overflow=15, # 最大临时连接数，如果超过了，只能等待，在超时时间内有连接还回来了，正常使用，如果没有，报错
            pool_pre_ping=True, # 获取连接时，会自动判断这个连接是否可用，如果不可用，自动创建一个新的返回给你， 防止数据库操作意外失败
        )
        # 创建工厂
        self.session_factory = async_sessionmaker(
            self.engine,
            autobegin=True,  # 默认就是True, 代表自动开启事务， 并不会自动提交事件
            expire_on_commit=False,  # 事务提交后，ORM对象是否过期，为False代表不过期，还可以使用
            autoflush=True,  # 在查询前是否自动将未提交事务的数据更新同步到暂存区 =》是否可以立即查询到  False查不到
        )

    async def close(self):
        await self.engine.dispose()

# 创建操作dw数据库的客户端管理器
finance_mysql_client_manager = MysqlClientManager(app_config.db_finance)

# 创建操作meta数据库的客户端管理器
meta_finance_mysql_client_manager = MysqlClientManager(app_config.db_meta_finance)

if __name__ == '__main__':
   pass