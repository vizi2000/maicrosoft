# CLAUDE.md - Maicrosoft AI Agent Rules

This file provides rules and constraints for AI agents (Claude, GPT, Gemini, etc.) when working with Maicrosoft - the Primitives-First AI Coding Framework.

## Project Overview

**Maicrosoft** is a framework for hallucination-free AI coding. Instead of generating arbitrary code, AI agents compose workflows from pre-validated primitives (particles, atoms, molecules).

## Core Architecture

```
USER REQUEST
    |
    v
+------------------+     Plan JSON      +-------------------+
|   BRAIN (AI)     | -----------------> |   BODY (Deterministic) |
|                  |                    |                   |
| - Intent parsing |   Validated Plan   | - Validation      |
| - Primitive      | <----------------- | - Compilation     |
|   selection      |                    | - Execution       |
+------------------+                    +-------------------+
```

**Critical Principle**: AI generates Plan JSON referencing primitives by ID. AI NEVER writes executable code directly.

---

## ABSOLUTE RULES (NON-NEGOTIABLE)

### Rule 1: PRIMITIVES-ONLY

```
AI NEVER writes executable code (Python, JavaScript, SQL, etc.)
AI ONLY references primitives by ID (P001, A001, M001, etc.)
```

**Allowed**:
```yaml
nodes:
  - id: "fetch_user"
    primitive_id: "P001"  # http_call particle
    inputs:
      method: "GET"
      url: "{{ config.api }}/users/{{ user_id }}"
```

**FORBIDDEN**:
```python
# AI must NEVER generate this
def fetch_user(user_id):
    response = requests.get(f"{api}/users/{user_id}")
    return response.json()
```

### Rule 2: REGISTRY-FIRST

Before ANY task, AI MUST:
1. Query the primitives registry
2. Verify primitive exists and is `stable` status
3. Check primitive interface (inputs/outputs)

```bash
# Use MCP tools
list_particles()           # Get all particles
get_primitive("P001")      # Get specific primitive
find_similar("send email") # Semantic search
```

### Rule 3: NO GUESSING

- Unknown primitive ID = ERROR (never guess)
- Unknown field = ERROR (never assume)
- Missing input = ASK USER (never default)

### Rule 4: INTERFACE COMPLIANCE

All inputs MUST match the primitive's interface schema:
- Correct types (string, number, object, etc.)
- Required fields provided
- Enum values from allowed list only

### Rule 5: HYBRID MODE (Escape Hatch)

When NO primitive exists and `allow_fallback: true`:

```yaml
- id: "custom_logic"
  primitive_id: null
  fallback:
    language: "javascript"  # python or javascript only
    code: |
      // MAX 500 CHARACTERS
      const x = $input.first().json;
      return [{json: {result: x.a + x.b}}];
    description: "Add two numbers"
    inputs_schema: {a: "number", b: "number"}
    outputs_schema: {result: "number"}
```

**Fallback Constraints**:
- Max 500 characters of code
- NO network access (sandboxed)
- NO file system access
- REQUIRES human review flag
- Auto-logged for future primitive extraction

---

## Available Primitives (Particles)

### Base Particles (P001-P010)

| ID | Name | Description |
|----|------|-------------|
| P001 | http_call | Make any HTTP request |
| P002 | db_query | Execute SQL queries |
| P003 | file_op | Read/write/delete files |
| P004 | transform | JSON/XML/CSV transformations |
| P005 | branch | Conditional logic (if/else) |
| P006 | loop | Iteration over arrays |
| P007 | llm_call | AI model invocation |
| P008 | cache | Get/set cache values |
| P009 | queue | Publish/subscribe messages |
| P010 | log | Structured logging |

### Using Particles

```yaml
# Example: Fetch data, transform, and store
nodes:
  - id: "fetch"
    primitive_id: "P001"
    inputs:
      method: "GET"
      url: "https://api.example.com/data"

  - id: "transform"
    primitive_id: "P004"
    inputs:
      operation: "map"
      source: "{{ ref: fetch.body }}"
      template: |
        {
          "name": "{{ item.firstName }} {{ item.lastName }}",
          "email": "{{ item.email | lower }}"
        }

  - id: "store"
    primitive_id: "P002"
    inputs:
      query: "INSERT INTO users (name, email) VALUES ($1, $2)"
      params: ["{{ ref: transform.result.name }}", "{{ ref: transform.result.email }}"]
```

---

## Plan JSON Format

### Required Structure

```yaml
metadata:
  id: "plan-unique-id"
  name: "Human-readable name"
  version: "1.0.0"

settings:
  allow_fallback: false  # Enable hybrid mode
  risk_level: "low"      # low, medium, high

trigger:
  type: "webhook"  # webhook, schedule, manual, event
  config: {}

nodes:
  - id: "step_1"
    primitive_id: "P001"
    inputs: {}

edges:
  - from_node: "step_1"
    to_node: "step_2"
```

### Reference Syntax

```yaml
# Reference another node's output
"{{ ref: node_id.output_field }}"

# Reference input parameters
"{{ input.param_name }}"

# Reference config values
"{{ config.api_key }}"

# Reference loop item
"{{ item.field }}"
```

---

## Workflow for AI Agents

### Step 1: Understand Intent
Parse user request to extract:
- Required operations
- Data flow
- Expected outputs

### Step 2: Search Registry
```
find_similar_primitives("send email notification")
→ Returns: [P001 (http_call), P007 (llm_call for content)]
```

### Step 3: Compose Plan
Build Plan JSON using only found primitives.

### Step 4: Validate
```
validate_plan(plan)
→ Returns: {valid: true/false, violations: [], warnings: []}
```

### Step 5: Present to User
Show the plan for approval before compilation.

### Step 6: Compile (After Approval)
```
compile_plan(plan, target="n8n")
→ Returns: N8N workflow JSON
```

---

## Error Handling

### When Primitive Not Found

1. **Search alternatives**: Try semantic search
2. **Suggest composition**: Can multiple particles achieve the goal?
3. **Request hybrid mode**: If `allow_fallback: true`, suggest code block
4. **Escalate**: Ask user to create new primitive

### When Validation Fails

1. Read violation message carefully
2. Fix the specific issue (type, required field, etc.)
3. Re-validate
4. NEVER bypass validation

---

## MCP Tools Available

When connected via MCP server:

| Tool | Description |
|------|-------------|
| `list_particles()` | Get all available particles |
| `get_primitive(id)` | Get primitive definition |
| `find_similar(query)` | Semantic search for primitives |
| `validate_plan(plan)` | Validate Plan JSON |
| `compile_plan(plan, target)` | Compile to N8N/Python |

---

## Self-Test Checklist

Before submitting ANY plan, verify:

- [ ] All `primitive_id` values exist in registry
- [ ] All required inputs are provided
- [ ] All input types match interface schema
- [ ] All `{{ ref: }}` point to existing node outputs
- [ ] No circular dependencies between nodes
- [ ] `allow_fallback` is set if using code blocks
- [ ] Code blocks are under 500 characters

---

## Example: Complete Plan

```yaml
metadata:
  id: "plan-invoice-processor"
  name: "Invoice Email Processor"
  version: "1.0.0"

settings:
  allow_fallback: false
  risk_level: "medium"

trigger:
  type: "schedule"
  config:
    cron: "0 9 * * *"  # Daily at 9 AM

nodes:
  - id: "fetch_emails"
    primitive_id: "P001"
    inputs:
      method: "GET"
      url: "{{ config.imap_api }}/inbox"
      headers:
        Authorization: "Bearer {{ config.email_token }}"

  - id: "filter_invoices"
    primitive_id: "P005"
    inputs:
      condition: "{{ item.subject | contains('invoice') }}"
      source: "{{ ref: fetch_emails.body.messages }}"

  - id: "extract_data"
    primitive_id: "P007"
    inputs:
      model: "claude-sonnet-4-5"
      prompt: |
        Extract invoice data from this email:
        {{ ref: filter_invoices.current }}

        Return JSON: {invoice_number, amount, due_date, vendor}
      output_schema:
        type: object
        properties:
          invoice_number: {type: string}
          amount: {type: number}
          due_date: {type: string}
          vendor: {type: string}

  - id: "store_invoice"
    primitive_id: "P002"
    inputs:
      query: |
        INSERT INTO invoices (number, amount, due_date, vendor)
        VALUES ($1, $2, $3, $4)
      params:
        - "{{ ref: extract_data.response.invoice_number }}"
        - "{{ ref: extract_data.response.amount }}"
        - "{{ ref: extract_data.response.due_date }}"
        - "{{ ref: extract_data.response.vendor }}"

  - id: "notify_finance"
    primitive_id: "P001"
    inputs:
      method: "POST"
      url: "{{ config.slack_webhook }}"
      body:
        text: "New invoice processed: {{ ref: extract_data.response.invoice_number }}"

edges:
  - from_node: "fetch_emails"
    to_node: "filter_invoices"
  - from_node: "filter_invoices"
    to_node: "extract_data"
  - from_node: "extract_data"
    to_node: "store_invoice"
  - from_node: "store_invoice"
    to_node: "notify_finance"
```

---

## Remember

> **AI writes Plans, not Code.**
> **Primitives are validated, code is not.**
> **When in doubt, ask the registry.**

Created by The Collective BORG.tools by assimilation of best technology and human assets.
