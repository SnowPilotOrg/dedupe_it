# Environment Variables

Create a `.env` file (gitignored) and populate with the following:
```
ANTHROPIC_API_KEY="my-api-key"
TOKENIZERS_PARALLELISM=false
```

# External Dependencies

- [Anthropic](https://www.anthropic.com/api)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Just](https://github.com/casey/just)

# Local Development

To run with hot reloading:
```bash
just dev
```

# Production

To ensure dependencies are up to date:
```bash
just build
```

To run:
```bash
just run
```
