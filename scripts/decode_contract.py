# Adapted from tpurtell/glmrt-5.3-1rtx-4spark dc6d9b8e; MIT.
#!/usr/bin/env python3
"""Measure native-MTP acceptance on varied semantic generation tasks."""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import json
import math
import re
import statistics
import time
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any



@dataclass(frozen=True)
class PromptCase:
    category: str
    prompt: str
    max_tokens: int
    weight: float = 1.0
    json_schema: bool = False


STRUCTURED_EDIT_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {"type": "string"},
        "operation": {"type": "string"},
        "line_start": {"type": "integer"},
        "line_end": {"type": "integer"},
        "rationale": {"type": "string"},
    },
    "required": ["path", "operation", "line_start", "line_end", "rationale"],
    "additionalProperties": False,
}


def structured_edit_response_format() -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "file_edit",
            "strict": True,
            "schema": STRUCTURED_EDIT_SCHEMA,
        },
    }


CASES = {
    "count": PromptCase(
        "low-entropy",
        "Count from 1 to 64, one number per line. Do not add any other text.",
        160,
    ),
    "repeat": PromptCase(
        "repetition",
        'Repeat the exact text "red green blue" 24 times, one repetition per line. '
        "Do not number the lines.",
        160,
    ),
    "code": PromptCase(
        "code",
        "Write a Python function merge_intervals(intervals) that merges overlapping "
        "integer intervals. Include type hints, a short docstring, and three assert-based "
        "examples. Return only one Python code block.",
        320,
    ),
    "math": PromptCase(
        "reasoning",
        "A shop discounts a $240 jacket by 25%, then applies 8% sales tax to the "
        "discounted price. What is the final price? Show the calculation briefly.",
        128,
    ),
    "fable": PromptCase(
        "creative-prose",
        "Write a self-contained fable of exactly 150 words about two parrots who disagree "
        "about sharing credit. Output no title or preamble. Include the final one-sentence "
        "moral in the 150-word total. Before responding, silently revise the draft until the "
        "entire response is between 140 and 170 words.",
        256,
    ),
    "hello": PromptCase("short-response", "hi", 32),
    "topic": PromptCase(
        "exposition",
        "Explain virtual memory to a junior programmer in five concise bullet points, "
        "including paging, page faults, and the role of the TLB.",
        384,
    ),
    "structured-json": PromptCase(
        "structured-output-natural",
        "Return only a JSON object describing a file edit with keys path, operation, "
        "line_start, line_end, and rationale. Use path src/cache.rs, operation replace, "
        "lines 41 through 47, and a one-sentence rationale about removing a redundant copy.",
        128,
        weight=0.5,
    ),
    "structured-json-schema": PromptCase(
        "structured-output-constrained",
        "Return only a JSON object describing a file edit with keys path, operation, "
        "line_start, line_end, and rationale. Use path src/cache.rs, operation replace, "
        "lines 41 through 47, and a one-sentence rationale about removing a redundant copy.",
        128,
        weight=0.5,
        json_schema=True,
    ),
    "multilingual": PromptCase(
        "multilingual",
        "請用繁體中文，以四個簡短條列解釋什麼是寫入時複製（copy-on-write），"
        "並包含一個行程 fork 後修改記憶體頁面的例子。",
        384,
    ),
}

WEIGHTED_CASE_IDS = tuple(
    case_id for case_id in CASES if case_id not in {"count", "repeat"}
)

# Explicit rare-width diagnostics. They are selectable with --case but are
# excluded from the default weighted corpus because their repetitive syntax is
# deliberately favorable to long speculative windows.
CASES.update(
    {
        "syntax-rust": PromptCase(
            "diagnostic-syntax",
            "Return only a Rust code block declaring enum Op with exactly 128 "
            "variants named Op000 through Op127, one variant per line.",
            512,
        ),
        "syntax-python": PromptCase(
            "diagnostic-syntax",
            "Return only Python code defining POWERS_OF_TWO as a parenthesized "
            "tuple containing 2**0 through 2**127, one expression per line.",
            512,
        ),
    }
)
REACHABILITY_CASE_IDS = ("count", "repeat", "syntax-rust", "syntax-python")
QUALITY_CONTRACT_VERSION = "glmrt-semantic-decode-contract-v3"
REQUEST_BINDING_VERSION = "glmrt-semantic-decode-request-v2"
RUN_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(8 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _python_block(content: str) -> tuple[str | None, list[str]]:
    match = re.fullmatch(
        r"\s*```(?:python|py)?\s*\n(?P<code>.*)\n```\s*",
        content,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if match is None:
        return None, ["response is not exactly one Python code block"]
    return match.group("code"), []


def _structured_json_content(content: str, *, allow_fence: bool) -> str:
    stripped = content.strip()
    if not allow_fence:
        return stripped
    match = re.fullmatch(
        r"```(?:json)?\s*\n(?P<json>.*)\n```",
        stripped,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return match.group("json").strip() if match is not None else stripped


def validate_case_content(case_id: str, content: str) -> dict[str, Any]:
    """Check prompt-visible contracts without executing generated content."""

    issues: list[str] = []
    stripped = content.strip()
    if not stripped:
        issues.append("response is empty")
    elif case_id == "count":
        lines = [line.strip() for line in stripped.splitlines() if line.strip()]
        if lines != [str(value) for value in range(1, 65)]:
            issues.append("response is not exactly the integers 1 through 64")
    elif case_id == "repeat":
        lines = [line.strip() for line in stripped.splitlines() if line.strip()]
        if lines != ["red green blue"] * 24:
            issues.append("response is not exactly 24 requested repetition lines")
    elif case_id == "code":
        code, block_issues = _python_block(content)
        issues.extend(block_issues)
        if code is not None:
            try:
                tree = ast.parse(code)
            except SyntaxError:
                issues.append("Python code does not parse")
            else:
                functions = [
                    node
                    for node in tree.body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == "merge_intervals"
                ]
                if len(functions) != 1:
                    issues.append("merge_intervals function is missing or duplicated")
                else:
                    function = functions[0]
                    if (
                        not function.args.args
                        or function.args.args[0].annotation is None
                        or function.returns is None
                    ):
                        issues.append("merge_intervals lacks requested type hints")
                    if ast.get_docstring(function) is None:
                        issues.append("merge_intervals lacks a docstring")
                if sum(isinstance(node, ast.Assert) for node in ast.walk(tree)) < 3:
                    issues.append("fewer than three assert examples were provided")
    elif case_id == "math":
        normalized = stripped.replace(",", "")
        if re.search(r"(?<![0-9])(?:\$\s*)?194\.4(?:0)?(?![0-9])", normalized) is None:
            issues.append("response does not contain the correct final price 194.40")
        if (
            "240" not in normalized
            or not any(token in normalized for token in ("25", "75", "0.75", ".75"))
            or not any(token in normalized for token in ("8", "1.08"))
        ):
            issues.append("response does not show the requested calculation inputs")
    elif case_id == "fable":
        words = re.findall(r"\b[\w'-]+\b", stripped, flags=re.UNICODE)
        if not 140 <= len(words) <= 170:
            issues.append(f"fable has {len(words)} words, outside 140..170")
        sentence_matches = list(
            re.finditer(r"(?:^|(?<=[.!?]))\s*([^.!?]+[.!?])", stripped)
        )
        final_sentence = (
            sentence_matches[-1].group(1).strip() if sentence_matches else ""
        )
        moral_words = re.findall(r"\b[\w'-]+\b", final_sentence, flags=re.UNICODE)
        moral_terms = (
            "credit",
            "share",
            "sharing",
            "together",
            "cooperat",
            "team",
            "recognition",
            "praise",
            "glory",
            "harmony",
            "humility",
            "fair",
            "both",
        )
        if not 3 <= len(moral_words) <= 32 or not any(
            term in final_sentence.casefold() for term in moral_terms
        ):
            issues.append(
                "response does not end with a concise moral about sharing credit"
            )
    elif case_id == "hello":
        if len(stripped) > 512:
            issues.append("short greeting response is unexpectedly long")
    elif case_id == "topic":
        bullets = [
            line
            for line in stripped.splitlines()
            if re.match(r"^\s*(?:[-*•]|[1-5][.)])\s+", line)
        ]
        if len(bullets) != 5:
            issues.append(f"response has {len(bullets)} bullets, expected five")
        lowered = stripped.casefold()
        for term in ("paging", "page fault", "tlb"):
            if term not in lowered:
                issues.append(f"response omits {term}")
    elif case_id in {"structured-json", "structured-json-schema"}:
        encoded = _structured_json_content(
            content,
            allow_fence=case_id == "structured-json",
        )
        try:
            value = json.loads(encoded)
        except json.JSONDecodeError:
            issues.append(
                "response is not valid bare-or-fenced JSON"
                if case_id == "structured-json"
                else "constrained response is not bare valid JSON"
            )
        else:
            expected_keys = {"path", "operation", "line_start", "line_end", "rationale"}
            if not isinstance(value, dict) or set(value) != expected_keys:
                issues.append("JSON object has the wrong key set")
            elif (
                value.get("path") != "src/cache.rs"
                or value.get("operation") != "replace"
                or value.get("line_start") != 41
                or value.get("line_end") != 47
                or not isinstance(value.get("rationale"), str)
                or not value["rationale"].strip()
            ):
                issues.append("JSON object does not preserve the requested edit")
    elif case_id == "multilingual":
        bullets = [
            line
            for line in stripped.splitlines()
            if re.match(r"^\s*(?:[-*•]|[1-4][.)、])\s*", line)
        ]
        if len(bullets) != 4:
            issues.append(f"response has {len(bullets)} bullets, expected four")
        lowered = stripped.casefold()
        if not ("寫入時複製" in stripped or "copy-on-write" in lowered):
            issues.append("response omits copy-on-write")
        if "fork" not in lowered or "頁" not in stripped:
            issues.append("response omits the requested fork/page example")
    elif case_id == "syntax-rust":
        variants = [
            int(match.group(1))
            for line in stripped.splitlines()
            if (match := re.match(r"^\s*Op([0-9]{3}),?\s*$", line))
        ]
        if variants != list(range(128)):
            issues.append("Rust enum does not contain exactly Op000 through Op127")
    elif case_id == "syntax-python":
        code, block_issues = _python_block(content)
        issues.extend(block_issues)
        if code is not None:
            try:
                tree = ast.parse(code)
            except SyntaxError:
                issues.append("Python code does not parse")
            else:
                assignments = [
                    node
                    for node in tree.body
                    if isinstance(node, ast.Assign)
                    and any(
                        isinstance(target, ast.Name) and target.id == "POWERS_OF_TWO"
                        for target in node.targets
                    )
                ]
                if len(assignments) != 1 or not isinstance(
                    assignments[0].value, ast.Tuple
                ):
                    issues.append("POWERS_OF_TWO tuple assignment is missing")
                else:
                    exponents = []
                    for element in assignments[0].value.elts:
                        if (
                            not isinstance(element, ast.BinOp)
                            or not isinstance(element.op, ast.Pow)
                            or not isinstance(element.left, ast.Constant)
                            or element.left.value != 2
                            or not isinstance(element.right, ast.Constant)
                            or not isinstance(element.right.value, int)
                        ):
                            break
                        exponents.append(element.right.value)
                    if exponents != list(range(128)):
                        issues.append("tuple is not exactly 2**0 through 2**127")
    else:
        issues.append(f"no quality validator exists for {case_id}")
    return {
        "quality_contract_version": QUALITY_CONTRACT_VERSION,
        "quality_contract_passed": not issues,
        "quality_contract_issues": issues,
    }


