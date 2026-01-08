"""
Maicrosoft - Framework for Hallucination-Free AI Coding

A primitives-first approach that forces AI agents to compose workflows
from pre-validated building blocks instead of generating arbitrary code.
"""

__version__ = "0.1.0"
__author__ = "BORG.tools"

from maicrosoft.core.models import Plan, PlanNode, Particle, Atom
from maicrosoft.registry.loader import PrimitiveLoader
from maicrosoft.registry.registry import PrimitiveRegistry

__all__ = [
    "Plan",
    "PlanNode",
    "Particle",
    "Atom",
    "PrimitiveLoader",
    "PrimitiveRegistry",
]
