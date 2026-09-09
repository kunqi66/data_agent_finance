from qdrant_client import AsyncQdrantClient, models

from app.conf.app_config import app_config
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant


class ColumnQdrantResposty:
    collection_name = "data-agent-finance-column-collection"
    
    def __init__(self, client:AsyncQdrantClient):
        self.client = client
    
    async def _create_collection(self):
        client = self.client
        collection_name = self.collection_name
        if await client.collection_exists(collection_name=collection_name):
            await client.delete_collection(collection_name=collection_name)
        
        await client.create_collection(
            collection_name=collection_name,  # 集合名称
            vectors_config=models.VectorParams(
                size=app_config.qdrant.embedding_size,  # 向量的维度
                distance=models.Distance.COSINE  # 余弦相似匹配
            ),
        )
            
            
    async def upsert_column_vectors(self,vectors: list[list[float]], payloads : list[ColumnInfoQdrant], ids: list[str]):
        client = self.client
        collection_name = self.collection_name
        await self._create_collection()
        batch_size =10
        for i in range(0,len(vectors),batch_size):
            batch_vectors = vectors[i:i+batch_size]
            batch_payloads = payloads[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            # 批量插入当前批次的向量数据
            await client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=batch_ids[j],
                        payload=batch_payloads[j],
                        vector=batch_vectors[j],  # 生成一个10维的向量数据
                    )
                    for j in range(len(batch_ids))
                ],
            )
    
    
    async def search(self, vector: list[float], score_threshold=0.6) -> list[ColumnInfoQdrant]:
        result = await self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            score_threshold=score_threshold,  # 匹配相似度的临界值，小于这个值的所有点忽略
        )

        # print(result.points)
        # print(len(result.points[0].payload))
        # return [point.payload for point in result.points]  # payload是纯字典
        return [ColumnInfoQdrant(**point.payload) for point in result.points]