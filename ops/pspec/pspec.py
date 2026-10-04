"""pspec — a prototype of our own prompt language (prompt-spec/1) and its output form.

One file declares a task semantically, then gives its prompt text as a template. The same file yields:
  - compile(spec, mode, values, section) -> prompt text      (mode: "verbatim" | "compact")
  - check(spec, answer, values) -> problems                    (the output checker, from the same `out` block)
  - tokens(text) -> estimated tokens                           (offline estimator: ceil(utf-8 bytes / 4))

File layout
  spec <name>/<n>
  goal <one line>
  in <name> : <SEMANTIC term> @<basis> once|turn      SEMANTIC_MODEL term; once = sent once per conversation
  let <name> = <int> | /<regex>/
  out <schema>                                         then indented field lines:  name[?] : <type>
  --- once | --- turn                                  template sections

Template syntax (Jinja-like, minimal; single braces are plain text so JSON needs no escaping)
  {{ a.b|filter:arg }}       value; filters: json, cap:N, rstrip:"chars", sort
  {% for x in xs %}..{% else %}..{% end %}   loop (else = empty list)
  {% if a %}..{% else %}..{% end %}
  {% v %}..{% c %}..{% end %}                 verbatim text | compact text (the token switch)
  {{ out }}                                  the compact one-line output form
  {% use <section> %}                        insert another section

Output types
  "lit"  str  str+ (non-blank)  int  {} (any object)  key(<in>)  id new  id seen
  [T] <= N      {a: T, b?: T}      T | null
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from typing import Any

TERMS = {"Observation", "Measurement", "State", "Evidence", "Model", "DecisionContext", "Opinion"}
BASES = {"observed", "runtime", "provider", "operator", "model", "label", "estimate"}


class SpecError(ValueError):
    pass


# ---- types -----------------------------------------------------------------------------------------------------

@dataclass
class T:
    kind: str                      # lit str str+ int any key id_new id_seen list obj nullable
    arg: Any = None                # lit value | key input | list item | obj fields | nullable inner
    max: str | int | None = None   # list bound (int or let name)


@dataclass
class Field:
    name: str
    type: T
    optional: bool = False


class _P:
    """Recursive-descent parser for one type expression."""

    def __init__(self, s: str):
        self.s, self.i = s, 0

    def ws(self):
        while self.i < len(self.s) and self.s[self.i] == " ":
            self.i += 1

    def eat(self, tok: str) -> bool:
        self.ws()
        if self.s.startswith(tok, self.i):
            self.i += len(tok)
            return True
        return False

    def need(self, tok: str):
        if not self.eat(tok):
            raise SpecError(f"type: expected {tok!r} at {self.i} in {self.s!r}")

    def word(self) -> str:
        self.ws()
        m = re.compile(r"[A-Za-z_][A-Za-z0-9_+]*").match(self.s, self.i)
        if not m:
            raise SpecError(f"type: expected a name at {self.i} in {self.s!r}")
        self.i = m.end()
        return m.group()

    def type(self) -> T:
        t = self.atom()
        if self.eat("|"):
            self.need("null")
            return T("nullable", t)
        return t

    def atom(self) -> T:
        self.ws()
        if self.eat('"'):
            j = self.s.index('"', self.i)
            v, self.i = self.s[self.i:j], j + 1
            return T("lit", v)
        if self.eat("["):
            item = self.type()
            self.need("]")
            bound = None
            if self.eat("<="):
                self.ws()
                m = re.compile(r"\d+|[A-Za-z_]\w*").match(self.s, self.i)
                self.i = m.end()
                bound = int(m.group()) if m.group().isdigit() else m.group()
            return T("list", item, bound)
        if self.eat("{"):
            if self.eat("}"):
                return T("any")
            fields = []
            while True:
                name = self.word()
                opt = self.eat("?")
                self.need(":")
                fields.append(Field(name, self.type(), opt))
                if self.eat("}"):
                    return T("obj", fields)
                self.need(",")
        w = self.word()
        if w in ("str", "str+", "int"):
            return T(w)
        if w == "key":
            self.need("(")
            inp = self.word()
            self.need(")")
            return T("key", inp)
        if w == "id":
            mode = self.word()
            if mode not in ("new", "seen"):
                raise SpecError("id must be `id new` or `id seen`")
            return T("id_" + mode)
        raise SpecError(f"type: unknown {w!r}")


# ---- the spec --------------------------------------------------------------------------------------------------

@dataclass
class Input:
    name: str
    term: str
    basis: str
    when: str


@dataclass
class Spec:
    name: str
    goal: str = ""
    inputs: dict[str, Input] = field(default_factory=dict)
    lets: dict[str, Any] = field(default_factory=dict)
    out_schema: str = ""
    out: list[Field] = field(default_factory=list)
    sections: dict[str, str] = field(default_factory=dict)


def load(text: str) -> Spec:
    spec: Spec | None = None
    lines = (text[:-1] if text.endswith("\n") else text).split("\n")   # a file's final newline is not prompt text
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("--- "):
            name = ln[4:].strip()
            body = []
            i += 1
            while i < len(lines) and not lines[i].startswith("--- "):
                body.append(lines[i])
                i += 1
            spec.sections[name] = "\n".join(body)
            continue
        if not ln.strip() or ln.startswith("#"):
            i += 1
            continue
        kw, _, rest = ln.partition(" ")
        if kw == "spec":
            spec = Spec(rest.strip())
        elif spec is None:
            raise SpecError("the file must start with `spec`")
        elif kw == "goal":
            spec.goal = rest.strip()
        elif kw == "in":
            m = re.fullmatch(r"(\w+)\s*:\s*(\w+)\s+@(\w+)\s+(once|turn)", rest.strip())
            if not m:
                raise SpecError(f"in: bad line {ln!r}")
            name, term, basis, when = m.groups()
            if term not in TERMS:
                raise SpecError(f"in {name}: {term!r} is not a SEMANTIC_MODEL term")
            if basis not in BASES:
                raise SpecError(f"in {name}: unknown basis {basis!r}")
            spec.inputs[name] = Input(name, term, basis, when)
        elif kw == "let":
            name, _, v = rest.partition("=")
            v = v.strip()
            spec.lets[name.strip()] = re.compile(v[1:-1]) if v.startswith("/") else int(v)
        elif kw == "out":
            spec.out_schema = rest.strip()
            i += 1
            while i < len(lines) and lines[i].startswith("  "):
                m = re.fullmatch(r"\s+(\w+)(\?)?\s*:\s*(.+)", lines[i])
                spec.out.append(Field(m.group(1), _P(m.group(3).strip()).type(), bool(m.group(2))))
                i += 1
            continue
        else:
            raise SpecError(f"unknown line {ln!r}")
        i += 1
    if spec is None:
        raise SpecError("empty spec")
    return spec


# ---- output form: compact text and checker -------------------------------------------------------------------

def _sig(t: T, lets: dict[str, Any]) -> str:
    k = t.kind
    if k == "lit":
        return json.dumps(t.arg)
    if k in ("str", "str+", "int"):
        return k
    if k == "any":
        return "{}"
    if k == "key":
        return t.arg
    if k in ("id_new", "id_seen"):
        return "id"
    if k == "nullable":
        return _sig(t.arg, lets) + "|null"
    if k == "list":
        b = t.max if isinstance(t.max, int) else lets.get(t.max, t.max)
        return "[" + _sig(t.arg, lets) + "]" + (f"≤{b}" if b is not None else "")
    if k == "obj":
        return "{" + ",".join(f'"{f.name}"{"?" if f.optional else ""}:{_sig(f.type, lets)}' for f in t.arg) + "}"
    raise SpecError(k)


def out_form(spec: Spec) -> str:
    return _sig(T("obj", spec.out), spec.lets)


def check(spec: Spec, value: Any, values: dict[str, Any]) -> list[str]:
    seen: list[str] = []
    out: list[str] = []
    _check(spec, T("obj", spec.out), value, "$", values, seen, out)
    return out


def _check(spec, t: T, v, path, values, seen, out):
    k = t.kind
    if k == "nullable":
        if v is not None:
            _check(spec, t.arg, v, path, values, seen, out)
    elif k == "lit":
        if v != t.arg:
            out.append(path)
    elif k == "str":
        if not isinstance(v, str):
            out.append(path)
    elif k == "str+":
        if not (isinstance(v, str) and v.strip()):
            out.append(path)
    elif k == "int":
        if not (isinstance(v, int) and not isinstance(v, bool)):
            out.append(path)
    elif k == "any":
        if not isinstance(v, dict):
            out.append(path)
    elif k == "key":
        if not isinstance(v, str) or v not in values.get(t.arg, {}):
            out.append(path)
    elif k == "id_new":
        rx = spec.lets.get("id")
        if not (isinstance(v, str) and (rx is None or rx.match(v))) or v in seen:
            out.append(path)
        seen.append(v)
    elif k == "id_seen":
        if v not in seen:
            out.append(path)
    elif k == "list":
        bound = t.max if isinstance(t.max, int) else spec.lets.get(t.max)
        if not isinstance(v, list) or (bound is not None and len(v) > bound):
            out.append(path)
            return
        for i, item in enumerate(v):
            _check(spec, t.arg, item, f"{path}[{i}]", values, seen, out)
    elif k == "obj":
        if not isinstance(v, dict):
            out.append(path)
            return
        names = {f.name for f in t.arg}
        if set(v) - names:
            out.append(path + ".unknown_field")
        for f in t.arg:
            if f.name not in v:
                if not f.optional:
                    out.append(f"{path}.{f.name}")
                continue
            _check(spec, f.type, v[f.name], f"{path}.{f.name}", values, seen, out)


# ---- template --------------------------------------------------------------------------------------------------

_TOK = re.compile(r"(\{\{.*?\}\}|\{%.*?%\})", re.S)


def _get(name: str, env: dict[str, Any]) -> Any:
    cur: Any = env
    for part in name.split("."):
        cur = cur.get(part, "") if isinstance(cur, dict) else getattr(cur, part, "")
    return cur


def _filter(v: Any, f: str) -> Any:
    name, _, arg = f.partition(":")
    if name == "json":
        return json.dumps(v, ensure_ascii=False)
    if name == "cap":
        return str(v)[: int(arg)]
    if name == "rstrip":
        return str(v).rstrip(json.loads(arg))
    if name == "sort":
        return sorted(v, key=lambda x: x.get("key", "") if isinstance(x, dict) else x)
    raise SpecError(f"unknown filter {name!r}")


def _parse(toks: list[str], i: int, stops: tuple[str, ...]) -> tuple[list, int, str | None]:
    nodes: list = []
    while i < len(toks):
        t = toks[i]
        if t.startswith("{%"):
            tag = t[2:-2].strip()
            word = tag.split()[0]
            if word in stops:
                return nodes, i, tag
            if word == "use":
                nodes.append(("use", tag, [], []))
            elif word in ("for", "if", "v"):
                body, i, end = _parse(toks, i + 1, ("else", "c", "end"))
                alt = []
                if end in ("else", "c"):
                    alt, i, end = _parse(toks, i + 1, ("end",))
                nodes.append((word, tag, body, alt))
            else:
                raise SpecError(f"unknown tag {tag!r}")
        else:
            nodes.append(t)
        i += 1
    if stops:
        raise SpecError(f"missing {stops}")
    return nodes, i, None


def _render(nodes: list, env: dict[str, Any], mode: str) -> str:
    out = []
    for n in nodes:
        if isinstance(n, str):
            if n.startswith("{{"):
                expr, *filters = [p.strip() for p in n[2:-2].split("|")]
                v = _get(expr, env)
                for f in filters:
                    v = _filter(v, f)
                out.append(str(v))
            else:
                out.append(n)
            continue
        word, tag, body, alt = n
        if word == "use":
            sub, _, _ = _parse(_TOK.split(env["__spec__"].sections[tag.split()[1]]), 0, ())
            out.append(_render(sub, env, mode))
        elif word == "v":
            out.append(_render(body if mode == "verbatim" else alt, env, mode))
        elif word == "if":
            out.append(_render(body if _get(tag.split()[1], env) else alt, env, mode))
        elif word == "for":
            m = re.fullmatch(r"for (\w+) in ([\w.]+)((?:\|\w+)*)", tag)
            seq = _get(m.group(2), env)
            for f in filter(None, m.group(3).split("|")):
                seq = _filter(seq, f)
            if isinstance(seq, dict):
                seq = [{"key": k, **v} for k, v in sorted(seq.items())]
            if not seq:
                out.append(_render(alt, env, mode))
            for x in seq:
                out.append(_render(body, {**env, m.group(1): x}, mode))
    return "".join(out)


def compile(spec: Spec, section: str, values: dict[str, Any], mode: str = "verbatim") -> str:
    if mode not in ("verbatim", "compact"):
        raise SpecError(mode)
    missing = [n for n, i in spec.inputs.items() if n not in values]
    if missing:
        raise SpecError(f"missing inputs: {missing}")
    nodes, _, _ = _parse(_TOK.split(spec.sections[section]), 0, ())
    env = {**spec.lets, **values, "out": out_form(spec), "out_schema": spec.out_schema, "__spec__": spec}
    return _render(nodes, env, mode)


def tokens(text: str) -> int:
    """Offline estimate: ceil(utf-8 bytes / 4). Not a provider tokenizer; use Telemetry usage for real counts."""
    return math.ceil(len(text.encode("utf-8")) / 4)
