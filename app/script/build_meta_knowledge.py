import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import finance_mysql_client_manager,meta_finance_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.conf.meta_config import meta_config
from app.core.log import logger
from app.repositories.es.value_es_respository import ValueESRepository
from app.repositories.mysql.finance_mysql_repository import FinanceMysqlRepository
from app.repositories.mysql.meta_finance_mysql_repository import MetaFinanceMysqlRepository
from app.repositories.qdrant.column_qdrang_repository import ColumnQdrantResposty
from app.repositories.qdrant.metric_qdrant_respository import MetricQdrantResposty
from app.services.build_knowledge_service import MetaKnowledgeService

"""
1. 初始所有客户端管理器
2. 创建构建的业务对象,要准备
    创建依赖的所有持久层对象，传入依赖的session或client
    用来生成向量的客户端
3. 调用业务对象的构建方法来构建知识库
4. 如果成功了，提交事务
5。如果失败了，回滚事务
6. 最终都要关闭客户端管理器
"""

async def start_build():
    embedding_client_manager.init()
    es_client_manager.init()
    finance_mysql_client_manager.init()
    meta_finance_mysql_client_manager.init()
    qdrant_client_manager.init()
    try:
        async with (
            finance_mysql_client_manager.session_factory() as finance_session,
            meta_finance_mysql_client_manager.session_factory() as meta_session
        ):
            pass
            service = MetaKnowledgeService(
                    finance_mysql_repo=FinanceMysqlRepository(finance_session),
                    meta_myql_repo=MetaFinanceMysqlRepository(meta_session),
                    value_es_repo=ValueESRepository(es_client_manager.client),
                    column_qdrant_repo=ColumnQdrantResposty(qdrant_client_manager.client),
                    metric_qdrant_repo=MetricQdrantResposty(qdrant_client_manager.client),
                    embedding_client=embedding_client_manager.client
                )
            
            await service.build(meta_config)
            # 4. 如果成功了，提交事务
            await finance_session.commit()
            await meta_session.commit()
            logger.info("构建成功了")
    except Exception as e:
        await finance_session.rollback()
        await meta_session.rollback()
        logger.error(f"构建知识库失败： {str(e)}")
        raise
    finally:
        await es_client_manager.close()
        await finance_mysql_client_manager.close()
        await meta_finance_mysql_client_manager.close()
        await qdrant_client_manager.close()



if __name__ == "__main__":
    asyncio.run(start_build())
