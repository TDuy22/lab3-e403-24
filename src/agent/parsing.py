from __future__ import annotations

import json
from typing import Any, Dict, Literal, Optional, Tuple, Union

from pydantic import BaseModel, ValidationError, TypeAdapter


# Pydantic message schemas

class ActionMessage(BaseModel):
    type: Literal["action"]
    tool: Literal["check_stock", "get_discount", "calc_shipping"]
    args: Dict[str, Any] = {}


class FinalMessage(BaseModel):
    type: Literal["final"]
    answer: str


Message = Union[ActionMessage, FinalMessage]
_MSG_ADAPTER = TypeAdapter(Message)


# Tool-args schemas

class CheckStockArgs(BaseModel):
    item_name: str


class GetDiscountArgs(BaseModel):
    coupon_code: str


class CalcShippingArgs(BaseModel):
    weight_kg: float
    destination: str


#Robust JSON extraction

def _extract_first_json_object(text: str) -> Optional[str]:
    """
    Extract the first {...} JSON object even if the model prints extra lines.
    Works by scanning and balancing braces while respecting JSON strings.
    """
    s = text.strip()
    start = s.find("{")
    if start < 0:
        return None

    in_str = False
    esc = False
    depth = 0
    for i in range(start, len(s)):
        ch = s[i]

        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue

        if ch == '"':
            in_str = True
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]

    return None


# Parse message

def parse_message(text: str) -> Optional[Message]:
    raw = _extract_first_json_object(text) or text.strip()
    try:
        return _MSG_ADAPTER.validate_json(raw)
    except ValidationError:
        return None


# Compatibility wrappers

def parse_action(text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Returns (tool_name, raw_args_dict) or None
    """
    msg = parse_message(text)
    if isinstance(msg, ActionMessage):
        return msg.tool, msg.args
    return None


def parse_final(text: str) -> Optional[str]:
    msg = parse_message(text)
    if isinstance(msg, FinalMessage):
        return msg.answer.strip()
    return None


def parse_args_for_tool(tool_name: str, raw_args: Dict[str, Any]) -> list:
    """
    Convert args dict -> positional args list for tool["func"](*args)
    """
    if tool_name == "check_stock":
        a = CheckStockArgs.model_validate(raw_args)
        return [a.item_name]

    if tool_name == "get_discount":
        a = GetDiscountArgs.model_validate(raw_args)
        return [a.coupon_code]

    if tool_name == "calc_shipping":
        a = CalcShippingArgs.model_validate(raw_args)
        return [a.weight_kg, a.destination]

    return []