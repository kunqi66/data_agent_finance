from dataclasses import dataclass
from pathlib import Path
from omegaconf import OmegaConf

@dataclass
class File:
    enable : bool
    level : str
    path: str
    rotation: str
    retention: str
    
@dataclass
class Console:
    enable : bool
    level : str

@dataclass
class LoggingConfig:
    file: File
    console: Console
    
    
    
@dataclass
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    
    
@dataclass
class QdrantConfig:
    host: str
    port: int
    embedding_size: int
    
    
@dataclass
class EmbeddingConfig:
    host: str
    port: int
    model: str
    
    
@dataclass
class ESConfig:
    host: str
    port: int
    index_name: str
    
    
    
@dataclass
class LLMConfig:
    model_name: str
    api_key: str
    
@dataclass
class AppConfig:
    logging: LoggingConfig
    db_meta_finance: DBConfig
    db_finance: DBConfig
    qdrant: QdrantConfig
    embedding: EmbeddingConfig
    es: ESConfig
    llm: LLMConfig
    
    
_yaml_path = Path(__file__).parents[2] / "conf/app_config.yaml"

_yaml_data = OmegaConf.load(_yaml_path)

app_config:AppConfig = OmegaConf.to_object(OmegaConf.merge(AppConfig, _yaml_data))

if __name__ == '__main__':
    print(app_config, type(app_config))
    print(app_config.logging.file.level)