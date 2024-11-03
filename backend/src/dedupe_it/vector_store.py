from contextlib import asynccontextmanager
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Dict, List
from functools import lru_cache
import duckdb
import polars as pl
import json

from .models import Record
from .logger import logger
from .utils import timing_decorator
from pydantic import BaseModel, Field


class StoreEntry(BaseModel):
    vector: List[float] = Field(..., description="Embedding vector for the record")
    id: str = Field(..., description="Unique identifier for the record")
    data: Dict = Field(..., description="The actual record data")

    def to_dict(self) -> Dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict) -> "StoreEntry":
        return cls(**data)


@asynccontextmanager
async def vector_store(embedding_model_name: str):
    logger.info(f"Creating vector store for {embedding_model_name}")
    vector_store = await VectorStore.create(embedding_model_name)
    try:
        yield vector_store
    finally:
        vector_store.close()


duckdb.install_extension("vss")


@lru_cache(maxsize=1)
def get_embedding_model(model_name: str) -> SentenceTransformer:
    return SentenceTransformer(model_name)


class VectorStore:
    def __init__(
        self,
        embedding_model_name: str,
        con: duckdb.DuckDBPyConnection,
    ):
        self.embedding_model = get_embedding_model(embedding_model_name)
        self.con = con
        logger.info("Vector store initialized")

    def union(self, record_id1: str, record_id2: str) -> None:
        """Merge two sets using union by rank.

        The rank-based union keeps the tree balanced by:
        1. Always attaching the shorter tree under the taller tree
        2. Increasing rank when combining trees of equal height
        """
        self.con.execute(
            f"""
            WITH RECURSIVE find_root AS (
                -- Base case: direct parent
                SELECT id, parent_id, rank
                FROM records
                WHERE id IN ('{record_id1}', '{record_id2}')
                
                UNION ALL
                
                -- Recursive case: follow parent pointers
                SELECT f.id, r.parent_id, r.rank
                FROM find_root f
                JOIN records r ON f.parent_id = r.id
                WHERE r.id != r.parent_id
            ),
            roots AS (
                -- Get the final roots and their ranks
                SELECT id, parent_id, rank,
                       ROW_NUMBER() OVER (ORDER BY rank DESC, id) as rn
                FROM find_root
                WHERE id = parent_id
            ),
            new_rank AS (
                -- Calculate new rank if ranks are equal
                SELECT CASE 
                    WHEN r1.rank = r2.rank THEN r1.rank + 1
                    ELSE r1.rank
                END as rank
                FROM roots r1
                JOIN roots r2 ON r1.rn = 1 AND r2.rn = 2
            )
            UPDATE records 
            SET parent_id = (SELECT parent_id FROM roots WHERE rn = 1),
                rank = CASE 
                    -- Only update rank for the root of the larger tree if ranks were equal
                    WHEN id = (SELECT parent_id FROM roots WHERE rn = 1)
                         AND (SELECT r1.rank FROM roots r1 JOIN roots r2 ON r1.rn = 1 AND r2.rn = 2 WHERE r1.rank = r2.rank)
                    THEN (SELECT rank FROM new_rank)
                    ELSE rank
                END
            WHERE id IN (
                SELECT id 
                FROM find_root 
                WHERE parent_id = (SELECT parent_id FROM roots WHERE rn = 2)
            )
            OR id = (SELECT parent_id FROM roots WHERE rn = 2)
            """
        )

    def close(self):
        try:
            logger.info("Closing DuckDB connection")
            self.con.close()
            logger.info("DuckDB connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing DuckDB connection: {str(e)}")
            raise

    @classmethod
    async def create(cls, embedding_model_name: str) -> "VectorStore":
        embedding_model = cls._init_embedding_model(embedding_model_name)
        logger.info(f"Embedding model initialized: {embedding_model_name}")
        dimension = embedding_model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {dimension}")
        con = await cls._init_db(dimension)
        logger.info("DuckDB initialized")
        return cls(embedding_model_name, con)

    @classmethod
    async def _init_db(cls, dimension: int) -> duckdb.DuckDBPyConnection:
        # Initialize DuckDB connection with VSS extension
        con = duckdb.connect()  # ":memory:"
        con.load_extension("vss")
        logger.info("VSS extension loaded")

        # Create tables and indexes - use execute instead of raw_sql
        con.execute(
            f"""
            CREATE TEMP TABLE IF NOT EXISTS records (
                vector FLOAT[{dimension}] NOT NULL,
                data JSON NOT NULL,
                id STRING NOT NULL,
                parent_id STRING NOT NULL,
                rank INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (id)
            )
            """
        )
        logger.info("Records table created")

        # Check if index exists
        indexes = con.execute("SELECT index_name FROM duckdb_indexes()").fetchall()
        if not any(index[0] == "vector_idx" for index in indexes):
            con.execute("CREATE INDEX vector_idx ON records USING HNSW (vector)")
            logger.info("Vector index created")
        else:
            logger.info("Vector index already exists")

        # Create view for group lookups
        con.execute("""
            CREATE VIEW IF NOT EXISTS record_groups AS
            WITH RECURSIVE find_roots AS (
                -- Base case: all records
                SELECT id, parent_id
                FROM records
                
                UNION ALL
                
                -- Recursive case: follow parent pointers to find roots
                SELECT f.id, r.parent_id
                FROM find_roots f
                JOIN records r ON f.parent_id = r.id
                WHERE r.id != r.parent_id
            )
            SELECT 
                id,
                LAST_VALUE(parent_id) OVER (
                    PARTITION BY id 
                    ORDER BY parent_id
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                ) as group_id
            FROM find_roots
        """)
        logger.info("Record groups view created")
        return con

    @classmethod
    def _init_embedding_model(cls, model_name: str) -> SentenceTransformer:
        return SentenceTransformer(
            model_name,
            prompts={
                "passage": "passage: ",
            },
            default_prompt_name="passage",
        )

    @classmethod
    def _format_record(cls, record_data: Dict[str, str]) -> str:
        """Combine record fields into a single string for embedding."""
        # Filter out internal fields
        text_fields = {
            k: v for k, v in record_data.items() if not k.startswith("_dedupit_")
        }
        return " ".join(str(v) for v in text_fields.values())

    @timing_decorator
    def _generate_embedding(self, record_data: Dict) -> np.ndarray:
        """Generate an embedding for a single record."""
        try:
            text = VectorStore._format_record(record_data)
            logger.debug(f"Formatted text length: {len(text)}")

            embedding = self.embedding_model.encode(
                text,
                output_value="sentence_embedding",
                precision="float32",
                convert_to_numpy=True,
            )
            logger.debug(f"Generated embedding shape: {embedding.shape}")
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    @timing_decorator
    def add_record(self, record: Record) -> StoreEntry:
        """Add a record and its embedding to the vector store."""
        try:
            logger.info(f"Adding record {record.id}")
            embedding = self._generate_embedding(record.data)
            logger.debug(f"Generated embedding of shape {embedding.shape}")

            entry = StoreEntry(
                vector=embedding.tolist(),
                id=record.id,
                data=record.data,
            )
            logger.debug(f"Created StoreEntry for {record.id}")

            entry_dict = entry.to_dict()
            entry_dict["parent_id"] = record.id
            entry_dict["rank"] = 0

            # Convert to Polars DataFrame and insert
            df = pl.DataFrame([entry_dict])
            logger.debug(f"Created Polars DataFrame: {df.schema}")

            self.con.execute("INSERT INTO records SELECT * FROM df")
            logger.info(f"Successfully inserted record {record.id}")
            return entry
        except Exception as e:
            logger.error(f"Error adding record {record.id}: {str(e)}")
            raise

    @timing_decorator
    async def find_neighbors(
        self,
        query_embedding: np.ndarray | List[float],
        k: int,
        exclude_record_id: str | None = None,
    ) -> List[Record]:
        try:
            logger.info(f"Finding {k} nearest neighbors")
            logger.debug(f"Query embedding shape/length: {len(query_embedding)}")
            logger.debug(f"Excluding record: {exclude_record_id}")

            query = f"""
                SELECT id, data::TEXT as data FROM records
                WHERE id != '{exclude_record_id}'
                ORDER BY array_distance(vector, {query_embedding}::FLOAT[{len(query_embedding)}])
                LIMIT {k}
            """
            logger.debug("Executing neighbor search query")
            result_df = self.con.execute(query).pl()
            logger.debug(f"Found {len(result_df)} results")

            results = result_df.to_dicts()
            return [
                Record.from_dict(
                    {"id": result["id"], "data": json.loads(result["data"])}
                )
                for result in results
            ]
        except Exception as e:
            logger.error(f"Error finding neighbors: {str(e)}")
            raise

    @timing_decorator
    async def find_neighbors_batch(
        self,
        query_embeddings: List[np.ndarray | List[float]],
        k: int,
        exclude_record_ids: List[str | None],
    ) -> List[List[Record]]:
        try:
            logger.info(
                f"Finding {k} nearest neighbors for {len(query_embeddings)} queries"
            )
            logger.debug(f"First query embedding shape: {len(query_embeddings[0])}")

            # Create temporary table
            create_table_sql = f"""
                CREATE TEMPORARY TABLE query_embeddings (
                    query_id INTEGER,
                    vector FLOAT[{len(query_embeddings[0])}],
                    exclude_id STRING
                )
            """
            logger.debug("Creating temporary table with SQL: " + create_table_sql)
            self.con.execute(create_table_sql)
            logger.debug("Temporary table created")

            # Prepare query data
            query_data = [
                {
                    "query_id": i,
                    "vector": embedding.tolist()
                    if isinstance(embedding, np.ndarray)
                    else embedding,
                    "exclude_id": exclude_id if exclude_id else "",
                }
                for i, (embedding, exclude_id) in enumerate(
                    zip(query_embeddings, exclude_record_ids)
                )
            ]
            logger.debug(f"Prepared {len(query_data)} query records")
            logger.debug(f"Sample query data: {query_data[0]}")

            # Insert using Polars
            query_df = pl.DataFrame(query_data)
            logger.debug(f"Query DataFrame schema: {query_df.schema}")

            self.con.execute("INSERT INTO query_embeddings SELECT * FROM query_df")
            logger.debug("Inserted query data into temporary table")

            # Perform batch search
            search_sql = """
                WITH neighbors AS (
                    SELECT 
                        q.query_id,
                        r.id,
                        r.data::TEXT as data,  -- Cast to TEXT to preserve the JSON string
                        array_distance(r.vector, q.vector) as distance,
                        ROW_NUMBER() OVER (
                            PARTITION BY q.query_id 
                            ORDER BY array_distance(r.vector, q.vector)
                        ) as rn
                    FROM query_embeddings q
                    CROSS JOIN records r
                    WHERE (q.exclude_id = '' OR r.id != q.exclude_id)
                )
                SELECT 
                    query_id,
                    id,
                    data,
                    distance
                FROM neighbors
                WHERE rn <= ?
                ORDER BY query_id, distance
            """
            logger.debug("Executing batch search query")
            result_df = self.con.execute(search_sql, [k]).pl()
            logger.debug(f"Search complete. Result shape: {result_df.shape}")

            # Clean up
            logger.debug("Dropping temporary table")
            self.con.execute("DROP TABLE query_embeddings")

            # Convert to Polars and group results
            results = []
            for query_id in range(len(query_embeddings)):
                group = result_df.filter(pl.col("query_id") == query_id)
                logger.debug(
                    f"Processing results for query {query_id}. Found {len(group)} matches"
                )

                try:
                    group_records = [
                        Record.from_dict(
                            {
                                "id": row["id"],
                                "data": json.loads(
                                    row["data"]
                                ),  # Parse the JSON string back to dict
                            }
                        )
                        for row in group.to_dicts()
                    ]
                    results.append(group_records)
                except Exception as e:
                    logger.error(
                        f"Error processing results for query {query_id}: {str(e)}"
                    )
                    logger.error(
                        f"Sample row data: {group.head(1) if len(group) > 0 else 'No results'}"
                    )
                    raise

            logger.info(f"Successfully processed all {len(query_embeddings)} queries")
            return results

        except Exception as e:
            logger.error(f"Error in batch neighbor search: {str(e)}")
            logger.error(
                f"Query embeddings shape: {len(query_embeddings)}x{len(query_embeddings[0])}"
            )
            logger.error(f"Exclude record IDs: {exclude_record_ids}")
            raise

    def get_groups(self, include_records: bool) -> pl.DataFrame:
        """Return all records with their group (root) IDs."""
        try:
            logger.info(f"Getting groups (include_records={include_records})")

            if include_records:
                query = """
                    SELECT r.id, g.group_id, r.data::TEXT as data
                    FROM records r
                    JOIN record_groups g ON r.id = g.id
                """
            else:
                query = "SELECT id, group_id FROM record_groups"

            logger.debug(f"Executing query: {query}")
            result_df = self.con.execute(query).pl()
            logger.debug(f"Got {len(result_df)} rows")

            if include_records:
                # Convert the data to a list of dictionaries and process JSON
                result_df = result_df.with_columns(
                    [pl.col("data").str.json_decode().alias("data")]
                )

            return result_df

        except Exception as e:
            logger.error(f"Error getting groups: {str(e)}")
            logger.error(f"Include records: {include_records}")
            if "result_df" in locals():
                logger.error(f"Result DataFrame schema: {result_df.schema}")
                logger.error(
                    f"Sample row: {result_df.head(1) if len(result_df) > 0 else 'No results'}"
                )
            raise

    def get_records(self, record_ids: List[str]) -> List[Record]:
        try:
            logger.info(f"Getting {len(record_ids)} records")
            record_ids_str = ", ".join(f"'{id}'" for id in record_ids)

            query = f"""
                SELECT id, data::TEXT as data 
                FROM records 
                WHERE id IN ({record_ids_str})
            """
            logger.debug(f"Executing query: {query}")

            result_df = self.con.execute(query).pl()
            logger.debug(f"Got {len(result_df)} records")

            # Parse JSON strings to dictionaries
            records = [
                Record.from_dict({"id": row["id"], "data": json.loads(row["data"])})
                for row in result_df.to_dicts()
            ]

            logger.info(f"Successfully retrieved {len(records)} records")
            return records

        except Exception as e:
            logger.error(f"Error getting records: {str(e)}")
            logger.error(f"Record IDs: {record_ids}")
            if "result_df" in locals():
                logger.error(f"Result DataFrame schema: {result_df.schema}")
                logger.error(
                    f"Sample row: {result_df.head(1) if len(result_df) > 0 else 'No results'}"
                )
            raise

    def _generate_embeddings_batch(self, records: List[Record]) -> List[np.ndarray]:
        """Generate embeddings for multiple records in batch."""
        texts = [self._format_record(record.data) for record in records]
        embeddings = self.embedding_model.encode(
            texts,
            batch_size=32,  # Adjust based on your memory constraints
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embeddings

    def add_records_batch(self, records: List[Record]) -> List[StoreEntry]:
        """Add multiple records and their embeddings to the vector store in batch."""
        try:
            logger.info(f"Adding batch of {len(records)} records")
            embeddings = self._generate_embeddings_batch(records)
            logger.debug(f"Generated {len(embeddings)} embeddings")

            entries = []
            records_data = []
            for record, embedding in zip(records, embeddings):
                try:
                    entry = StoreEntry(
                        vector=embedding.tolist(),
                        id=record.id,
                        data=record.data,
                    )
                    entries.append(entry)

                    record_dict = entry.to_dict()
                    # Ensure data is properly JSON serialized
                    record_dict["data"] = json.dumps(record_dict["data"])
                    record_dict["parent_id"] = record.id
                    record_dict["rank"] = 0
                    records_data.append(record_dict)

                    logger.debug(f"Prepared record {record.id} for insertion")
                    logger.debug(f"Record data type: {type(record_dict['data'])}")

                except Exception as e:
                    logger.error(f"Error processing record {record.id}: {str(e)}")
                    logger.error(f"Record data: {record.data}")
                    raise

            # Use Polars for batch insert
            df = pl.DataFrame(records_data)
            logger.debug(f"Created Polars DataFrame with schema: {df.schema}")
            logger.debug(f"First row sample: {df.head(1)}")

            # Create a temporary view of the data
            self.con.execute("CREATE TEMPORARY TABLE temp_records AS SELECT * FROM df")
            self.con.execute("""
                INSERT INTO records 
                SELECT 
                    vector,
                    CAST(data AS JSON) as data,
                    id,
                    parent_id,
                    rank
                FROM temp_records
            """)
            self.con.execute("DROP TABLE temp_records")

            logger.info(f"Successfully inserted {len(records)} records")
            return entries
        except Exception as e:
            logger.error(f"Error in batch insert: {str(e)}")
            logger.error(
                f"DataFrame schema: {df.schema if 'df' in locals() else 'Not created'}"
            )
            raise

    def batch_union(self, record_pairs: List[tuple[str, str]]) -> None:
        """Merge multiple pairs of sets using union by rank in batch.

        Args:
            record_pairs: List of (record_id1, record_id2) tuples to union
        """
        # Create a temporary table for the pairs
        self.con.execute("""
            CREATE TEMPORARY TABLE record_pairs (
                record_id1 STRING,
                record_id2 STRING
            )
        """)

        # Insert the pairs
        pairs_df = pl.DataFrame(
            {
                "record_id1": [pair[0] for pair in record_pairs],
                "record_id2": [pair[1] for pair in record_pairs],
            }
        )
        self.con.execute("INSERT INTO record_pairs SELECT * FROM pairs_df")

        # Perform batch union
        self.con.execute("""
            WITH RECURSIVE find_root AS (
                -- Base case: direct parent for all pairs
                SELECT id, parent_id, rank
                FROM records
                WHERE id IN (
                    SELECT record_id1 FROM record_pairs
                    UNION
                    SELECT record_id2 FROM record_pairs
                )
                
                UNION ALL
                
                -- Recursive case: follow parent pointers
                SELECT f.id, r.parent_id, r.rank
                FROM find_root f
                JOIN records r ON f.parent_id = r.id
                WHERE r.id != r.parent_id
            ),
            roots AS (
                -- Get the final roots and their ranks for each pair
                SELECT 
                    p.record_id1,
                    p.record_id2,
                    r1.parent_id as root1,
                    r2.parent_id as root2,
                    r1.rank as rank1,
                    r2.rank as rank2
                FROM record_pairs p
                JOIN find_root r1 ON r1.id = p.record_id1
                JOIN find_root r2 ON r2.id = p.record_id2
                WHERE r1.id = r1.parent_id  -- Only get roots
                  AND r2.id = r2.parent_id
            ),
            updates AS (
                -- Determine the new parent and rank for each pair
                SELECT 
                    CASE 
                        WHEN rank1 > rank2 THEN root1
                        WHEN rank2 > rank1 THEN root2
                        WHEN root1 < root2 THEN root1  -- Use ID as tiebreaker
                        ELSE root2
                    END as new_parent,
                    CASE 
                        WHEN rank1 = rank2 THEN rank1 + 1
                        ELSE GREATEST(rank1, rank2)
                    END as new_rank,
                    CASE 
                        WHEN rank1 > rank2 THEN root2
                        WHEN rank2 > rank1 THEN root1
                        WHEN root1 < root2 THEN root2
                        ELSE root1
                    END as old_parent
                FROM roots
            )
            UPDATE records 
            SET 
                parent_id = u.new_parent,
                rank = CASE 
                    WHEN id = u.new_parent AND EXISTS (
                        SELECT 1 FROM roots r 
                        WHERE r.rank1 = r.rank2 
                        AND (r.root1 = u.new_parent OR r.root2 = u.new_parent)
                    )
                    THEN u.new_rank
                    ELSE rank
                END
            FROM updates u
            WHERE records.parent_id = u.old_parent
               OR records.id = u.old_parent
        """)

        # Clean up
        self.con.execute("DROP TABLE record_pairs")
