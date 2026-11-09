"""Candidate RTL admission screen (checker-interference restrictions).

The candidate is simulated in the same Icarus process as the trusted checker, so
it can, in principle, print a forged result line or write the checker's state.
Review finding M1-C1 showed a nonce-aware ``$display`` forgery; an upward
hierarchical reference (``tb_adder4.errors = 0``) forges a pass with no system
task at all. This screen rejects the constructs that give a design access to
anything outside its own ports:

* system tasks/functions other than ``$signed``, ``$unsigned`` and ``$clog2``,
  and any other use of ``$`` (so ``$`` inside identifiers is not supported);
* hierarchical (dotted) references, including generate-scope references;
* escaped identifiers (they can hide dots and comment markers);
* ``force``, ``release`` and ``defparam``;
* every compiler directive except ```timescale``.

Restricted supported subset (review M1-R2-N1). These rules define the RTL subset
the M1 harness admits. Some rejected constructs are legal, synthesizable Verilog
(for example a local generate-scope reference, ```default_nettype``, a ``$`` inside
an identifier, or an identifier such as ``enforce`` that ends in a forbidden
keyword). Rejection is a policy decision reported as
``candidate_policy_violation`` before compilation; it is not evidence of a
functional defect. The team must revisit this subset before benchmark evaluation.

Lexical alignment with Icarus (review M1-R2 C1). The screen must never treat as
comment or string text that Icarus compiles as code. Verified against Icarus
Verilog 13.0 (see docs/reviews/M1_HANDOFF_R2.md):

* a ``//`` comment ends at LF or CR (a lone CR, as well as CRLF); VT, FF, NEL and
  U+2028/U+2029 do not end it, so the screen does not treat them as line ends;
* a string literal must close on its own line. A raw CR/LF inside a string, or a
  backslash immediately followed by CR/LF (Icarus continues the string across
  LF, CR and CRLF), is rejected rather than emulated;
* ``$``, keyword and hierarchical-reference rules do not exempt a match because
  it follows a digit or identifier character: ``#0$display`` and
  ``#0tb.errors = 0`` lex as a number followed by the construct.

This is a conservative lexical screen for trusted team-authored fixtures. It is
NOT a sandbox and is not proven complete against every interference vector; it
does not restrict filesystem, network, CPU or memory use.
"""

from __future__ import annotations

import bisect
import itertools
import re
from typing import Callable, Iterator

ALLOWED_SYSTEM_FUNCTIONS = frozenset({"$signed", "$unsigned", "$clog2"})
ALLOWED_DIRECTIVES = frozenset({"timescale"})
FORBIDDEN_KEYWORDS = ("force", "release", "defparam")
MAX_REPORTED_VIOLATIONS = 20

# Characters Icarus 13.0 treats as ending a line (and a // comment).
_LINE_END_CHARS = "\r\n"
_IDENT_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_$")

_LINE_BREAK_RE = re.compile(r"\r\n|\r|\n")
_LINE_END_RE = re.compile(r"[\r\n]")
_DOLLAR_RE = re.compile(r"\$")
_SYSTEM_TOKEN_RE = re.compile(r"\$[A-Za-z0-9_]*")
_DIRECTIVE_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_$]*)?")
# A run of identifier/number characters (or ']') followed by a dot and a name.
# The run may start with a digit so "#0tb.errors" is caught; the lookbehind only
# anchors the run at its first character to keep the scan linear.
_HIER_RE = re.compile(r"(?:(?<![A-Za-z0-9_$])[A-Za-z0-9_$]+|\])\s*\.\s*[A-Za-z_$\\]")
_NAME_TAIL_RE = re.compile(r"[A-Za-z0-9_$.\[\]]*")
# No lookbehind: "#1force" lexes as a number followed by the keyword. This also
# rejects identifiers that merely end in a keyword (e.g. "enforce"); see above.
_KEYWORD_RE = re.compile(rf"({'|'.join(FORBIDDEN_KEYWORDS)})(?![A-Za-z0-9_$])")


def _line_lookup(text: str) -> Callable[[int], int]:
    """Map an offset to a 1-based line number; LF, CRLF and lone CR each end a line."""
    starts = [0] + [m.end() for m in _LINE_BREAK_RE.finditer(text)]
    return lambda pos: bisect.bisect_right(starts, pos)


def _blank_comments_and_strings(text: str, line: Callable[[int], int]) -> tuple[str, list[str]]:
    """Return ``text`` with comment and string contents replaced by spaces (CR
    and LF kept, so offsets and line numbers are preserved), plus lexical
    problems. One left-to-right pass, so comment markers inside strings and
    quotes inside comments are treated the way the Icarus lexer treats them."""
    out = list(text)
    problems: list[str] = []
    i, n = 0, len(text)

    def blank(a: int, b: int) -> None:
        for k in range(a, b):
            if out[k] not in _LINE_END_CHARS:
                out[k] = " "

    def report(problem: str) -> None:
        # Keep one more than the cap so the caller knows more exist; the list
        # (and memory) stays bounded however many problems the input contains.
        if len(problems) <= MAX_REPORTED_VIOLATIONS:
            problems.append(problem)

    while i < n:
        c = text[i]
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            m = _LINE_END_RE.search(text, i)
            end = n if m is None else m.start()
            blank(i, end)
            i = end
        elif c == "/" and i + 1 < n and text[i + 1] == "*":
            end = text.find("*/", i + 2)
            if end == -1:
                report(f"line {line(i)}: unterminated block comment")
                blank(i, n)
                i = n
            else:
                blank(i, end + 2)
                i = end + 2
        elif c == '"':
            stop, problem = _scan_string(text, i)
            if problem:
                report(f"line {line(i)}: {problem}")
            blank(i, stop)
            i = stop
        else:
            i += 1
    return "".join(out), problems


def _scan_string(text: str, i: int) -> tuple[int, str | None]:
    """Scan the string literal opening at ``text[i]``. Return the offset after
    the part to blank, and a problem when the literal is unsupported. On a
    problem, scanning resumes at the line end, which is screened as code."""
    j, n = i + 1, len(text)
    while j < n:
        ch = text[j]
        if ch == '"':
            return j + 1, None
        if ch in _LINE_END_CHARS:
            return j, "string literal is not closed on its line"
        if ch == "\\" and j + 1 < n and text[j + 1] in _LINE_END_CHARS:
            return j + 1, "line continuation inside a string literal is not supported"
        j += 2 if ch == "\\" else 1
    return n, "string literal is not closed before end of file"


def _iter_violations(code: str, line: Callable[[int], int]) -> Iterator[str]:
    """Lazily yield violations so scanning stops once the reporting cap is hit."""
    for m in _DOLLAR_RE.finditer(code):
        p = m.start()
        token = _SYSTEM_TOKEN_RE.match(code, p).group(0)
        if p > 0 and code[p - 1] in _IDENT_CHARS:
            start = p - 1
            while start > 0 and code[start - 1] in _IDENT_CHARS:
                start -= 1
            yield (f"line {line(p)}: {token!r} directly after an identifier character or number "
                   f"({code[start:p] + token!r}) is not allowed; '$' is not supported inside identifiers")
        elif token not in ALLOWED_SYSTEM_FUNCTIONS:
            yield f"line {line(p)}: system task/function {token!r} is not allowed"
    for m in _DIRECTIVE_RE.finditer(code):
        name = m.group(1)
        if name not in ALLOWED_DIRECTIVES:
            yield f"line {line(m.start())}: compiler directive `{name or ''} is not allowed"
    for m in _HIER_RE.finditer(code):
        name = re.sub(r"\s+", "", m.group(0)) + _NAME_TAIL_RE.match(code, m.end()).group(0)
        yield f"line {line(m.start())}: hierarchical reference {name!r} is not allowed"
    for m in _KEYWORD_RE.finditer(code):
        yield f"line {line(m.start())}: '{m.group(1)}' is not allowed"
    if "\\" in code:
        yield f"line {line(code.index(chr(92)))}: escaped identifiers are not allowed"


def screen_candidate_rtl(source: bytes) -> list[str]:
    """Return human-readable policy violations; an empty list means admitted.

    ``source`` must be the exact bytes that will be compiled (no line-ending
    normalization). At most ``MAX_REPORTED_VIOLATIONS`` are listed, followed by
    one marker entry if more exist, so artifacts and CLI output stay bounded."""
    try:
        text = source.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [f"candidate is not valid UTF-8 ({exc.reason} at byte {exc.start})"]
    if "\x00" in text:
        return ["candidate contains NUL bytes"]

    line = _line_lookup(text)
    code, lexical_problems = _blank_comments_and_strings(text, line)
    violations: list[str] = []
    for violation in itertools.chain(lexical_problems, _iter_violations(code, line)):
        if len(violations) >= MAX_REPORTED_VIOLATIONS:
            violations.append(f"further violations not listed (limit {MAX_REPORTED_VIOLATIONS})")
            break
        violations.append(violation)
    return violations
