# Quick Start: Your First Dig

From clone to your first excavated user story in about five minutes. No prior fieldwork required.

## 1. Pack the tools

```bash
git clone https://github.com/osick/archaeocode.git
cd archaeocode
pip install -r requirements.txt
pip install -e .        # optional: puts `archaeo` and `archaeo-kb` on your PATH
```

## 2. Hire an interpreter (optional, for user stories and questions)

```bash
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY (or OPENAI_API_KEY)
```

Without an API key the expedition still runs discovery, AST analysis, dependency mapping, and knowledge-base indexing. Only the two steps that need someone to *read* the code for meaning are skipped: user-story extraction and natural-language answers.

## 3. Break ground

```bash
# The bundled COBOL site
python archaeo --source sample_data/cobol --source-lang cobol --target-lang java

# Java, with a custom report path and verbose output
python archaeo --source sample_data/java --source-lang java --target-lang python \
    --report report.json --verbose

# Your own site
python archaeo --source /path/to/legacy/code --source-lang cobol --target-lang java
```

Supported source languages: `cobol`, `smalltalk`, `java`, `python`, `javascript`, `fortran`, `pascal`.

## 4. What happens down there

1. **Discovery** — surveys the site and catalogs every source file
2. **AST analysis** — brushes off the dirt with tree-sitter (entities, complexity)
3. **Dependency mapping** — reconstructs who called whom: graph, cycles, layers
4. **User-story extraction** — an LLM asks "what was this *for*?" and writes user stories (needs API key)
5. **Report** — a JSON report is written (default: `workflow_report.json`)

View the report:

```bash
python -m json.tool workflow_report.json
```

## 5. Keep the finds (the knowledge base)

Add one flag and the run is filed into a knowledge graph instead of evaporating into a JSON file:

```bash
python archaeo --source sample_data/cobol --source-lang cobol --knowledge-base --kb-wiki ./wiki
```

Then interrogate the archive:

```bash
archaeo-kb retrieve "PAYMENT" --mode local                    # entities, relations, code — no API key needed
archaeo-kb graph "PAYMENT.cob"                                # what does this program touch?
archaeo-kb query "Which programs touch the customer file?"    # a real answer — needs an LLM key
archaeo-kb stats                                              # how big is the museum?
```

Open `./wiki/index.md` in Obsidian (or any Markdown viewer) for one page per file, function, dependency, and user story, cross-linked. Add `--kb-extract` to also let the LLM dig out business vocabulary. By default everything lives in `data/knowledge_base/` as plain files; for a site the size of a core-banking system, point it at Neo4j / Postgres / Qdrant via `KB_*` variables. The full story: [docs/KNOWLEDGE_MANAGEMENT.md](docs/KNOWLEDGE_MANAGEMENT.md).

## 6. Optional extras

**LangSmith tracing** — full observability of every run:

```bash
echo "ENABLE_LANGSMITH=true" >> .env
echo "LANGSMITH_API_KEY=lsv2_pt_..." >> .env
echo "LANGSMITH_PROJECT=archaeocode" >> .env
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
- **`archaeo-kb query` says no LLM configured**: same fix, or use `retrieve` / `graph` / `stats`, which never need one.
- **Knowledge base can't download models** (air-gapped site): set `KB_TOKENIZER=bytes` and `KB_EMBEDDING_PROVIDER=hashing`, or point `KB_EMBEDDING_PROVIDER=ollama` at a local Ollama.

## Next steps

- [README](README.md) — feature overview and Python API
- [examples/user_story_extraction/basic_usage.py](examples/user_story_extraction/basic_usage.py) — programmatic usage
- [examples/knowledge_base/query_knowledge_base.py](examples/knowledge_base/query_knowledge_base.py) — build and query the knowledge base
- [docs/ROADMAP.md](docs/ROADMAP.md) — where the expedition is heading
