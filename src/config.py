from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class Settings:
    data_dir: Path = ROOT / "data"
    output_dir: Path = ROOT / "outputs"
    embedding_model: str = "all-MiniLM-L6-v2"
    auto_merge_threshold: float = 0.92
    review_threshold: float = 0.82
    semantic_weight: float = 0.60
    lexical_weight: float = 0.15
    attribute_weight: float = 0.25

SETTINGS = Settings()
