# Dedupe It

Deduplicate your CSV in one click. Try it: https://dedupe.it

Watch a demo:
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
- **Incremental / stream deduplication**: Persist the vector database and groupings to deduplicate new records without reprocessing the whole dataset.
- **Custom rules**: Allow specifying custom guidelines, either fuzzy (ex. "consider international subsidiaries to be distinct entities") or deterministic (always use the values from the last updated record when merging).
- **Integrations**: Excel, Google Sheets, Google Forms, Salesforce, Hubspot, Snowflake, etc.

NOTE: Some of these features are already in the works. If you have requests or want early access, email founders@snowpilot.com or fill out the form on the demo site (https://dedupe.it)

## Self-hosting

Frontend: see instructions in `frontend/README.md`
Backend: see instructions in `backend/README.md`

## Contributing

Contributions are welcome. We don't currently have a formal process for contribs; feel free to simply open an issue or PR.

## License

Dedupe It is open-source software, available under the Apache 2.0 license.

If you intend to use Dedupe It for commercial purposes, we simply ask that you include a copy of the original license in your code, and email the authors (founders@snowpilot.com) with a short explanation of how you intend to use Dedupe It.

## FAQ

<details>
  <summary>What does Dedupe It cost to run?</summary>

  With no modifications, this implementation will cost you ~$8.40 per 1k records.
  This will depend on the size of your records, so please benchmark your costs on a small, representative sample of data before attempting to run on a large dataset.

  NOTE: We're working on optimizations to reduce the cost 100x.
  If you need to run deduplication on a larger dataset (100k+ rows), please email us: founders@snowpilot.com
</details>

<details>
  <summary>When should I use Dedupe It?</summary>

  Dedupe It is built for fuzzy deduplication of structured data.
  In other words, it's a good fit if your data:
  - Fits into a spreadsheet / CSV
  - Might have duplicates
  - The duplicates are not exact (ex. "Michael B. Schmidt, michael.schmidt@acme.com" and "mike schmidt, mike@acme.com")

  This is typically the case if:
  - Your data comes from manual entry, like someone filling out a form
  - Your data is a combination of multiple sources, each of which has different fields or formatting
</details>


<details>
  <summary>Do you have performance benchmarks?</summary>

  We'll release some more detailed head-to-head and benchmarks in the future.

  Anecdotally, on the datasets that we've tested (people, companies, and products):
  - Rate of false negatives (not catching a pair of duplicates): <5%
  - Rate of false positives (mistakenly identifying distinct records as duplicates): vanishingly small  
</details>


<details>
  <summary>Why should I use Dedupe It over alternative X?</summary>

  As of today, our main value proposition is simplicity.
  
  There is no other fuzzy deduplication solution that works out-of-the-box without manual configuration.

  That said, this implementation is a minimum viable product. Shortcomings of Dedupe It today include:
  - Relatively expensive (~$8.40/1k records). NOTE: we will be bringing this down 100x over the next month or two.
  - No incrementality. NOTE: we have incremental versions working locally.
  - No integrations. NOTE: on the roadmap.
  - No custom rules. NOTE: on the roadmap.

  If you need any of those features, please [contact us](##Contact).

  In the meantime, here are some popular alternatives:
  - Enterprise-ready: [AWS Entity Resolution](https://aws.amazon.com/entity-resolution/)
  - Open-source: [Zingg](https://www.zingg.ai/)
  - Integrated with Salesforce: [DataGroomr](https://datagroomr.com/)
  
</details>

<details>
  <summary>Can you add feature X?</summary>

  Probably! Add a thread in the discussions section on Github, email us at founders@snowpilot.com.
</details>

## Contact

Dedupe It is built by the [Snowpilot](https://www.snowpilot.com) team

To contact us, email founders@snowpilot.com

Cheers!
