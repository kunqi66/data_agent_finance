from typing import TypedDict

from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.models.es.value_info_es import ValueInfoES

class DateinfoState(TypedDict):
    data: str
    weekday : str
    quarter : str
    
    
class DBInfoState(TypedDict):
    version : str
    dialect: str
    
class ColumnInfoState(TypedDict):
    name : str
    type : str
    role : str
    examples : list
    description : str
    alias : list
    
class TableInfoState(TypedDict):
    name : str
    role : str
    description : str
    columns : list[ColumnInfoState]
    
class MetricInfoState(TypedDict):
    name:str
    description:str
    relevant_columns:list
    alias:list


class DataAgentState(TypedDict):
    query : str
    keywords : list[str]
    sql : str
    error : str
    recall_columns : list[ColumnInfoQdrant]
    recall_metrics : list[MetricInfoQdrant]
    recall_values : list[ValueInfoES]
    table_infos : list[TableInfoState]
    metric_infos : list[MetricInfoState]
    date_info: DateinfoState
    db_info : DBInfoState
    

