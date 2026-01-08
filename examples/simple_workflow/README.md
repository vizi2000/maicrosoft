# Simple Workflow Example

This example demonstrates a basic Maicrosoft workflow that:

1. Fetches user data from an API
2. Transforms the data to extract specific fields
3. Filters the results
4. Logs the output

## Structure

```
simple_workflow/
├── plan.yaml     # The workflow definition
└── README.md     # This file
```

## Running the Example

```bash
# Validate the plan
maicrosoft validate examples/simple_workflow/plan.yaml

# Compile to N8N (when implemented)
maicrosoft compile examples/simple_workflow/plan.yaml -t n8n
```

## Particles Used

| ID | Name | Purpose |
|----|------|---------|
| P001 | http_call | Fetch data from API |
| P004 | transform | Map and filter data |
| P010 | log | Log results |

## Notes

- The plan uses only stable particles
- No code fallback is used
- All inputs are validated against particle interfaces
