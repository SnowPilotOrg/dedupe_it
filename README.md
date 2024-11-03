# Dedupe It

Deduplicate your CSV in one click. Try it: https://dedupe.it

[![Dedupe It Demo Video](https://github.com/user-attachments/assets/f4189062-8921-4b5b-9f1f-d0fd77d92347)](https://www.youtube.com/watch?v=7mZ0kdwXBwM)

## Overview

Dirty datasets suck. Common problems:
- Same person signs up with business and personal email
- Same company gets added to your CRM twice with slightly different naming, ex. "Amazon" vs. Amazon.com"
- Two overlapping datasets get merged - ex. website visitors and demo form submissions

I've wasted tons of time cleaning datasets with Excel formulas and SQL, but hand-crafting deterministic rules is tedious.

After trying "AI-powered" solutions like the AWS Entity Resolution, I was frustrated to find that I still had to map fields and hand-tune "confidence scores".

Dedupe It obviates manual configuration by using LLM vector embeddings & chat completions.

## How it works

The algorithm:
1. Perform an LLM vector embedding of each record
2. For each record, perform vector similarity search to identify its nearest neighbors (typically 2-5 neighbors)
3. For each nearest neighbor, ask an LLM to determine whether it's a duplicate of the record under consideration
4. If we identify two records as duplicates, we group them together
5. For each duplicate group, we have our LLM propose a merged record

Here are some advantages of this approach:
- Unlike a pure NxN record comparison, scales approximately linearly in time and cost
- Unlike a pure vector clustering approach, avoids the hard problem of picking a cluster cutoff
- Utilizes LLM chat completions to make fine-grained comparisons. Also makes it possible to add custom guidelines, ex. "consider international subsidiaries to be distinct entities".


## Future improvements
NOTE: I'm already testing some of these features locally.
If you want early access, feel free to email me at ben@snowpilot.com or fill out the form on the demo site (https://dedupe.it)

- **Incremental / stream deduplication**: Persist the vector database and groupings to deduplicate new records without reprocessing the whole dataset.
- **Custom rules**: Allow specifying custom guidelines, either fuzzy (ex. "consider international subsidiaries to be distinct entities") or deterministic (always use the values from the last updated record when merging).
- **Integrations**: Excel, Google Sheets, Google Forms, Salesforce, Hubspot, Snowflake, etc.

## Self-hosting

Frontend: see instructions in `frontend/README.md`
Backend: see instructions in `backend/README.md`

## Contributing

Contributions are welcome. We don't currently have a formal process for contribs; feel free to simply open an issue or PR.

## License

Dedupe It is open-source software, available under the Apache 2.0 license.

If you intend to use Dedupe It for commercial purposes, we simply ask that you include a copy of the original license in your code, and email the authors (founders@snowpilot.com) with a short explanation of how you intend to use Dedupe It.

## Contact

Dedupe It is built by the team at Snowpilot (YC S24, https://www.snowpilot.com)

The founders (Ben Warren and Dom Crosby) can be reached at founders@snowpilot.com.

Cheers!
