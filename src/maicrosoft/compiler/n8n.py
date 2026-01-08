"""N8N Workflow Compiler.

Compiles Maicrosoft Plan JSON into N8N workflow JSON format.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from maicrosoft.core.models import (
    CodeBlock,
    Plan,
    PlanNode,
    Primitive,
    TriggerType,
)
from maicrosoft.registry.registry import PrimitiveRegistry


class N8NNode:
    """Represents an N8N workflow node."""

    def __init__(
        self,
        name: str,
        node_type: str,
        position: tuple[int, int],
        parameters: dict[str, Any] | None = None,
        type_version: int = 1,
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.type = node_type
        self.position = list(position)
        self.parameters = parameters or {}
        self.type_version = type_version

    def to_dict(self) -> dict[str, Any]:
        """Convert to N8N node dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "position": self.position,
            "parameters": self.parameters,
            "typeVersion": self.type_version,
        }


class N8NConnection:
    """Represents a connection between N8N nodes."""

    def __init__(
        self,
        source_node: str,
        target_node: str,
        source_index: int = 0,
        target_index: int = 0,
    ):
        self.source_node = source_node
        self.target_node = target_node
        self.source_index = source_index
        self.target_index = target_index


class N8NCompiler:
    """Compiles Maicrosoft plans to N8N workflow format."""

    # Mapping from particle ID to N8N node type
    PARTICLE_TO_N8N: dict[str, dict[str, Any]] = {
        "P001": {  # http_call
            "type": "n8n-nodes-base.httpRequest",
            "version": 4,
            "param_map": {
                "method": "method",
                "url": "url",
                "headers": "headerParameters",
                "body": "body",
                "query_params": "queryParameters",
                "timeout": "timeout",
                "auth": "authentication",
            },
        },
        "P002": {  # db_query
            "type": "n8n-nodes-base.postgres",
            "version": 2,
            "param_map": {
                "query": "query",
                "operation": "operation",
            },
        },
        "P003": {  # file_op
            "type": "n8n-nodes-base.readWriteFile",
            "version": 1,
            "param_map": {
                "operation": "operation",
                "path": "filePath",
                "content": "fileContent",
            },
        },
        "P004": {  # transform
            "type": "n8n-nodes-base.code",
            "version": 2,
            "custom_handler": "_compile_transform",
        },
        "P005": {  # branch
            "type": "n8n-nodes-base.if",
            "version": 2,
            "custom_handler": "_compile_branch",
        },
        "P006": {  # loop
            "type": "n8n-nodes-base.splitInBatches",
            "version": 3,
            "custom_handler": "_compile_loop",
        },
        "P007": {  # llm_call
            "type": "@n8n/n8n-nodes-langchain.openAi",
            "version": 1,
            "custom_handler": "_compile_llm_call",
        },
        "P008": {  # cache
            "type": "n8n-nodes-base.redis",
            "version": 1,
            "param_map": {
                "operation": "operation",
                "key": "key",
                "value": "value",
                "ttl": "expire",
            },
        },
        "P009": {  # queue
            "type": "n8n-nodes-base.rabbitmq",
            "version": 1,
            "param_map": {
                "operation": "operation",
                "queue": "queue",
                "message": "content",
            },
        },
        "P010": {  # log
            "type": "n8n-nodes-base.code",
            "version": 2,
            "custom_handler": "_compile_log",
        },
    }

    # Trigger type to N8N trigger node
    TRIGGER_TO_N8N: dict[str, dict[str, Any]] = {
        "webhook": {
            "type": "n8n-nodes-base.webhook",
            "version": 2,
            "parameters": {
                "httpMethod": "POST",
                "path": "webhook",
                "responseMode": "responseNode",
            },
        },
        "schedule": {
            "type": "n8n-nodes-base.scheduleTrigger",
            "version": 1,
            "parameters": {
                "rule": {"interval": [{"field": "hours", "hoursInterval": 1}]}
            },
        },
        "manual": {
            "type": "n8n-nodes-base.manualTrigger",
            "version": 1,
            "parameters": {},
        },
        "event": {
            "type": "n8n-nodes-base.webhook",
            "version": 2,
            "parameters": {
                "httpMethod": "POST",
                "path": "event",
            },
        },
    }

    def __init__(self, registry: PrimitiveRegistry | None = None):
        """Initialize compiler.

        Args:
            registry: Primitive registry for looking up definitions
        """
        self.registry = registry or PrimitiveRegistry()

    def compile(self, plan: Plan) -> dict[str, Any]:
        """Compile a plan to N8N workflow JSON.

        Args:
            plan: The plan to compile

        Returns:
            N8N workflow JSON dict
        """
        nodes: list[N8NNode] = []
        connections: dict[str, dict[str, list[list[dict[str, Any]]]]] = {}
        node_id_map: dict[str, str] = {}  # plan node id -> n8n node name

        # Position tracking
        x_pos = 250
        y_pos = 300
        x_step = 250
        y_step = 100

        # Add trigger node
        trigger_node = self._compile_trigger(plan)
        trigger_node.position = [x_pos, y_pos]
        nodes.append(trigger_node)
        node_id_map["__trigger__"] = trigger_node.name

        # Compile each plan node
        for i, plan_node in enumerate(plan.nodes):
            x_pos += x_step
            n8n_node = self._compile_node(plan_node, plan)
            n8n_node.position = [x_pos, y_pos + (i % 3) * y_step]
            nodes.append(n8n_node)
            node_id_map[plan_node.id] = n8n_node.name

        # Build connections
        connections = self._build_connections(plan, node_id_map, trigger_node.name)

        # Build workflow
        workflow = {
            "name": plan.metadata.name,
            "nodes": [node.to_dict() for node in nodes],
            "connections": connections,
            "active": False,
            "settings": {
                "executionOrder": "v1",
            },
            "versionId": str(uuid.uuid4()),
            "meta": {
                "maicrosoft_plan_id": plan.metadata.id,
                "maicrosoft_version": plan.metadata.version,
            },
        }

        return workflow

    def _compile_trigger(self, plan: Plan) -> N8NNode:
        """Compile plan trigger to N8N trigger node."""
        if plan.trigger is None:
            # Default to manual trigger
            trigger_type = "manual"
            config = {}
        else:
            trigger_type = plan.trigger.type.value
            config = plan.trigger.config

        trigger_def = self.TRIGGER_TO_N8N.get(
            trigger_type, self.TRIGGER_TO_N8N["manual"]
        )

        # Merge config with default parameters
        parameters = dict(trigger_def["parameters"])
        if trigger_type == "schedule" and "cron" in config:
            parameters["rule"] = {"cron": config["cron"]}
        elif trigger_type == "webhook" and "path" in config:
            parameters["path"] = config["path"]

        return N8NNode(
            name="Trigger",
            node_type=trigger_def["type"],
            position=(0, 0),
            parameters=parameters,
            type_version=trigger_def.get("version", 1),
        )

    def _compile_node(self, node: PlanNode, plan: Plan) -> N8NNode:
        """Compile a plan node to N8N node."""
        if node.fallback is not None:
            return self._compile_fallback(node)

        if node.primitive_id is None:
            raise ValueError(f"Node {node.id} has no primitive_id or fallback")

        # Get primitive definition
        primitive_id = node.primitive_id
        n8n_def = self.PARTICLE_TO_N8N.get(primitive_id)

        if n8n_def is None:
            # Try to compile as generic code node
            return self._compile_generic(node)

        # Check for custom handler
        if "custom_handler" in n8n_def:
            handler = getattr(self, n8n_def["custom_handler"])
            return handler(node, n8n_def)

        # Standard parameter mapping
        parameters = self._map_parameters(node.inputs, n8n_def.get("param_map", {}))

        return N8NNode(
            name=self._sanitize_name(node.id),
            node_type=n8n_def["type"],
            position=(0, 0),
            parameters=parameters,
            type_version=n8n_def.get("version", 1),
        )

    def _compile_fallback(self, node: PlanNode) -> N8NNode:
        """Compile a code fallback node."""
        if node.fallback is None:
            raise ValueError("Node has no fallback")

        code = self._wrap_fallback_code(node.fallback)

        return N8NNode(
            name=self._sanitize_name(node.id),
            node_type="n8n-nodes-base.code",
            position=(0, 0),
            parameters={
                "mode": "runOnceForAllItems",
                "jsCode": code,
            },
            type_version=2,
        )

    def _wrap_fallback_code(self, fallback: CodeBlock) -> str:
        """Wrap fallback code for N8N execution."""
        if fallback.language == "javascript":
            return f"""
// Maicrosoft Fallback Code: {fallback.description}
// Inputs: {json.dumps(fallback.inputs_schema)}
// Outputs: {json.dumps(fallback.outputs_schema)}

{fallback.code}
""".strip()
        elif fallback.language == "python":
            # N8N doesn't natively support Python, wrap in code node
            return f"""
// Maicrosoft Fallback: Python code (requires external execution)
// Description: {fallback.description}
// WARNING: Python fallback not directly executable in N8N

const pythonCode = `{fallback.code}`;
// TODO: Send to Python execution service
return $input.all();
""".strip()
        else:
            return fallback.code

    def _compile_transform(
        self, node: PlanNode, n8n_def: dict[str, Any]
    ) -> N8NNode:
        """Compile transform particle to N8N code node."""
        operation = node.inputs.get("operation", "map")
        source = node.inputs.get("source", "$input.all()")
        template = node.inputs.get("template", "")
        condition = node.inputs.get("condition", "true")

        # Resolve references
        source = self._resolve_reference(source)

        if operation == "map":
            code = f"""
// Transform: Map operation
const items = {source};
const results = items.map(item => {{
  return {template or "item"};
}});
return results.map(json => ({{json}}));
"""
        elif operation == "filter":
            code = f"""
// Transform: Filter operation
const items = {source};
const results = items.filter(item => {{
  return {condition};
}});
return results.map(json => ({{json}}));
"""
        elif operation == "reduce":
            code = f"""
// Transform: Reduce operation
const items = {source};
const result = items.reduce((acc, item) => {{
  {template or "return acc;"}
}}, {node.inputs.get("initial", "{}")});
return [{{json: result}}];
"""
        elif operation == "flatten":
            code = f"""
// Transform: Flatten operation
const items = {source};
const results = items.flat();
return results.map(json => ({{json}}));
"""
        else:
            code = f"""
// Transform: {operation}
const items = {source};
return items.map(json => ({{json}}));
"""

        return N8NNode(
            name=self._sanitize_name(node.id),
            node_type="n8n-nodes-base.code",
            position=(0, 0),
            parameters={
                "mode": "runOnceForAllItems",
                "jsCode": code.strip(),
            },
            type_version=2,
        )

    def _compile_branch(
        self, node: PlanNode, n8n_def: dict[str, Any]
    ) -> N8NNode:
        """Compile branch particle to N8N IF node."""
        condition = node.inputs.get("condition", "true")

        # Convert condition to N8N format
        return N8NNode(
            name=self._sanitize_name(node.id),
            node_type="n8n-nodes-base.if",
            position=(0, 0),
            parameters={
                "conditions": {
                    "options": {
                        "caseSensitive": True,
                        "leftValue": "",
                    },
                    "conditions": [
                        {
                            "leftValue": "={{ $json }}",
                            "rightValue": "",
                            "operator": {
                                "type": "boolean",
                                "operation": "true",
                            },
                        }
                    ],
                    "combinator": "and",
                },
            },
            type_version=2,
        )

    def _compile_loop(
        self, node: PlanNode, n8n_def: dict[str, Any]
    ) -> N8NNode:
        """Compile loop particle to N8N SplitInBatches node."""
        batch_size = node.inputs.get("batch_size", 1)

        return N8NNode(
            name=self._sanitize_name(node.id),
            node_type="n8n-nodes-base.splitInBatches",
            position=(0, 0),
            parameters={
                "batchSize": batch_size,
                "options": {},
            },
            type_version=3,
        )

    def _compile_llm_call(
        self, node: PlanNode, n8n_def: dict[str, Any]
    ) -> N8NNode:
        """Compile llm_call particle to N8N OpenAI node."""
        prompt = node.inputs.get("prompt", "")
        model = node.inputs.get("model", "gpt-4")
        system_prompt = node.inputs.get("system_prompt", "")
        temperature = node.inputs.get("temperature", 0.7)
        max_tokens = node.inputs.get("max_tokens", 1000)

        return N8NNode(
            name=self._sanitize_name(node.id),
            node_type="@n8n/n8n-nodes-langchain.openAi",
            position=(0, 0),
            parameters={
                "resource": "chat",
                "operation": "message",
                "model": model,
                "messages": {
                    "values": [
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ]
                },
                "options": {
                    "temperature": temperature,
                    "maxTokens": max_tokens,
                },
            },
            type_version=1,
        )

    def _compile_log(
        self, node: PlanNode, n8n_def: dict[str, Any]
    ) -> N8NNode:
        """Compile log particle to N8N code node."""
        level = node.inputs.get("level", "info")
        message = node.inputs.get("message", "")
        data = node.inputs.get("data", {})

        code = f"""
// Log: {level.upper()}
console.log('{level.upper()}: {message}');
console.log('Data:', {json.dumps(data)});

// Pass through input data
return $input.all();
"""

        return N8NNode(
            name=self._sanitize_name(node.id),
            node_type="n8n-nodes-base.code",
            position=(0, 0),
            parameters={
                "mode": "runOnceForAllItems",
                "jsCode": code.strip(),
            },
            type_version=2,
        )

    def _compile_generic(self, node: PlanNode) -> N8NNode:
        """Compile unknown primitive as generic code node."""
        return N8NNode(
            name=self._sanitize_name(node.id),
            node_type="n8n-nodes-base.code",
            position=(0, 0),
            parameters={
                "mode": "runOnceForAllItems",
                "jsCode": f"""
// Generic node for primitive: {node.primitive_id}
// Inputs: {json.dumps(node.inputs)}
return $input.all();
""".strip(),
            },
            type_version=2,
        )

    def _map_parameters(
        self, inputs: dict[str, Any], param_map: dict[str, str]
    ) -> dict[str, Any]:
        """Map plan inputs to N8N parameters."""
        parameters: dict[str, Any] = {}

        for input_name, value in inputs.items():
            n8n_param = param_map.get(input_name, input_name)

            # Resolve references
            if isinstance(value, str) and "{{ ref:" in value:
                value = self._resolve_reference(value)

            # Handle nested parameters
            if "." in n8n_param:
                parts = n8n_param.split(".")
                current = parameters
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                parameters[n8n_param] = value

        return parameters

    def _resolve_reference(self, value: str) -> str:
        """Resolve {{ ref: node.output }} to N8N expression."""
        if not isinstance(value, str):
            return value

        if "{{ ref:" in value:
            # Extract reference
            import re

            match = re.search(r"\{\{\s*ref:\s*([^}]+)\s*\}\}", value)
            if match:
                ref = match.group(1).strip()
                parts = ref.split(".")
                node_id = parts[0]
                output_field = ".".join(parts[1:]) if len(parts) > 1 else "body"

                # Convert to N8N expression
                n8n_expr = f"$('{{{{ $node[\"{node_id}\"].json.{output_field} }}}}')"
                return value.replace(match.group(0), n8n_expr)

        return value

    def _build_connections(
        self,
        plan: Plan,
        node_id_map: dict[str, str],
        trigger_name: str,
    ) -> dict[str, dict[str, list[list[dict[str, Any]]]]]:
        """Build N8N connections from plan edges."""
        connections: dict[str, dict[str, list[list[dict[str, Any]]]]] = {}

        # Find first node (no incoming edges)
        incoming = {edge.to_node for edge in plan.edges}
        first_nodes = [node.id for node in plan.nodes if node.id not in incoming]

        # Connect trigger to first nodes
        if first_nodes:
            connections[trigger_name] = {
                "main": [
                    [
                        {"node": node_id_map[node_id], "type": "main", "index": 0}
                        for node_id in first_nodes
                    ]
                ]
            }

        # Build connections from edges
        for edge in plan.edges:
            source_name = node_id_map.get(edge.from_node)
            target_name = node_id_map.get(edge.to_node)

            if source_name and target_name:
                if source_name not in connections:
                    connections[source_name] = {"main": [[]]}

                connections[source_name]["main"][0].append(
                    {"node": target_name, "type": "main", "index": 0}
                )

        return connections

    def _sanitize_name(self, name: str) -> str:
        """Sanitize node name for N8N."""
        # Replace underscores with spaces and title case
        return name.replace("_", " ").title()

    def to_json(self, plan: Plan, indent: int = 2) -> str:
        """Compile plan and return as JSON string."""
        workflow = self.compile(plan)
        return json.dumps(workflow, indent=indent)
