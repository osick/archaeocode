# Quick Start Guide

Get from clone to your first analysis in about five minutes.

## 1. Install

```bash
git clone https://github.com/osick/codelore.git
cd codelore
pip install -r requirements.txt
```

## 2. Configure (optional, for user stories)

```bash
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY (or OPENAI_API_KEY)
```

Without an API key the workflow still runs discovery, AST analysis, and dependency mapping — only user-story extraction is skipped.

## 3. Run

```bash
# Analyze the bundled COBOL samples
python reverse --source sample_data/cobol --source-lang cobol --target-lang java

# Java, with a custom report path and verbose output
python reverse --source sample_data/java --source-lang java --target-lang python \
    --report report.json --verbose

# Any codebase of yours
python reverse --source /path/to/legacy/code --source-lang cobol --target-lang java
```

Supported source languages: `cobol`, `smalltalk`, `java`, `python`, `javascript`, `fortran`, `pascal`.

## 4. What happens

1. **Discovery** — finds and catalogs all source files
2. **AST analysis** — parses files with tree-sitter (entities, complexity)
3. **Dependency mapping** — builds the dependency graph, detects cycles, computes layers
4. **User-story extraction** — an LLM turns each file's business logic into user stories (needs API key)
5. **Report** — a JSON report is written (default: `workflow_report.json`)

View the report:

```bash
python -m json.tool workflow_report.json
```

## 5. Optional extras

**LangSmith tracing** — full observability of every run:

```bash
echo "ENABLE_LANGSMITH=true" >> .env
echo "LANGSMITH_API_KEY=lsv2_pt_..." >> .env
echo "LANGSMITH_PROJECT=codelore" >> .env
```
Then view traces at https://smith.langchain.com. Details: [docs/LANGSMITH_SETUP.md](docs/LANGSMITH_SETUP.md)

**Smalltalk grammars** — required before analyzing Smalltalk code:

```bash
python scripts/build_smalltalk_grammar.py
```

## Troubleshooting

- **Import errors**: run from the project root; the CLI adds the right paths itself.
- **Missing dependencies**: `pip install -r requirements.txt`
- **No user stories generated**: check that your API key is set in `.env` and valid.

## Next steps

- [README](README.md) — feature overview and Python API
- [examples/user_story_extraction/basic_usage.py](examples/user_story_extraction/basic_usage.py) — programmatic usage
- [docs/ROADMAP.md](docs/ROADMAP.md) — where the project is heading
