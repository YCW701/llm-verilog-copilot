// TRUSTED CHECKER -- team-authored synthetic M1 fixture, not benchmark material.
// Do not edit to make a candidate pass. Its sha256 is pinned in
// src/verilog_copilot/benchmarks/local_fixtures.py and verified on every run.
//
// Exhaustively checks a 4-bit unsigned adder with carry-out:
//   module adder4(input [3:0] a, input [3:0] b, output [4:0] sum);  sum = a + b
// Emits exactly one result line:
//   CHECKER_RESULT nonce=<per-run nonce> checks=<n> errors=<n>
`timescale 1ns/1ps
module tb_adder4;
  reg  [3:0] a;
  reg  [3:0] b;
  wire [4:0] sum;
  integer i;
  integer j;
  integer checks;
  integer errors;
  reg [8*64-1:0] nonce;

  adder4 dut (.a(a), .b(b), .sum(sum));

  initial begin
    if (!$value$plusargs("checker_nonce=%s", nonce))
      nonce = "missing";
    checks = 0;
    errors = 0;
    for (i = 0; i < 16; i = i + 1) begin
      for (j = 0; j < 16; j = j + 1) begin
        a = i;
        b = j;
        #1;
        checks = checks + 1;
        if (sum !== i + j) begin
          errors = errors + 1;
          if (errors <= 8)
            $display("CHECKER_MISMATCH a=%0d b=%0d expected=%0d got=%0d", i, j, i + j, sum);
        end
      end
    end
    $display("CHECKER_RESULT nonce=%0s checks=%0d errors=%0d", nonce, checks, errors);
    $finish;
  end
endmodule
