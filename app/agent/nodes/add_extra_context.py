from datetime import datetime

from langgraph.runtime import Runtime
from app.agent.state import DataAgentState
from app.agent.context import DataAgentContext



async def add_extra_context(state: DataAgentState, runtime : Runtime[DataAgentContext]):
    runtime.stream_writer({"stage": "添加额外信息"})