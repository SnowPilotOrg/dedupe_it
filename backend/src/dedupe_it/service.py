from typing import List, Dict
import asyncio
from .config import Config
from .grouper import Grouper
from .vector_store import vector_store
from .merger import Merger
from .logger import logger
from .models import Record
from pydantic import BaseModel
import polars as pl


class GroupResult(BaseModel):
    group_id: str
    merged_data: Dict
    record_ids: List[str]


class DedupeResult(BaseModel):
    groups: List[GroupResult]


async def dedupe_records(records: List[Record]) -> DedupeResult:
    """Main deduplication service function that processes a list of records"""
    config = Config()

    logger.info(f"Preparing vector store for {config.embedding_model_name}")
    async with vector_store(config.embedding_model_name) as store:
        logger.info("Vector store prepared")
        grouper = Grouper(config, store)

        await grouper.process_records(records)
        groups_df = grouper.get_groups(include_records=True)
        logger.info(f"Found {len(groups_df)} records in groups")

        logger.debug(f"Groups DataFrame: {groups_df.head(1)}")

        groups_with_data = groups_df.group_by("group_id").agg(
            [pl.col("data").alias("data"), pl.col("id").alias("id")]
        )

        logger.debug(f"Groups with data: {groups_with_data.head(1)}")

        # Initialize merger for groups that need merging
        merger = Merger(config)

        # Process each group
        group_info = []
        merge_tasks = []

        logger.debug(f"Will merge {len(groups_with_data)} groups")

        for row in groups_with_data.iter_rows(named=True):
            group_id = row["group_id"]
            group_records = row["data"]
            record_ids = row["id"]

            if len(group_records) == 1:
                continue

            group_info.append((group_id, record_ids))
            merge_tasks.append(merger.merge_records(group_records))

        logger.debug(f"Merge tasks: {merge_tasks}")
        merge_results = await asyncio.gather(*merge_tasks)
        logger.debug(f"Merge results: {merge_results}")

        result_groups = []
        # Add merged results to final output
        for (group_id, record_ids), merged_data in zip(group_info, merge_results):
            result_groups.append(
                GroupResult(
                    group_id=group_id,
                    merged_data=merged_data,
                    record_ids=record_ids,
                )
            )

        logger.debug(f"Result groups: {result_groups}")

        logger.info(f"Processed {len(result_groups)} groups")
        return DedupeResult(groups=result_groups)
