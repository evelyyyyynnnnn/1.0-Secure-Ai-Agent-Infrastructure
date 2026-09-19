"""Load and validate the authored skill-screening benchmark corpus.

The corpus is a JSONL file (one skill record per line) plus a JSON Schema-ish
document at `data/schema.json`. Validation here is dependency-free: it walks the
schema fields directly rather than pulling in a validator library.

CRITICAL: the corpus is AUTHORED BY HAND for this skeleton. It is not scraped
from any real skill/MCP registry. `is_synthetic()` is hard-wired to True.
"""

from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CORPUS_PATH = ROOT / "data" / "corpus.jsonl"
SCHEMA_PATH = ROOT / "data" / "schema.json"


def is_synthetic() -> bool:
    """Always True. The corpus is authored, never real registry data."""
    return True


def load(path=None) -> list:
    path = pathlib.Path(path) if path else CORPUS_PATH
    records = []
    with path.open(encoding="utf8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{lineno}: bad JSON: {exc}") from exc
    return records


def load_schema(path=None) -> dict:
    path = pathlib.Path(path) if path else SCHEMA_PATH
    return json.loads(path.read_text(encoding="utf8"))


class ValidationError(ValueError):
    pass


def validate_record(rec: dict, schema: dict) -> None:
    """Validate one record against schema['fields']. Raises ValidationError."""
    fields = schema["fields"]
    sid = rec.get("skill_id", "<no id>")

    for name, spec in fields.items():
        required = spec.get("required", False)
        present = name in rec
        if required and not present:
            raise ValidationError(f"{sid}: missing required field '{name}'")
        if not present:
            continue
        if rec[name] is None and not required:
            continue  # optional field explicitly null (e.g. prior_version)
        _check_type(sid, name, rec[name], spec)

    extra = set(rec) - set(fields)
    if extra:
        raise ValidationError(f"{sid}: unexpected field(s): {sorted(extra)}")

    # cross-field: adversarial records must be malicious and carry techniques
    if rec.get("adversarial_techniques"):
        if not rec["label"]["malicious"]:
            raise ValidationError(
                f"{sid}: has adversarial_techniques but label.malicious is false")
    # every label class must be in the taxonomy
    for c in rec["label"].get("classes", []):
        if c not in schema["classes"]:
            raise ValidationError(f"{sid}: label class '{c}' not in taxonomy")


_PY = {"string": str, "bool": bool, "int": int, "object": dict, "array": list}


def _check_type(sid, name, value, spec):
    t = spec.get("type")
    if t in _PY and not isinstance(value, _PY[t]):
        # bool is a subclass of int; guard it
        if not (t == "int" and isinstance(value, bool)):
            raise ValidationError(
                f"{sid}: field '{name}' should be {t}, got {type(value).__name__}")
    if t == "object" and value is not None:
        for sub, subspec in spec.get("fields", {}).items():
            if subspec.get("required", False) and sub not in value:
                raise ValidationError(
                    f"{sid}: '{name}.{sub}' is required")


def validate_all(records=None, schema=None) -> int:
    records = records if records is not None else load()
    schema = schema if schema is not None else load_schema()
    seen = set()
    for rec in records:
        validate_record(rec, schema)
        key = (rec["skill_id"], rec.get("version"))
        if key in seen:
            raise ValidationError(f"duplicate (skill_id, version): {key}")
        seen.add(key)
    return len(records)


def stats(records=None) -> dict:
    records = records if records is not None else load()
    benign = [r for r in records if not r["label"]["malicious"]]
    malicious = [r for r in records if r["label"]["malicious"]]
    adversarial = [r for r in malicious if r.get("adversarial_techniques")]
    by_class = {}
    for r in malicious:
        for c in r["label"]["classes"]:
            by_class[c] = by_class.get(c, 0) + 1
    by_split = {}
    for r in records:
        by_split[r.get("split", "?")] = by_split.get(r.get("split", "?"), 0) + 1
    return {
        "total": len(records),
        "benign": len(benign),
        "malicious": len(malicious),
        "adversarial": len(adversarial),
        "by_class": by_class,
        "by_split": by_split,
        "is_synthetic": is_synthetic(),
    }
