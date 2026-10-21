"""QuickAnswer: answers computable quiz questions in Python, with zero tokens.

Letter counts ("How many times does the letter r appear in strawberry?") and plain arithmetic
("What is 47 * 89?", "15% of 240", "2 to the power of 10", "square root of 144") are solved
exactly. It answers only when exactly one option matches; everything else goes to the agent.
Self-contained on purpose: the CLI ships this file alone as a platform Code component.
"""

import ast
import math
import operator
import re

from haystack import component
from haystack.dataclasses import ChatMessage

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}

NUM = r"-?\d[\d,]*(?:\.\d+)?"
WORD_OPS = {"divided by": "/", "multiplied by": "*", "times": "*", "plus": "+", "minus": "-"}
LETTER_PATTERNS = [
    r"how many times does the letter ['\"]?([a-z])['\"]? (?:appear|occur) in (?:the word |the name )?['\"]?([a-z][a-z\- ]*?)['\"]?",
    r"how many ['\"]?([a-z])['\"]?'?s are (?:there )?in (?:the word |the name )?['\"]?([a-z][a-z\- ]*?)['\"]?",
]


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        if isinstance(node.op, ast.Pow) and abs(_eval(node.right)) > 100:
            raise ValueError("exponent too large")
        return OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
        return OPS[type(node.op)](_eval(node.operand))
    raise ValueError("not plain arithmetic")


def _number(text: str) -> float:
    return float(text.replace(",", ""))


def _parse(text: str):
    """Split the quiz text into the question and its A-D options."""
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    options = {}
    while lines and (m := re.fullmatch(r"([ABCD])\)\s*(.+)", lines[-1])):
        options[m.group(1)] = m.group(2)
        lines.pop()
    return " ".join(lines), options


def _solve_value(question: str):
    """The exact answer as a number, or None when the question is not computable."""
    q = question.strip().lower().rstrip("?").strip()
    for words, op in WORD_OPS.items():
        q = re.sub(rf"(?<=\d) {words} (?=\d)", f" {op} ", q)
    for pattern in LETTER_PATTERNS:
        if m := re.fullmatch(pattern, q):
            return m.group(2).count(m.group(1))
    if m := re.fullmatch(rf"what is ({NUM}) ?% of ({NUM})", q):
        return _number(m.group(1)) * _number(m.group(2)) / 100
    if m := re.fullmatch(rf"what is ({NUM}) (?:to the power of|raised to the power of) ({NUM})", q):
        return _eval(ast.parse(f"{_number(m.group(1))}**{_number(m.group(2))}", mode="eval").body)
    if m := re.fullmatch(rf"what is the square root of ({NUM})", q):
        return math.sqrt(_number(m.group(1)))
    if m := re.fullmatch(r"what is ([\d,.\s+\-*/×÷x()^]+)", q):
        expr = m.group(1)
        expr = re.sub(r"(?<=\d),(?=\d{3}\b)", "", expr)  # thousands separators only
        expr = expr.replace("×", "*").replace("÷", "/").replace("x", "*").replace("^", "**")
        if re.search(r"\d", expr) and re.search(r"[+\-*/]", expr):
            return _eval(ast.parse(expr, mode="eval").body)
    return None


def solve(text: str) -> str | None:
    """The option letter for a computable question, or None to hand it to the agent."""
    question, options = _parse(text)
    if len(options) != 4:
        return None
    try:
        value = _solve_value(question)
    except (ValueError, SyntaxError, ZeroDivisionError, OverflowError, TypeError):
        return None
    if value is None:
        return None
    matches = []
    for letter, option in options.items():
        m = re.fullmatch(rf"({NUM})\s*%?", option.strip())
        if m and math.isclose(_number(m.group(1)), value, rel_tol=1e-9, abs_tol=1e-9):
            matches.append(letter)
    return matches[0] if len(matches) == 1 else None


@component
class QuickAnswer:
    """Answers computable questions itself; routes all other questions on to the agent."""

    @component.output_types(answered=list[ChatMessage], unanswered=list[ChatMessage])
    def run(self, messages: list[ChatMessage]):
        user_texts = [m.text for m in messages if m.is_from("user") and m.text]
        letter = solve(user_texts[-1]) if user_texts else None
        if letter is None:
            return {"unanswered": messages}
        return {"answered": [*messages, ChatMessage.from_assistant(letter)]}
