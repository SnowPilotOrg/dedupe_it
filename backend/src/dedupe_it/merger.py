from typing import List, Dict, Any

from .utils import timing_decorator, with_anthropic_retry
from .config import Config
from .logger import logger
import json
from .llm import get_anthropic_client

system_prompt = """
You are a data merging assistant. 
Your task is to merge multiple records that represent the same entity into a single record.
- Combine all unique information
- When values appear compatible, combine them to create the most complete value
- When values appear to be contradictory, choose the most likely correct value

IMPORTANT: You must return ONLY the merged record as valid JSON with no additional text.
Maintain the exact same schema as the input records.

You will have to use good judgement, but here are some general guidelines:

- Prefer completeness:
    - If two records have similar values for a field, combine them to create the most complete value.
- Prefer latest timestamp:
    - If there is a conflict between two records with different timestamps, prefer the record with the latest timestamp.
- Prefer work email:
    - If there appear to be personal and work email addresses in the same field, prefer the work email address.
- Prefer specific address:
    - If there are two records with different addresses, prefer the address that appears more complete and specific.
- Prefer full name:
    - If there are two records with variations of the same name, prefer the full name.


Here are some examples:

Example 1:
- INPUT: [
    {"name": "John Smith", "email": "john@acme.com", "address": "123 Main St, Anytown, USA"},
    {"name": "John B. Smith", "email": "john.smith@gmail.com", "address": "123 Main St, Anytown, USA"}
]
- OUTPUT: {"name": "John B. Smith", "email": "john@acme.com", "address": "123 Main St, Anytown, USA"}
- Explanation: The name is more complete in the second record, and the email is more likely to be work.  The address is the same in both records.

Example 2:
- INPUT: [
    {"name": "Acme Inc.", "address": "123 Main St, Anytown, USA"},
    {"name": "acme corporation", "address": "123 Main St, Suite 100, Anytown, California, USA "},
    {"name": "Acme Inc.", "address": "123 Main St, Anytown"}
]
- OUTPUT: {"name": "Acme Inc.", "address": "123 Main St, Suite 100, Anytown, California, USA"}
- Explanation: The first and third records have the same form of the name, and the address is more complete in the second record.

The user may provide additional guidelines for merging.  Follow these guidelines if provided.  The user's guidelines take precedence over the examples above.
The user will also provide the records to be merged.  Use your best judgement; remember that you are an expert at entity matching and deduplication.
"""


class Merger:
    def __init__(self, config: Config):
        self.config = config
        self.anthropic_client = get_anthropic_client()

    # TODO: use structured outputs to ensure valid JSON conforming to the schema
    async def merge_records(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple records with the same schema into a single record."""
        if not records:
            raise ValueError("No records provided for merging")
        if len(records) == 1:
            return records[0]

        logger.info(f"Merging {len(records)} records")
        logger.info(f"Records: {json.dumps(records, indent=2)}")

        # Get the LLM to merge the records
        user_prompt = self._build_user_prompt(records)
        completion = await self._anthropic_completion_async(user_prompt)
        merged_record = json.loads(completion)
        return merged_record

    @timing_decorator
    @with_anthropic_retry(max_retries=5, initial_delay=1.0)
    async def _anthropic_completion_async(self, user_prompt: str) -> str:
        try:
            message = await self.anthropic_client.beta.prompt_caching.messages.create(
                # model="claude-3-5-sonnet-20241022",
                model="claude-3-haiku-20240307",  # cheaper and faster
                max_tokens=1024,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
            )
            answer = message.content[0].text.strip()
            logger.info(f"Anthropic answer: {answer}")
            return answer
        except Exception as e:
            logger.error(f"Error in anthropic completion: {e}")
            raise

    def _build_user_prompt(self, records: List[Dict[str, Any]]) -> str:
        """Create a prompt for the LLM to merge the records."""
        records_str = json.dumps(records, indent=2)
        return f"""Please merge these records into a single record that combines all unique information 
and resolves any conflicts. Maintain the exact same schema.

Records to merge:

<duplicate_records>
{records_str}
</duplicate_records>

Return only the merged record as a JSON object."""
