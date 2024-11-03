import asyncio
from typing import AsyncIterator, Dict, List, Tuple

import polars as pl

from .models import Record
from .config import Config
from .vector_store import VectorStore
from .comparator import Comparator


class Grouper:
    def __init__(
        self,
        config: Config,
        vector_store: VectorStore,
    ):
        self.config = config
        self.vector_store = vector_store
        self.comparator = Comparator()

    async def process_records(self, records: List[Record]) -> None:
        """Process multiple records in batch, finding and comparing neighbors."""
        # Add all records to the store
        store_entries = self.vector_store.add_records_batch(records)

        # Find neighbors for all records
        neighbors = await self.vector_store.find_neighbors_batch(
            query_embeddings=[entry.vector for entry in store_entries],
            k=self.config.max_neighbors,
            exclude_record_ids=[entry.id for entry in store_entries],
        )

        # Prepare all comparison pairs
        comparison_pairs = []
        record_pairs = []  # Keep track of which records are being compared
        for record, record_neighbors in zip(records, neighbors):
            for neighbor in record_neighbors:
                comparison_pairs.append((record.data, neighbor.data))
                record_pairs.append((record.id, neighbor.id))

        # Batch compare all pairs
        batch_size = 200  # Adjust based on your API limits and performance needs
        results = []

        for i in range(0, len(comparison_pairs), batch_size):
            batch = comparison_pairs[i : i + batch_size]
            batch_results = await asyncio.gather(
                *[self.comparator.are_duplicates(pair[0], pair[1]) for pair in batch]
            )
            results.extend(batch_results)

        # Process all matches
        matches = []
        for (record_id, neighbor_id), is_match in zip(record_pairs, results):
            if is_match:
                matches.append((record_id, neighbor_id))

        self.vector_store.batch_union(matches)

    async def process_record(self, record: Record) -> None:
        async for match in self.identify_matches(record):
            record_id1, record_id2 = match
            self.vector_store.union(record_id1, record_id2)

    async def identify_matches(self, record: Record) -> AsyncIterator[Tuple[str, str]]:
        # Add record to vector store
        store_entry = self.vector_store.add_record(record)

        # Find neighbors
        neighbor_records = await self.vector_store.find_neighbors(
            store_entry.vector,
            self.config.max_neighbors,
            exclude_record_id=store_entry.id,  # Exclude self
        )

        # Compare record to neighbors
        tasks = []
        async with asyncio.TaskGroup() as tg:
            for neighbor_record in neighbor_records:
                task = tg.create_task(
                    self.comparator.are_duplicates(
                        store_entry.data, neighbor_record.data
                    )
                )
                tasks.append((task, neighbor_record))

        # Process results as they complete
        for task, neighbor_record in tasks:
            if task.result():
                yield store_entry.id, neighbor_record.id

    def get_groups(self, include_records=False) -> pl.DataFrame:
        return self.vector_store.get_groups(include_records)
