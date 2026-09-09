import asyncio
import uuid
from app.conf.meta_config import MetaConfig, meta_config, Table, Metric
from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.column_metric_mysql import ColumnMetricMySQL
from app.models.mysql.metric_info_mysql import MetricInfoMySQL
from app.models.mysql.table_info_mysql import TableInfoMySQL
from app.models.es.value_info_es import ValueInfoES
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.repositories.es.value_es_respository import ValueESRepository
from app.repositories.qdrant.column_qdrang_repository import ColumnQdrantResposty
from app.repositories.qdrant.metric_qdrant_respository import MetricQdrantResposty
from app.repositories.mysql.finance_mysql_repository import FinanceMysqlRepository
from app.repositories.mysql.meta_finance_mysql_repository import MetaFinanceMysqlRepository

from langchain_huggingface import HuggingFaceEndpointEmbeddings
from app.core.log import logger


from datetime import timedelta, date, datetime
from decimal import Decimal

def convert_mysql_value(v):
    if isinstance(v, timedelta):
        # 处理TIME字段，支持微秒
        total_sec = int(v.total_seconds())
        h = total_sec // 3600
        m = (total_sec % 3600) // 60
        s = total_sec % 60
        if v.microseconds:
            return f"{h:02d}:{m:02d}:{s:02d}.{v.microseconds:06d}"
        return f"{h:02d}:{m:02d}:{s:02d}"
    elif isinstance(v, (datetime, date)):
        return v.isoformat()
    elif isinstance(v, Decimal):
        return str(v) # 保留高精度，不要直接float
    elif isinstance(v, bytes):
        import base64
        return base64.b64encode(v).decode("utf-8")
    else:
        return v

from decimal import Decimal

def convert_for_json_field(obj):
    """递归处理对象，用于MySQL JSON字段，把不可序列化类型转为字符串"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, timedelta):
        total_sec = int(obj.total_seconds())
        h = total_sec // 3600
        m = (total_sec % 3600) // 60
        s = total_sec % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    elif isinstance(obj, Decimal):
        return str(obj)
    elif isinstance(obj, list):
        return [convert_for_json_field(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_for_json_field(v) for k, v in obj.items()}
    else:
        return obj


EMBED_SEM = asyncio.Semaphore(4)

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import aiohttp

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=10),
    retry=retry_if_exception_type(aiohttp.client_exceptions.ServerDisconnectedError),
    reraise=True
)
async def embed_with_sem(texts, embedding_client):
    async with EMBED_SEM:
        return await embedding_client.aembed_documents(texts)

class MetaKnowledgeService:
    def __init__(self,
                 finance_mysql_repo: FinanceMysqlRepository,
                 meta_myql_repo: MetaFinanceMysqlRepository,
                 value_es_repo: ValueESRepository,
                 column_qdrant_repo: ColumnQdrantResposty,
                 metric_qdrant_repo: MetricQdrantResposty,
                 embedding_client: HuggingFaceEndpointEmbeddings
    ):
        self.finance_mysql_repo = finance_mysql_repo
        self.meta_myql_repo = meta_myql_repo
        self.value_es_repo = value_es_repo
        self.column_qdrant_repo = column_qdrant_repo
        self.metric_qdrant_repo = metric_qdrant_repo
        self.embedding_client = embedding_client
        
    
    async def build(self, config : MetaConfig):
        logger.info("开始构建知识库")
        if config.tables:
            column_infos = await self._save_table_infos_to_meta(config.tables)
            logger.info("保存表信息和字段信息到meta库成功")

            await self._save_column_infos_values_to_qdrant(column_infos)
            logger.info("生成向量并保存，保存列信息字段到qdrant成功")
            await self._save_column_values_to_es(column_infos,config.tables)
            logger.info("es建立全文索引库成功")
        if config.metrics:
            metric_infos : list[MetricInfoMySQL] = await self._save_metric_infos_to_meta_db(config.metrics)
            logger.info("保存指标信息到meta库成功")
            
            await self._save_metric_infos_to_qdrant(metric_infos)
            logger.info("保存指标信息到qdrant向量库成功")
        
        
    async def _save_table_infos_to_meta(self, tables: list[Table]) -> list[ColumnInfoMySQL]:
        table_infos : list[TableInfoMySQL] = []
        column_infos : list[ColumnInfoMySQL] = []
        
        for table in tables:
            table_info = TableInfoMySQL(
                id = table.name,
                name = table.name,
                description = table.description,
                role = table.role
            )
            table_infos.append(table_info)
            
            column_type_dict : dict[str,str] = await self.finance_mysql_repo.get_column_types(table_info.name)
            
            for column in table.columns:
                examples : list = await self.finance_mysql_repo.get_column_values(table_info.name, column.name)
                examples_safe = convert_for_json_field(examples)
                column_info = ColumnInfoMySQL(
                    id=f"{table.name}.{column.name}",
                    name=column.name,
                    type=column_type_dict[column.name],  # 需要检查表中字段类型
                    role=column.role,
                    examples=examples_safe, # 需要查表
                    description=column.description,
                    alias=column.alias,
                    table_id=table_info.id
                )
                
                column_infos.append(column_info)
                
        self.meta_myql_repo.save_table_infos(table_infos)
        self.meta_myql_repo.save_column_infos(column_infos)
        
        return column_infos

    async def _save_column_infos_values_to_qdrant(self, column_infos : list[ColumnInfoMySQL]):
        data_dict_list : list[dict] = []
        for column_info in column_infos:
            column_info_qdrant = ColumnInfoQdrant(
                id=column_info.id,
                name=column_info.name,
                type=column_info.type,
                role=column_info.role,
                examples=column_info.examples,
                description=column_info.description,
                alias=column_info.alias,
                table_id=column_info.table_id
            )
            
            # 向量化文本收集
            # name
            data_dict_list.append({
                "id": uuid.uuid4(),
                "embedding_text": column_info.name,
                "payload": column_info_qdrant
            })
            # description
            data_dict_list.append({
                "id": uuid.uuid4(),
                "embedding_text": column_info.description,
                "payload": column_info_qdrant
            })
            # alias
            for alia in column_info.alias:
                data_dict_list.append({
                    "id": uuid.uuid4(),
                    "embedding_text": alia,
                    "payload": column_info_qdrant
                })
                
        embedding_texts = [data_dict["embedding_text"] for data_dict in data_dict_list]
        batch_size = 8
        vectors : list[list[float]] = []
        for i in range(0, len(embedding_texts), batch_size):
            batch_embedding_texts = embedding_texts[i: i+batch_size]
            batch_vectors : list[list[float]] = await embed_with_sem(batch_embedding_texts,self.embedding_client)
            vectors.extend(batch_vectors)
            
        ids : list[str] = [data_dict["id"] for data_dict in data_dict_list]
        
        payloads: list[dict] = [data_dict["payload"] for data_dict in data_dict_list]
        await self.column_qdrant_repo.upsert_column_vectors(vectors, payloads, ids)


    async def _save_column_values_to_es(self,column_infos: list[ColumnInfoMySQL], tables : list[Table]):
        column_sync_dict: dict[str, bool] = {}
        for table in tables:
            for column in table.columns:
                column_sync_dict[f"{table.name}.{column.name}"] = column.sync
        value_infos: list[ValueInfoES] = []
        for column_info in column_infos:
            sync = column_sync_dict[column_info.id]
            if sync:
                # 查询dw库得到字段的所有值，对每个值，创建一个valueInfoES对象封装相关信息数据  value_infos:list[valueInfoES]
                values = await self.finance_mysql_repo.get_column_values(column_info.table_id, column_info.name, 100)
                
                
                
                
                for value in values:
                    
                    value = convert_mysql_value(value)
                    
                    value_infos.append(ValueInfoES(
                        id=f"{column_info.id}.{value}",
                        value=value,
                        type=column_info.type,
                        column_id=column_info.id,
                        column_name=column_info.name,
                        table_id=column_info.table_id,
                        table_name=column_info.table_id
                    ))
                # 调用持久层保存数据到ES中
            await self.value_es_repo.insert_values(value_infos)
            value_infos.clear()
        
        
        
    async def _save_metric_infos_to_meta_db(self, metrics: list[Metric]) -> list[MetricInfoMySQL]:
        metric_infos: list[MetricInfoMySQL] = []
        column_metrics: list[ColumnMetricMySQL] = []
        
        for metric in metrics:
            metric_infos.append(MetricInfoMySQL(
                id=metric.name,
                name = metric.name,
                description= metric.description,
                relevant_columns=metric.relevant_columns,
                alias=metric.alias
            ))
            for column_id in metric.relevant_columns:
                column_metrics.append(ColumnMetricMySQL(
                    column_id=column_id,
                    metric_id = metric.name
                ))
            
        self.meta_myql_repo.save_metric_infos(metric_infos)
        self.meta_myql_repo.save_column_metrics(column_metrics)
        
        return metric_infos
    
    
    async def _save_metric_infos_to_qdrant(self,metric_infos:list[MetricInfoMySQL]):
        
        data_dict_list : list[dict] = []
        
        for metric_info in metric_infos:
            metric_info_qdrant = MetricInfoQdrant(
                id=metric_info.id,
                name=metric_info.name,
                description=metric_info.description,
                alias=metric_info.alias,
                relevant_columns=metric_info.relevant_columns
            )
            
            data_dict_list.append({
                "id": uuid.uuid4(),
                "embedding_text" : metric_info.name,
                "payload" : metric_info_qdrant
            })
            
            data_dict_list.append({
                "id": uuid.uuid4(),
                "embedding_text": metric_info.description,
                "payload": metric_info_qdrant
            })
            for alia in metric_info.alias:
                    data_dict_list.append({
                        "id": uuid.uuid4(),
                        "embedding_text": alia,
                        "payload": metric_info_qdrant
                    })
            
            
        embedding_texts = [data_dict["embedding_text"] for data_dict in data_dict_list]
        batch_size = 8
        vectors : list[list[float]] = []
        for i in range(0, len(embedding_texts), batch_size):
            batch_embedding_texts = embedding_texts[i:i+ batch_size]
            batch_vectors: list[list[float]] = await embed_with_sem(batch_embedding_texts,self.embedding_client)

            vectors.extend(batch_vectors)

        ids: list[str] = [data_dict["id"] for data_dict in data_dict_list]

        # 从上面的数组容器中取出所有payload组成数组：payloads: list[dict]
        payloads: list[dict] = [data_dict["payload"] for data_dict in data_dict_list]

        # 调用持久层保存到向量库
        await self.metric_qdrant_repo.upsert_metric_vectors(vectors, payloads, ids)
    