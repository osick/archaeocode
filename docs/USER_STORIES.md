# User Story Extraction

## Overview

The User Story Extraction feature automatically generates business-focused user stories from legacy code using Large Language Models (LLMs).

## ✨ What It Does

Analyzes your legacy code and generates:
- **User stories** in INVEST format
- **Acceptance criteria** in Given-When-Then format
- **Priority rankings** (High/Medium/Low)
- **Complexity estimates** (Fibonacci scale: 1, 2, 3, 5, 8, 13)
- **Code mapping** to source files

## 🚀 Quick Setup

### Step 1: Get an API Key

Choose one:

**Option A: Anthropic Claude** (Recommended)
1. Sign up at https://console.anthropic.com/
2. Create an API key
3. Copy it (starts with `sk-ant-...`)

**Option B: OpenAI GPT-4**
1. Sign up at https://platform.openai.com/
2. Create an API key
3. Copy it (starts with `sk-...`)

### Step 2: Configure Environment

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key
nano .env  # or use your favorite editor
```

Add this line to `.env`:
```bash
# For Claude
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

# OR for GPT-4
OPENAI_API_KEY=sk-your-actual-key-here
```

### Step 3: Run Workflow

```bash
python archaeo --source ./sample_data --source-lang cobol --target-lang java
```

## 📖 Example Output

### Console Output

```
📖 Extracting user stories from code...
  Analyzing 3 code files...
  [1/3] Analyzing sample_data/cobol/CUSTMGMT.cob...
    ✓ Generated story: Customer Balance Processing
  [2/3] Analyzing sample_data/cobol/PAYMENT.cob...
    ✓ Generated story: Payment Validation and Application
  [3/3] Analyzing sample_data/java/CustomerService.java...
    ✓ Generated story: Customer Management Service

✅ Generated 3 user stories

📋 User Stories Generated:
  1. Customer Balance Processing (High priority, 8 points)
  2. Payment Validation and Application (Medium priority, 5 points)
  3. Customer Management Service (Low priority, 3 points)
```

### Generated Report (workflow_report.json)

```json
{
  "user_stories": [
    {
      "title": "Customer Balance Processing",
      "user_role": "customer service representative",
      "capability": "view and process customer account balances",
      "benefit": "I can quickly identify active customers and their financial status",
      "priority": "High",
      "complexity": 8,
      "confidence": 0.85,
      "acceptance_criteria": [
        "Given an active customer record, When the system processes the file, Then it displays customer ID, name, and balance",
        "Given multiple customer records, When processing completes, Then the system shows total customers processed and total balance",
        "Given an inactive customer, When processing the file, Then the customer is skipped and not included in totals"
      ],
      "code_files": ["sample_data/cobol/CUSTMGMT.cob"]
    }
  ]
}
```

### Markdown Format

The CLI can also generate markdown format user stories:

```markdown
### User Story: Customer Balance Processing

**Priority**: High | **Complexity**: 8 points | **Confidence**: 0.85

As a **customer service representative**,
I want to **view and process customer account balances**,
So that **I can quickly identify active customers and their financial status**.

**Acceptance Criteria**:
1. Given an active customer record, When the system processes the file, Then it displays customer ID, name, and balance
2. Given multiple customer records, When processing completes, Then the system shows total customers processed and total balance
3. Given an inactive customer, When processing the file, Then the customer is skipped and not included in totals

**Code Mapping**:
- Files: sample_data/cobol/CUSTMGMT.cob
```

## ⚙️ Configuration

### Environment Variables

Edit `.env` to customize:

```bash
# Model selection
MODEL_NAME=claude-3-5-sonnet-20241022
# Alternatives:
# MODEL_NAME=claude-3-opus-20240229  # Most capable
# MODEL_NAME=gpt-4-turbo-preview      # OpenAI alternative

# Story generation settings
USER_STORY_MAX_CODE_LENGTH=500  # Max code length to analyze
USER_STORY_TEMPERATURE=0.3       # Lower = more consistent, Higher = more creative
```

### Limiting Files Analyzed

By default, user story extraction analyzes the first 5 files. To change this, edit:

`src/orchestration/nodes/user_story_node.py:267`

```python
artifacts_to_analyze = state["code_artifacts"][:10]  # Analyze first 10 files
```

## 🎯 Use Cases

### 1. Requirements Recovery

**Scenario**: You have legacy COBOL code but lost the original requirements.

**Solution**: Extract user stories to recover business requirements.

```bash
python archaeo --source ./legacy_cobol --source-lang cobol --target-lang java
```

### 2. Migration Planning

**Scenario**: Planning a migration to Java and need to estimate effort.

**Solution**: User stories provide complexity estimates for planning.

```bash
python archaeo --source ./old_system --source-lang cobol --target-lang java --report migration_plan.json
```

### 3. Stakeholder Communication

**Scenario**: Business stakeholders don't understand technical code.

**Solution**: Show them user stories in plain language.

```bash
python archaeo --source ./codebase --source-lang java --target-lang kotlin
# Share workflow_report.json with stakeholders
```

## 🔍 How It Works

1. **Code Analysis**: Each file is analyzed for business logic
2. **LLM Processing**: Code is sent to Claude/GPT-4 with a specialized prompt
3. **Story Generation**: LLM generates user story in INVEST format
4. **Validation**: Stories are validated for completeness
5. **Ranking**: Stories are prioritized and ranked by complexity

## 💡 Tips for Better Results

### 1. Use Meaningful File Names

✅ **Good**: `CustomerPaymentProcessor.cob`, `AccountValidator.java`
❌ **Bad**: `PROG001.cob`, `temp.java`

### 2. Smaller Files Work Better

- Files under 200 lines: Excellent results
- Files 200-500 lines: Good results (may be chunked)
- Files over 500 lines: Split into modules first

### 3. Add Business Context

If you have business documentation, include it in a README:

```bash
echo "This is a payment processing system for retail banking" > ./codebase/README.md
python archaeo --source ./codebase --source-lang cobol --target-lang java
```

### 4. Use Descriptive Variable Names

Code with descriptive names generates better stories:

```cobol
✅ CUSTOMER-BALANCE
❌ WS-VAR-01
```

## 📊 Quality Metrics

Each user story includes a **confidence score** (0.0 - 1.0):

- **0.8 - 1.0**: High confidence, minimal review needed
- **0.6 - 0.8**: Good confidence, minor review recommended
- **0.4 - 0.6**: Medium confidence, detailed review required
- **Below 0.4**: Low confidence, may need manual rewrite

## 🚨 Troubleshooting

### "No LLM API key found"

**Problem**: Workflow skips user story extraction.

**Solution**:
```bash
# Check .env file exists
ls -la .env

# Verify API key is set
cat .env | grep API_KEY

# If missing, add it
echo "ANTHROPIC_API_KEY=sk-ant-your-key" >> .env
```

### "Rate limit exceeded"

**Problem**: Too many requests to API.

**Solution**: Reduce files analyzed or add delay:

```python
# In user_story_node.py
import time
...
for artifact in artifacts_to_analyze:
    story = self.generate_story_for_artifact(artifact)
    time.sleep(1)  # Add 1 second delay between files
```

### "Generated stories are too technical"

**Problem**: Stories focus on implementation, not business value.

**Solution**: Modify the prompt in `user_story_node.py:127`:

```python
prompt = f"""...
Focus HEAVILY on BUSINESS VALUE, not technical implementation.
Imagine explaining to a non-technical executive.
Use simple language that a business stakeholder would understand.
..."""
```

## 💰 Cost Estimation

### Anthropic Claude

- **Input**: ~$3 per million tokens
- **Output**: ~$15 per million tokens

**Typical costs**:
- Small file (100 lines): ~$0.001
- Medium file (500 lines): ~$0.005
- Large codebase (1000 files): ~$5-10

### OpenAI GPT-4

- **Input**: ~$10 per million tokens
- **Output**: ~$30 per million tokens

**Typical costs**:
- Small file: ~$0.003
- Medium file: ~$0.015
- Large codebase: ~$15-30

## 🔐 Security & Privacy

- **API keys** are stored in `.env` (not committed to git)
- **Code** is sent to Claude/OpenAI APIs for processing
- **Data** is NOT stored by default (unless using LangSmith tracing)

For sensitive code:
1. Use a self-hosted LLM instead
2. Or run on a subset of non-sensitive files
3. Or disable user story extraction entirely

## 🎓 Research Foundation

Based on the September 2025 research paper:
**"Reverse Engineering User Stories from Code using Large Language Models"** ([arxiv:2509.19587](https://arxiv.org/abs/2509.19587))

Key findings:
- **0.8 F1 score** for code up to 200 lines
- **Few-shot learning** improves quality significantly
- **Validated** on 1,750 code snippets

## 📚 Additional Resources

- [INVEST Criteria](https://en.wikipedia.org/wiki/INVEST_(mnemonic)) - User story best practices
- [Given-When-Then](https://martinfowler.com/bliki/GivenWhenThen.html) - Acceptance criteria format
- [Story Points Guide](https://www.atlassian.com/agile/project-management/estimation) - Complexity estimation

## 🆘 Need Help?

1. Check `.env` file has valid API key
2. Try with sample data first: `python archaeo --source ./sample_data`
3. Review the logs for specific error messages
4. Check API key has sufficient credits

---

**Next**: See [QUICKSTART.md](../QUICKSTART.md) for running your first workflow
