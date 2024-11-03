from dataclasses import dataclass

RECORD_ID_FIELD = "_dedupit_record_id"
GROUP_ID_FIELD = "_dedupit_group_id"


@dataclass
class Config:
    # Embedding settings
    embedding_model_name: str = "intfloat/e5-base"

    # Processing settings
    max_neighbors: int = 3
