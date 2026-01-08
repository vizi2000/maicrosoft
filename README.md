# Maicrosoft

**Framework for Hallucination-Free AI Coding**

Maicrosoft forces AI agents to compose workflows from pre-validated primitives instead of generating arbitrary code. This eliminates hallucinations in AI-generated automation.

## The Problem

Traditional AI coding:
```
User: "Build me an invoice processor"
AI: *generates 500 lines of Python with made-up APIs and bugs*
```

Maicrosoft approach:
```
User: "Build me an invoice processor"
AI: *composes validated primitives into a Plan*
    -> Plan validated against registry
    -> Plan compiled to N8N/Python
    -> Zero hallucinations, fully auditable
```

## Key Innovation: Micro-Primitives

Instead of building 30+ atoms upfront, Maicrosoft uses **10 base particles** that compose into higher-level abstractions on-demand:

| Particle | Description |
|----------|-------------|
| `http_call` | Make any HTTP request |
| `db_query` | Execute SQL queries |
| `file_op` | File read/write/delete |
| `transform` | JSON/XML/CSV transformations |
| `branch` | Conditional logic |
| `loop` | Iteration |
| `llm_call` | AI model invocation |
| `cache` | Get/set cache |
| `queue` | Pub/sub messages |
| `log` | Structured logging |

## Installation

```bash
pip install maicrosoft
# or
uv add maicrosoft
```

## Quick Start

### 1. Initialize Project

```bash
maicrosoft init my-automation
cd my-automation
```

### 2. Compose a Workflow

```bash
maicrosoft compose "Fetch invoices from email, extract data, save to database"
```

This generates a Plan JSON:

```yaml
nodes:
  - id: fetch_emails
    primitive_id: "P001"  # http_call
    inputs:
      method: GET
      url: "{{ config.imap_api }}/inbox"

  - id: extract_data
    primitive_id: "P007"  # llm_call
    inputs:
      prompt: "Extract invoice data..."

  - id: save_record
    primitive_id: "P002"  # db_query
    inputs:
      query: "INSERT INTO invoices..."
```

### 3. Validate

```bash
maicrosoft validate plan.yaml
```

### 4. Compile

```bash
maicrosoft compile plan.yaml -t n8n
# Outputs: N8N workflow JSON
```

### 5. Deploy

```bash
maicrosoft deploy --target n8n.example.com
```

## Hybrid Mode

When no primitive exists, Maicrosoft supports constrained code fallback:

```yaml
- id: "custom_logic"
  primitive_id: null
  fallback:
    language: "javascript"
    code: |
      // Max 500 chars, sandboxed, no network/file access
      return [{json: {result: $input.a + $input.b}}];
```

Code blocks are:
- Limited to 500 characters
- Sandboxed (no network/file access)
- Flagged for human review
- Auto-logged for future primitive extraction

## Architecture

```
+------------------+     Plan JSON      +-------------------+
|   BRAIN (AI)     | -----------------> |   BODY (Deterministic) |
|                  |                    |                   |
| - Intent parsing |   Validated Plan   | - Validation      |
| - Primitive      | <----------------- | - Compilation     |
|   selection      |                    | - Execution       |
+------------------+                    +-------------------+
```

**Critical Principle**: AI never writes executable code. It only references validated primitives by ID.

## Validation Pipeline

Every plan goes through 6 validation layers:

1. **Syntax** - JSON Schema validation
2. **Registry** - Primitive exists and is stable
3. **Interface** - Inputs match primitive schema
4. **Dependency** - No circular dependencies
5. **Policy** - Business rules (GDPR, SOC2, etc.)
6. **Compilation** - Target-specific compatibility

## CLI Commands

| Command | Description |
|---------|-------------|
| `maicrosoft init` | Initialize new project |
| `maicrosoft compose "..."` | AI-assisted plan composition |
| `maicrosoft validate` | Validate plan |
| `maicrosoft compile -t TARGET` | Compile to N8N/Python |
| `maicrosoft deploy` | Deploy to execution engine |
| `maicrosoft particles list` | Show available particles |
| `maicrosoft gaps` | Show missing primitives |

## MCP Integration

For AI agents (Claude, GPT, etc.), start the MCP server:

```bash
maicrosoft mcp serve --port 8080
```

Available tools:
- `list_particles` - Get all particles
- `get_primitive` - Get primitive definition
- `find_similar` - Semantic search
- `validate_plan` - Validate Plan JSON
- `compile_plan` - Compile to target

## When to Use Maicrosoft

**Best fit**:
- Enterprise automation requiring auditability
- Regulated industries (finance, healthcare)
- Repetitive processes (onboarding, invoicing)
- Multi-tenant SaaS

**Not ideal for**:
- One-off scripts
- R&D/exploration
- Real-time processing
- Creative tasks

## Project Structure

```
my-automation/
├── maicrosoft.yaml      # Project config
├── primitives/          # Custom primitives
│   ├── particles/
│   ├── atoms/
│   └── molecules/
├── plans/               # Workflow definitions
└── compiled/            # Generated outputs
```

## License

MIT

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

---

Created by The Collective BORG.tools by assimilation of best technology and human assets.
