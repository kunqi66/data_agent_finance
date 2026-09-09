from typing import TypedDict

from langchain_huggingface import HuggingFaceEndpointEmbeddings
from app.repositories.qdrant.metric_qdrant_respository import MetricQdrantResposty
from app.repositories.qdrant.column_qdrang_repository import ColumnQdrantResposty
from app.repositories.es.value_es_respository import ValueESRepository
from app.repositories.mysql.meta_finance_mysql_repository import MetaFinanceMysqlRepository
from app.repositories.mysql.finance_mysql_repository import FinanceMysqlRepository

class DataAgentContext(TypedDict):
    embedding_client : HuggingFaceEndpointEmbeddings
    column_qdrant_repo: ColumnQdrantResposty
    metric_qdrant_repo: MetricQdrantResposty
    value_es_pero: ValueESRepository
    meta_mysql_repo:MetaFinanceMysqlRepository
    finance_mysql_repo : FinanceMysqlRepository
    