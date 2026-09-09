from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class FinanceMysqlRepository:
    def __init__(self, session : AsyncSession):
        self.session = session
        
    async def get_column_types(self, table_name: str) -> dict[str,str]:
        sql = f"show columns from {table_name}"
        result = await self.session.execute(text(sql))
        return {row.Field:row.Type for row in result.all()}

    async def get_column_values(self,table_name: str, column_name : str, limit:int = 10) -> list:
        sql = f"select distinct {column_name} from {table_name} limit {limit}"
        result = await self.session.execute(text(sql))
        return result.scalars().all()
    
    async def get_db_infos(self) ->dict[str,str]:
        result = await self.session.execute(text("select version()"))
        version = result.scalar()
        dialect = self.session.get_bind().dialect.name
        return {"version":version, "dialect":dialect}
    
    async def validate_sql(self, sql):
        await self.session.execute(text(f"explain {sql}"))
        
    async def excute_sql(self, sql):
        result = await self.session.execute(text(sql))
        return [dict(row) for row in result.mappings().all()]