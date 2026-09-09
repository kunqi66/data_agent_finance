from dataclasses import dataclass, field
from pathlib import Path
from omegaconf import OmegaConf


@dataclass
class Column:
    name: str
    role: str
    description: str
    alias: list[str]
    sync: bool


@dataclass
class Table:
    name: str
    role: str
    description: str
    columns: list[Column]


@dataclass
class Metric:
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]


@dataclass
class MetaConfig:
    tables: list[Table]
    metrics: list[Metric]


_yaml_path = Path(__file__).parents[2] / "conf/meta_config.yaml"

_yaml_data = OmegaConf.load(_yaml_path)

meta_config: MetaConfig = OmegaConf.to_object(OmegaConf.merge(MetaConfig, _yaml_data))

if __name__ == '__main__':
    print(meta_config, type(meta_config))
    print(meta_config.tables[0].name)
    print(meta_config.metrics[0].name)
