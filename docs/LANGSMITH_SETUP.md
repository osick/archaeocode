# LangSmith Observability Setup

This guide explains how to enable LangSmith tracing for full observability of your reverse engineering workflows.

## What is LangSmith?

LangSmith is LangChain's observability and monitoring platform that provides:

- **Trace Visualization**: See every step of your workflow execution
- **Performance Metrics**: Track latency, token usage, and costs
- **Debugging Tools**: Inspect inputs/outputs for each node
- **Error Tracking**: Capture and analyze failures
- **Compliance**: SOC 2, GDPR, and HIPAA compliant
- **Team Collaboration**: Share traces and insights with your team

## Quick Start

### 1. Sign Up for LangSmith

Visit [https://smith.langchain.com](https://smith.langchain.com) and create a free account.

### 2. Get Your API Key

1. Log in to LangSmith
2. Click on your profile (top right)
3. Select "Settings"
4. Navigate to "API Keys"
5. Click "Create API Key"
6. Copy your new API key

### 3. Configure Environment

Add your LangSmith API key to your `.env` file:

```bash
# Copy example file
cp .env.example .env

# Edit .env and add your keys
nano .env
```

Add these lines to `.env`:

```bash
# LangSmith Configuration
ENABLE_LANGSMITH=true
LANGSMITH_API_KEY=lsv2_pt_your_api_key_here
LANGSMITH_PROJECT=archaeocode
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

### 4. Run Your Workflow

```bash
python archaeo --source ./sample_data --source-lang cobol --target-lang java
```

You should see:

```
✅ LangSmith tracing enabled
   Project: archaeocode
   Endpoint: https://api.smith.langchain.com
```

### 5. View Traces in LangSmith

1. Open [https://smith.langchain.com](https://smith.langchain.com)
2. Navigate to your project: `archaeocode`
3. Click on a trace to see detailed execution flow

## Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENABLE_LANGSMITH` | Enable/disable tracing | `false` | No |
| `LANGSMITH_API_KEY` | Your LangSmith API key | - | Yes |
| `LANGSMITH_PROJECT` | Project name in LangSmith | `archaeocode` | No |
| `LANGSMITH_ENDPOINT` | LangSmith API endpoint | `https://api.smith.langchain.com` | No |

### YAML Configuration

Edit `config/langgraph_config.yaml`:

```yaml
langsmith:
  enabled: true
  deployment: "cloud"  # Options: "cloud", "eu_cloud", "self_hosted"
  project_name: "archaeocode"
  tracing:
    enabled: true
    sample_rate: 1.0  # 100% of runs
    capture_input: true
    capture_output: true
    capture_errors: true
```

## What Gets Traced?

### Workflow Metadata

Every workflow run includes:

- Workflow ID
- Source and target languages
- Source code path
- Start time and duration
- Success/failure status

### Node Execution

Each node traces:

- **Discovery Node**: Files discovered, lines of code, language breakdown
- **AST Analysis**: Files parsed, entities extracted, complexity metrics
- **Dependency Mapping**: Dependencies found, circular dependencies, layers
- **User Story Extraction**: Stories generated, LLM calls, token usage

### LLM Calls

All LLM interactions include:

- Model name (e.g., Claude 3.5 Sonnet)
- Prompt text
- Completion text
- Token counts (input/output)
- Latency
- Cost estimation

## Viewing Traces

### Trace List View

Navigate to your project to see all traces:

- **Status**: Success/Error indicators
- **Duration**: How long the workflow took
- **Tags**: Filter by `source:cobol`, `target:java`, etc.
- **Metadata**: Workflow ID, languages, paths

### Detailed Trace View

Click on a trace to see:

1. **Timeline**: Visual representation of node execution
2. **Node Details**: Inputs, outputs, and state for each step
3. **LLM Calls**: All prompts and completions
4. **Errors**: Stack traces and error messages
5. **Performance**: Latency breakdown by node

### Example Trace

```
📊 Workflow: ace11b17-28a4-4489-a730-d7adab91547d
├─ 🔍 discovery (150ms)
│  └─ Output: 2 files, 171 lines
├─ 🌳 ast_analysis (300ms)
│  └─ Output: 0 entities (placeholder)
├─ 🔗 dependency_mapping (100ms)
│  └─ Output: 0 edges
└─ 📖 user_story_extraction (2.5s)
   ├─ LLM Call: Claude 3.5 Sonnet
   ├─ Tokens: 1,250 in, 450 out
   ├─ Cost: $0.015
   └─ Output: 2 user stories
```

## Filtering and Searching

### By Tags

Traces are automatically tagged with:

- `source:cobol`, `source:fortran`, `source:pascal`, etc.
- `target:java`, `target:python`, etc.
- `reverse-engineering`
- `migration`
- `langgraph`

### By Metadata

Filter traces by:

- Workflow ID
- Source/target language
- Date range
- Success/failure status

### Search

Search trace content:

- Input/output text
- Error messages
- Node names
- Custom metadata

## Cost Tracking

### Token Usage

LangSmith automatically tracks:

- Total tokens per workflow
- Tokens per node
- Tokens per LLM call
- Input vs output tokens

### Cost Estimation

Approximate costs based on:

- **Claude 3.5 Sonnet**: $3 per million input tokens, $15 per million output tokens
- **GPT-4 Turbo**: $10 per million input tokens, $30 per million output tokens

### Example Cost Breakdown

For a typical COBOL → Java migration:

```
Discovery Node:        0 tokens, $0.00
AST Analysis:          0 tokens, $0.00
Dependency Mapping:    0 tokens, $0.00
User Story Extraction: 1,700 tokens, $0.015
----------------------------------------
Total:                 1,700 tokens, $0.015
```

## Debugging with LangSmith

### Common Issues

#### 1. Workflow Fails at User Story Extraction

**Trace shows:**
- LLM call with error
- Token limit exceeded or API rate limit

**Solution:**
- Reduce `USER_STORY_MAX_CODE_LENGTH` in `.env`
- Wait and retry for rate limits

#### 2. Low Quality User Stories

**Trace shows:**
- Valid LLM call but poor output quality

**Solution:**
- Review prompt in trace
- Adjust `USER_STORY_TEMPERATURE` (lower = more deterministic)
- Check code quality (garbage in = garbage out)

#### 3. High Costs

**Trace shows:**
- Excessive token usage

**Solution:**
- Filter code files before processing
- Use cheaper models for initial analysis
- Cache results where possible

## Privacy and Security

### Data Sent to LangSmith

LangSmith receives:

- Workflow metadata (IDs, languages, paths)
- Code snippets sent to LLMs
- LLM prompts and completions
- Node inputs/outputs
- Error messages and stack traces

### Data NOT Sent

- Full source code files (unless sent to LLM)
- Database credentials (filtered from traces)
- API keys (filtered from traces)

### Compliance

LangSmith is:

- **SOC 2 Type II** certified
- **GDPR** compliant
- **HIPAA** compliant (Business Associate Agreement available)

### Data Retention

- Traces retained for 30 days (configurable)
- Can delete traces manually
- Can export traces for archival

## Self-Hosted LangSmith

For sensitive codebases, deploy LangSmith on-premises:

### 1. Deploy LangSmith

Follow the [self-hosted deployment guide](https://docs.smith.langchain.com/self_hosting).

### 2. Update Configuration

In `.env`:

```bash
LANGSMITH_ENDPOINT=http://your-langsmith-server:8000
```

In `config/langgraph_config.yaml`:

```yaml
langsmith:
  deployment: "self_hosted"
  endpoints:
    self_hosted: "http://your-langsmith-server:8000"
```

## Advanced Features

### Custom Metadata

Add custom metadata to traces:

```python
from src.orchestration.utils.tracing import create_run_metadata

metadata = create_run_metadata(
    workflow_id=workflow_id,
    source_language="cobol",
    target_language="java",
    additional={
        "team": "modernization",
        "customer": "acme-corp",
        "environment": "production"
    }
)
```

### Custom Tags

Add custom tags:

```python
from src.orchestration.utils.tracing import create_run_tags

tags = create_run_tags(
    source_language="cobol",
    target_language="java",
    additional_tags=["priority-high", "customer-acme"]
)
```

### Sampling

Trace only a percentage of runs:

```yaml
langsmith:
  tracing:
    sample_rate: 0.1  # Trace 10% of runs
```

## Troubleshooting

### LangSmith Not Enabled

**Symptom**: No trace message in output

**Check:**

1. `ENABLE_LANGSMITH=true` in `.env`
2. `.env` file in project root
3. API key is valid

**Test:**

```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('ENABLE_LANGSMITH'))"
```

### Invalid API Key

**Symptom**: Warning message about missing key

**Solution:**

1. Verify key starts with `lsv2_pt_`
2. Regenerate key in LangSmith UI
3. Update `.env` file

### No Traces Appear

**Check:**

1. Network connectivity to LangSmith
2. Firewall not blocking `api.smith.langchain.com`
3. API key has correct permissions

### Traces Too Large

**Symptom**: Traces fail to upload

**Solution:**

1. Reduce code sent to LLMs
2. Disable input/output capture:

```yaml
langsmith:
  tracing:
    capture_input: false
    capture_output: false
```

## Resources

- [LangSmith Documentation](https://docs.smith.langchain.com)
- [LangSmith Pricing](https://www.langchain.com/pricing)
- [LangSmith Status](https://status.smith.langchain.com)
- [LangChain Discord](https://discord.gg/langchain)

## Next Steps

1. ✅ **Set up LangSmith** (you're here!)
2. Run workflows and view traces
3. Set up alerts for failures
4. Create dashboards for team visibility
5. Export traces for compliance

---

**Questions?** See our [GitHub Discussions](https://github.com/osick/archaeocode/discussions)
