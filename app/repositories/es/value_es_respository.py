from elasticsearch import AsyncElasticsearch

from app.models.es.value_info_es import ValueInfoES
from app.core.log import logger

class ValueESRepository:
    index_name = "data-agent-finance-index"
    mapping = {
        "dynamic" : False,
        "properties": {
            "id": {"type": "keyword"},
            "value": {"type": "text", "analyzer": "ik_max_word", "search_analyzer": "ik_max_word"},
            "type": {"type": "keyword"},
            "column_id": {"type": "keyword"},
            "column_name": {"type": "keyword"},
            "table_id": {"type": "keyword"},
            "table_name": {"type": "keyword"},      
        }
    }
    
    def __init__(self, client : AsyncElasticsearch):
        self.client = client
        
    async def _create_index(self):
        client = self.client
        index_name = self.index_name
        if await client.indices.exists(index=index_name):
            await client.indices.delete(index=index_name)
        await client.indices.create(
            index=index_name,
            mappings=self.mapping,
        )
        
        
    async def insert_values(self, values: list[ValueInfoES]):
        await self._create_index()
        
        index_dict = {
            "index": {
                "_index": self.index_name
            }
        }
        
        operations = []
        for value in values:
            operations.append(index_dict)
            operations.append(value)

        # 批量插入多个字段值信息数据
        # 分批批量插入
        logger.info("开始写入了")
        batch_size = 10
        for i in range(0, len(operations), batch_size):
            # 得到当前批次的operations
            batch_operations = operations[i:i+batch_size]
            # 批量插入当前批次的数据
            await self.client.bulk(operations=batch_operations)
            
            
    
    async def search(self, keyword:str)-> list[ValueInfoES]:
        result = await self.client.search(
            index=self.index_name,
            query={
                "match": {
                    "value": keyword
                }
            },
        )
        return [ValueInfoES(**item["_source"]) for item in result["hits"]["hits"]]
