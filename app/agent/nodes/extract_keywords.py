from jieba.analyse import extract_tags
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger

"""
利用Jiaba对提问进行一个基本非语义分词，可能会丢失语义的词，需要后面的节点对提问进行语义分词补充
"""
def extract_keywords(state: DataAgentState, runtime: Runtime[DataAgentContext])->dict:
    runtime.stream_writer({"stage": "提取关键字"})
    try:
        query = state["query"]