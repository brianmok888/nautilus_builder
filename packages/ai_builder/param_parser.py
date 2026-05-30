"""# @param convention parser for AI Builder.

Parses structured comments from strategy code to extract tunable parameters
and strategy metadata. Convention:

    # @param name:type:default description
    # @strategy key="value" key2="value2"

This reduces StrategySpec boilerplate by allowing strategy authors to declare
params as structured comments that the AI Builder pipeline picks up automatically.
"""
from __future__ import annotations

import re
from pydantic import BaseModel, ConfigDict


class ParamDecl(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: str
    default: str
    description: str = ""


class ParseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    params: list[ParamDecl] = []
    strategy_header: dict[str, str] | None = None


# Regex for # @param name:type:default [description]
_PARAM_RE = re.compile(
    r"#\s*@param\s+"
    r"(?P<name>\w+):"
    r"(?P<type>\w+):"
    r"(?P<default>\S+)"
    r"(?:\s+(?P<description>.*))?$"
)

# Regex for # @strategy key="value" ...
_STRATEGY_RE = re.compile(
    r'#\s*@strategy\s+'
    r'(?P<attrs>.+)'
)

_KV_RE = re.compile(r'(\w+)="([^"]*)"')


def parse_params(code: str) -> ParseResult:
    """Parse # @param declarations from code.

    Returns a ParseResult with all found param declarations.
    """
    params: list[ParamDecl] = []
    strategy_header: dict[str, str] | None = None

    for line in code.splitlines():
        line = line.strip()

        # Check for @strategy header
        strat_match = _STRATEGY_RE.match(line)
        if strat_match:
            attrs_str = strat_match.group("attrs")
            header: dict[str, str] = {}
            for kv_match in _KV_RE.finditer(attrs_str):
                header[kv_match.group(1)] = kv_match.group(2)
            strategy_header = header
            continue

        # Check for @param
        param_match = _PARAM_RE.match(line)
        if param_match:
            params.append(ParamDecl(
                name=param_match.group("name"),
                type=param_match.group("type"),
                default=param_match.group("default"),
                description=param_match.group("description") or "",
            ))

    return ParseResult(params=params, strategy_header=strategy_header)


def parse_strategy_header(code: str) -> dict[str, str] | None:
    """Parse only the # @strategy header from code.

    Returns key-value dict or None if no header found.
    """
    for line in code.splitlines():
        line = line.strip()
        strat_match = _STRATEGY_RE.match(line)
        if strat_match:
            attrs_str = strat_match.group("attrs")
            header: dict[str, str] = {}
            for kv_match in _KV_RE.finditer(attrs_str):
                header[kv_match.group(1)] = kv_match.group(2)
            return header
    return None
