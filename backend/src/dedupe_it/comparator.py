from .llm import get_anthropic_client
from .logger import logger
from typing import Dict, List
import json
from .utils import timing_decorator, with_anthropic_retry


system_prompt = """
    You are a messy data deduplication expert.  Your job is to determine if two records refer to the same entity,
    bearing in mind that records representing the same entity may have slight discrepancies in their representations due to typos,
    abbreviations, formatting, or changes in mutable attributes like address over time.

    To indicate that the two records refer to the same entity, respond with ONLY 'YES'.
    To indicate that the two records do not refer to the same entity, respond with ONLY 'NO'.
    Respond with ONLY 'YES' or 'NO'.  Do not respond with anything else.

    Here are some examples:

    Example 1:
    - Record 1: {"name": "John Smith", "email": "john@acme.com", "address": "123 Main St, Anytown, USA"}
    - Record 2: {"name": "John B. Smith", "email": "john.smith@gmail.com", "address": "123 Main St, Anytown, USA"}
    - Result: YES
    - Explanation: Given the similarity in the name and address (only differing by inclusion of a middle initial), we can infer that these two records likely refer to the same person,
            and that the differences in the email are likely a work vs. personal email

    Example 2:
    - Record 1: {"name": "Acme Inc.", "address": "123 Main St, Anytown, USA"}
    - Record 2: {"name": "acme corporation", "address": "123 Main St, Suite 100, Anytown, California, USA "}
    - Result: YES
    - Explanation: The two companies have the same name and address, with differences only in formatting and some additional address information.  These are likely the same company.

    The user may provide additional guidelines for matching.  Follow these guidelines if provided.  The user's guidelines take precedence over the examples above.
    The user will also provide the two records to be compared.  Use your best judgement; remember that you are an expert at entity matching and deduplication.
"""


class Comparator:
    def __init__(self):
        self.anthropic_client = get_anthropic_client()

    @timing_decorator
    async def are_duplicates(self, data1: Dict, data2: Dict) -> bool:
        """Async verification of a pair of records"""
        completion = await self._anthropic_completion_async(
            self._build_prompt(data1, data2, examples=[])
        )
        result = self._parse_response(completion)
        return result

    def _build_prompt(self, data1: Dict, data2: Dict, examples: List[str]) -> str:
        user_guidelines = """
        - Different legal entity names for the same company should match (e.g., 'Apple Inc' and 'Apple Corporation' are the same company)
        - Abbreviated forms should match their full forms (Corp/Corporation, Inc/Incorporated)
        """

        base_prompt = f"""
Consider the following guidelines:
{user_guidelines}

{examples}

Are the records referring to the same entity?

Record 1: {json.dumps(data1, indent=2)}
Record 2: {json.dumps(data2, indent=2)}
"""
        return base_prompt.strip()

    @timing_decorator
    @with_anthropic_retry(max_retries=5, initial_delay=1.0)
    async def _anthropic_completion_async(self, user_prompt: str) -> str:
        try:
            message = await self.anthropic_client.beta.prompt_caching.messages.create(
                model="claude-3-5-sonnet-20241022",
                # model="claude-3-haiku-20240307",
                max_tokens=1,
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
                temperature=0,
            )
            answer = message.content[0].text.strip()
            logger.info(f"Anthropic answer: {answer}")
            return answer
        except Exception as e:
            logger.error(f"Error in anthropic completion: {e}")
            raise

    def _parse_response(self, response: str) -> bool:
        return response.strip().upper() == "YES"
