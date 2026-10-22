"""Small, dependency-free MCP tool registry and JSON Schema validator."""

from dataclasses import dataclass
import math


class ToolError(ValueError):
    pass


S = {"type": "string"}
B = {"type": "boolean"}
I = {"type": "integer", "minimum": 1}  # noqa: E741
O = {"type": "object"}  # noqa: E741


def arr(items, maximum=500):
    return {"type": "array", "items": items, "minItems": 1, "maxItems": maximum}


def enum(*values):
    return {"type": "string", "enum": list(values)}


def obj(properties, required=()):
    return {"type": "object", "properties": properties, "required": list(required), "additionalProperties": False}


def validate(value, schema, path="arguments"):
    kind = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "boolean": bool, "integer": int, "number": (int, float)}
    if kind and (not isinstance(value, types[kind]) or (kind in ("integer", "number") and isinstance(value, bool))):
        raise ToolError(f"{path}: expected {kind}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(value):
            raise ToolError(f"{path}: must be finite")
        for key, check in (("minimum", lambda x: value >= x), ("maximum", lambda x: value <= x)):
            if key in schema and not check(schema[key]):
                raise ToolError(f"{path}: violates {key}={schema[key]}")
    if "enum" in schema and value not in schema["enum"]:
        raise ToolError(f"{path}: expected one of {schema['enum']}")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                raise ToolError(f"{path}.{key}: required")
        for key, item in value.items():
            if key in props:
                validate(item, props[key], f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                raise ToolError(f"{path}.{key}: unknown argument")
            elif isinstance(schema.get("additionalProperties"), dict):
                validate(item, schema["additionalProperties"], f"{path}.{key}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", 10000):
            raise ToolError(f"{path}: invalid number of items")
        for index, item in enumerate(value):
            validate(item, schema.get("items", {}), f"{path}[{index}]")
    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        raise ToolError(f"{path}: too short")


@dataclass
class Tool:
    name: str
    description: str
    schema: dict
    function: object
    write: bool = False
    destructive: bool = False
    undoable: bool = True

    def public(self):
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.schema,
            "annotations": {"readOnlyHint": not self.write, "destructiveHint": self.destructive, "openWorldHint": False},
        }


TOOLS = {}


def tool(name, description, properties=None, required=(), *, write=False, destructive=False, undoable=True):
    def register(function):
        TOOLS[name] = Tool(name, description, obj(properties or {}, required), function, write, destructive, undoable)
        return function

    return register


@dataclass
class ContentResult:
    """Explicit MCP content, for example a real image block for vision clients."""

    content: list
