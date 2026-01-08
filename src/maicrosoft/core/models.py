"""Core Pydantic models for Maicrosoft primitives and plans."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class PrimitiveType(str, Enum):
    """Type of primitive."""

    PARTICLE = "particle"
    ATOM = "atom"
    MOLECULE = "molecule"
    ORGANISM = "organism"


class PrimitiveStatus(str, Enum):
    """Lifecycle status of a primitive."""

    DRAFT = "draft"
    STABLE = "stable"
    DEPRECATED = "deprecated"


class Category(str, Enum):
    """Primitive category."""

    DATA = "data"
    TRANSFORM = "transform"
    CONTROL = "control"
    STORAGE = "storage"
    MESSAGING = "messaging"
    AI = "ai"
    OBSERVABILITY = "observability"
    NOTIFY = "notify"


class FieldType(str, Enum):
    """Supported field types."""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    ANY = "any"
    ENUM = "enum"


class InputField(BaseModel):
    """Definition of a primitive input field."""

    name: str
    type: FieldType
    enum_values: list[str] | None = None
    required: bool = False
    default: Any = None
    description: str | None = None
    validation: dict[str, Any] | None = None


class OutputField(BaseModel):
    """Definition of a primitive output field."""

    name: str
    type: FieldType
    description: str | None = None


class ErrorDef(BaseModel):
    """Definition of a possible error."""

    code: str
    description: str | None = None
    retryable: bool = False


class Interface(BaseModel):
    """Primitive interface definition."""

    inputs: list[InputField] = Field(default_factory=list)
    outputs: list[OutputField] = Field(default_factory=list)
    errors: list[ErrorDef] = Field(default_factory=list)


class CompilationTarget(BaseModel):
    """Compilation target configuration."""

    node_type: str | None = None
    operation: str | None = None
    version: str | None = None
    module: str | None = None
    function: str | None = None
    activity: str | None = None


class Constraints(BaseModel):
    """Execution constraints."""

    timeout: str = "30s"
    retry_count: int = Field(default=0, ge=0, le=10)
    idempotent: bool = False


class PrimitiveMetadata(BaseModel):
    """Metadata for a primitive."""

    id: str
    name: str
    type: PrimitiveType
    version: str
    status: PrimitiveStatus
    description: str
    category: Category | None = None
    tags: list[str] = Field(default_factory=list)
    generated_from: list[str] | None = None
    depends_on: list[str] | None = None

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate primitive ID format."""
        import re

        if not re.match(r"^(P|A|M|O)[0-9]{3}$", v):
            raise ValueError(f"Invalid primitive ID: {v}")
        return v


class CompositionStep(BaseModel):
    """A step in atom composition from particles."""

    particle: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)


class Example(BaseModel):
    """Usage example for a primitive."""

    name: str
    inputs: dict[str, Any]
    expected_outputs: dict[str, Any] | None = None


class Primitive(BaseModel):
    """Base primitive definition (particle, atom, molecule, organism)."""

    metadata: PrimitiveMetadata
    interface: Interface
    compilation_targets: dict[str, CompilationTarget] = Field(default_factory=dict)
    constraints: Constraints = Field(default_factory=Constraints)
    composition: list[CompositionStep] | None = None
    examples: list[Example] = Field(default_factory=list)


class Particle(Primitive):
    """A particle - the smallest building block."""

    pass


class Atom(Primitive):
    """An atom - composed from particles."""

    pass


class Molecule(Primitive):
    """A molecule - composed from atoms."""

    pass


class TriggerType(str, Enum):
    """Plan trigger types."""

    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    EVENT = "event"


class Trigger(BaseModel):
    """Plan trigger definition."""

    type: TriggerType
    config: dict[str, Any] = Field(default_factory=dict)


class CodeBlock(BaseModel):
    """Hybrid mode code fallback block."""

    language: str = Field(pattern="^(python|javascript)$")
    code: str = Field(max_length=500)
    description: str
    inputs_schema: dict[str, str] = Field(default_factory=dict)
    outputs_schema: dict[str, str] = Field(default_factory=dict)


class PlanNode(BaseModel):
    """A node in a plan workflow."""

    id: str
    primitive_id: str | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)
    fallback: CodeBlock | None = None

    @field_validator("primitive_id")
    @classmethod
    def validate_primitive_id(cls, v: str | None) -> str | None:
        """Validate primitive ID format if provided."""
        import re

        if v is not None and not re.match(r"^(P|A|M|O)[0-9]{3}$", v):
            raise ValueError(f"Invalid primitive ID: {v}")
        return v


class Edge(BaseModel):
    """Connection between plan nodes."""

    from_node: str
    to_node: str
    condition: str | None = None


class PlanSettings(BaseModel):
    """Plan execution settings."""

    allow_fallback: bool = False
    risk_level: str = Field(default="low", pattern="^(low|medium|high)$")


class PlanMetadata(BaseModel):
    """Plan metadata."""

    id: str
    name: str
    version: str = "1.0.0"
    description: str | None = None


class Plan(BaseModel):
    """A complete plan workflow definition."""

    metadata: PlanMetadata
    settings: PlanSettings = Field(default_factory=PlanSettings)
    trigger: Trigger | None = None
    nodes: list[PlanNode] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)


class ValidationViolation(BaseModel):
    """A validation error or warning."""

    level: str = Field(pattern="^(error|warning|info)$")
    code: str
    message: str
    node_id: str | None = None
    field: str | None = None


class ValidationResult(BaseModel):
    """Result of plan validation."""

    valid: bool
    violations: list[ValidationViolation] = Field(default_factory=list)
    warnings: list[ValidationViolation] = Field(default_factory=list)
