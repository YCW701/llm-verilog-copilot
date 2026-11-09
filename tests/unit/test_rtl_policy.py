"""RTL admission screen (review finding M1-C1). Pure function; no tools needed."""

from __future__ import annotations

import pytest

from conftest import ADDER4_CANDIDATES
from verilog_copilot.rtl import screen_candidate_rtl


def screen(text: str) -> list[str]:
    return screen_candidate_rtl(text.encode())


@pytest.mark.parametrize("name", ["correct", "wrong_behavior", "syntax_error", "hang_silent"])
def test_admitted_fixtures(name):
    assert screen_candidate_rtl((ADDER4_CANDIDATES / f"{name}.v").read_bytes()) == []


@pytest.mark.parametrize("name,needle", [
    ("nonce_forgery", "$value$plusargs"),
    ("hierarchical_tamper", "hierarchical reference"),
    ("fake_pass", "$display"),
    ("early_finish", "$finish"),
    ("hang", "$display"),
])
def test_rejected_fixtures(name, needle):
    violations = screen_candidate_rtl((ADDER4_CANDIDATES / f"{name}.v").read_bytes())
    assert violations and any(needle in v for v in violations)


@pytest.mark.parametrize("src", [
    "module m(input a, output y); assign y = a; endmodule",
    "adder4 u0 (.a(x), .b(y), .sum(s));",                      # named port connections
    "assign y = $signed(a) >>> 1; localparam W = $clog2(16);",  # allowed system functions
    "assign y = $unsigned(b);",
    "`timescale 1ns/1ps\nmodule m; endmodule",
    "// $display(\"x\"); tb.errors = 0;\nmodule m; endmodule",  # comment contents ignored
    "/* $finish; force x = 1; `include \"a\" */ module m; endmodule",
    'localparam [8*8-1:0] S = "a.b $x \\" `y";',               # string contents ignored
    "real r = 1.5e3;",
    "assign y = a ? 4'hF : 4'd0;",
])
def test_legitimate_rtl_is_admitted(src):
    assert screen(src) == []


@pytest.mark.parametrize("src,needle", [
    ("initial $display(\"PASS\");", "$display"),
    ("initial $finish;", "$finish"),
    ("initial $stop;", "$stop"),
    ("integer f = $fopen(\"x\");", "$fopen"),
    ("assign y = $root.tb.errors;", "$root"),
    ("assign y = $time;", "$time"),
    ("always @(tb_adder4.checks) tb_adder4.errors = 0;", "hierarchical reference"),
    ("assign y = top . sub . sig;", "hierarchical reference"),
    ("assign y = gen_blk[0].r;", "hierarchical reference"),
    ("initial force tb.errors = 0;", "'force'"),
    ("initial release y;", "'release'"),
    ("defparam u0.W = 8;", "'defparam'"),
    ("`include \"tb_adder4.v\"", "`include"),
    ("`define X 1", "`define"),
    ("`ifdef X\n`endif", "`ifdef"),
    ("wire \\tb.errors ; ", "escaped identifiers"),
    # Deliberate M1-R2 tightening: '$' inside an identifier is legal Verilog (R2
    # admitted it), but a '$' after an identifier/number character is now always
    # rejected so "#0$display" cannot hide behind the identifier exemption.
    ("wire a$b; assign y = a$b;", "'$' is not supported inside identifiers"),
    ("/* unterminated", "unterminated block comment"),
    ('localparam S = "unterminated\ninitial $finish;', "$finish"),  # newline ends a string
    ('localparam S = "x"; initial $finish;', "$finish"),
])
def test_interfering_constructs_are_rejected(src, needle):
    violations = screen(src)
    assert any(needle in v for v in violations), violations


def test_violation_reports_line_number():
    assert screen("module m;\n\n  initial $finish;\nendmodule")[0].startswith("line 3:")


def test_non_utf8_and_nul_rejected():
    assert screen_candidate_rtl(b"module m; \xff endmodule")
    assert screen_candidate_rtl(b"module m; \x00 endmodule")


@pytest.mark.parametrize("unit", [
    b"$a ",       # token violations
    b'"\n',      # unterminated strings (lexical problems; found before the R2 handoff)
    b'"\\\n',   # string line continuations
    b'"\r',      # unterminated strings, CR line ends
    b"/*",        # one unterminated block comment plus nothing else
], ids=["system_ids", "unterminated_strings", "continuations", "cr_strings", "block_comment"])
def test_violation_output_is_bounded_and_fast(unit):
    import time

    from verilog_copilot.rtl import MAX_REPORTED_VIOLATIONS

    pathological = unit * (350 * 1024 // len(unit))  # ~1 MiB
    t0 = time.monotonic()
    violations = screen_candidate_rtl(pathological)
    assert time.monotonic() - t0 < 2.0
    assert 1 <= len(violations) <= MAX_REPORTED_VIOLATIONS + 1
    if unit != b"/*":
        assert len(violations) == MAX_REPORTED_VIOLATIONS + 1
        assert violations[-1].startswith("further violations not listed")


# --- M1-R2 C1 regressions: lexer alignment with Icarus 13.0 --------------------------
# All payloads are bytes so no line-ending normalization can occur.

FORGERY = (b"reg [511:0] n; initial begin "
           b'if ($value$plusargs("checker_nonce=%s",n)) '
           b'$display("CHECKER_RESULT nonce=%0s checks=256 errors=0",n); $finish; end')

R2_LONE_CR_PAYLOAD = (  # verbatim from docs/reviews/M1_REVIEW_R2.md section 4
    b"module adder4(input [3:0] a,b,output [4:0] sum);\n"
    b"assign sum=0; // ignored?\r"
    b"reg [511:0] n; initial begin "
    b'if ($value$plusargs("checker_nonce=%s",n)) '
    b'$display("CHECKER_RESULT nonce=%0s checks=256 errors=0",n); '
    b"$finish; end\nendmodule\n"
)

LINE_ENDINGS = {"lf": b"\n", "crlf": b"\r\n", "cr": b"\r"}
# Separators that do NOT end a // comment in Icarus 13.0 (verified, see handoff).
NON_TERMINATORS = [bytes([c]) for c in range(1, 32) if c not in (10, 13)] + [
    b"\x7f", "\u0085".encode(), " ".encode(), " ".encode()]
ALL_SEPARATORS = NON_TERMINATORS + [b"\n", b"\r", b"\r\n"]


def _convert(data: bytes, ending: bytes) -> bytes:
    out = data.replace(b"\r\n", b"\n").replace(b"\n", ending)
    assert ending == b"\n" or ending in out
    return out


def test_r2_lone_cr_payload_is_rejected():
    assert b"// ignored?\r" in R2_LONE_CR_PAYLOAD
    violations = screen_candidate_rtl(R2_LONE_CR_PAYLOAD)
    assert any("$display" in v for v in violations) and any("$finish" in v for v in violations)


@pytest.mark.parametrize("ending", list(LINE_ENDINGS.values()), ids=list(LINE_ENDINGS))
def test_lf_crlf_cr_forms_classify_identically(ending):
    """Same violations and line numbers whatever the line-ending convention."""
    base = R2_LONE_CR_PAYLOAD.replace(b"\r", b"\n")
    assert screen_candidate_rtl(_convert(base, ending)) == screen_candidate_rtl(base)
    for name in ("correct", "wrong_behavior", "hang_silent"):
        assert screen_candidate_rtl(_convert((ADDER4_CANDIDATES / f"{name}.v").read_bytes(), ending)) == []
    for name in ("nonce_forgery", "hierarchical_tamper"):
        data = (ADDER4_CANDIDATES / f"{name}.v").read_bytes()
        assert screen_candidate_rtl(_convert(data, ending)) == screen_candidate_rtl(data)


@pytest.mark.parametrize("sep", [b"\n", b"\r", b"\r\n"], ids=["lf", "cr", "crlf"])
def test_line_comment_ends_at_lf_and_cr(sep):
    assert any("$finish" in v for v in screen_candidate_rtl(b"// c" + sep + b"initial $finish;"))


@pytest.mark.parametrize("sep", NON_TERMINATORS, ids=lambda s: s.hex())
def test_other_separators_do_not_end_line_comment(sep):
    # Icarus keeps these inside the comment; ending the comment early here would
    # let a later "/*" hide real code from the screen.
    assert screen_candidate_rtl(b"module m; // c" + sep + b"$finish;\nendmodule\n") == []


@pytest.mark.parametrize("sep", ALL_SEPARATORS, ids=lambda s: s.hex())
def test_comment_then_block_comment_matches_icarus(sep):
    """After a real line end the "/*" opens a block comment in Icarus too, so the
    forgery is inert and admitted; after any other separator the "/*" is still
    comment text and the forgery is live code that must be flagged."""
    src = b"module m; // x" + sep + b"/*\n" + FORGERY + b"\n// */\nendmodule\n"
    flagged = any("$display" in v for v in screen_candidate_rtl(src))
    assert flagged is (sep not in (b"\n", b"\r", b"\r\n")), sep


@pytest.mark.parametrize("sep", ALL_SEPARATORS, ids=lambda s: s.hex())
def test_string_separator_variants_cannot_hide_code(sep):
    for src in (
        b'module m; localparam [15:0] S = "a' + sep + b'"; ' + FORGERY + b'; localparam [7:0] T = "";\nendmodule\n',
        b'module m; localparam [15:0] S = "a\\' + sep + b'"; ' + FORGERY + b'; localparam [7:0] T = "";\nendmodule\n',
    ):
        assert screen_candidate_rtl(src), src


@pytest.mark.parametrize("sep", [b"\n", b"\r", b"\r\n"], ids=["lf", "cr", "crlf"])
def test_string_line_continuation_is_rejected(sep):
    # Icarus continues a string across backslash-LF/CR/CRLF; the screen rejects
    # rather than emulates it. The CRLF form previously desynchronized quote
    # parity and hid the code that follows.
    src = b'localparam [7:0] S = "a\\' + sep + b'b"; initial $finish; localparam T = "";\n'
    assert any("line continuation inside a string literal" in v for v in screen_candidate_rtl(src))


def test_raw_line_end_inside_string_is_rejected():
    for sep in (b"\n", b"\r"):
        assert any("not closed on its line" in v for v in screen_candidate_rtl(b'localparam S = "a' + sep + b'";'))
    assert any("before end of file" in v for v in screen_candidate_rtl(b'localparam S = "abc'))


@pytest.mark.parametrize("src,needle", [
    (b'initial #0$display("CHECKER_RESULT");', "$display"),
    (b"initial #1$finish;", "$finish"),
    (b"initial #1.5$finish;", "$finish"),
    (b"initial #1e0$finish;", "$finish"),
    (b"initial #4'hA$finish;", "$finish"),
    (b"initial #0tb_adder4.errors = 0;", "hierarchical reference"),
    (b"initial #4'd1tb_adder4.errors = 0;", "hierarchical reference"),
    (b"initial #1force sum = 0;", "'force'"),
    (b"initial #1release sum;", "'release'"),
    (b"initial #4'b1release sum;", "'release'"),
    (b"wire [3:0] x = 4'hF$display;", "$display"),
    (b"assign y = $signed$display(a);", "$display"),
])
def test_number_prefix_does_not_hide_constructs(src, needle):
    """M1-R2: a digit before '$', a keyword, or a dotted name lexes as a separate
    number token in Icarus, so the screen must not treat it as part of an identifier."""
    violations = screen_candidate_rtl(src)
    assert any(needle in v for v in violations), violations


def test_identifier_ending_in_keyword_is_conservatively_rejected():
    # Documented restriction: no identifier-boundary exemption before keywords.
    assert any("'force'" in v for v in screen_candidate_rtl(b"wire enforce; assign y = enforce;"))
    assert screen_candidate_rtl(b"wire forced, release_n; assign y = forced & release_n;") == []


def test_real_numbers_and_ranges_are_not_hierarchical():
    assert screen_candidate_rtl(b"real r = 1.5; real q = 2.0e-3; wire [3:0] w = x[3:0];") == []
