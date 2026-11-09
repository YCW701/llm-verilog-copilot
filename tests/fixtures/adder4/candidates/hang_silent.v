// Known-bad candidate: elaborates, but self-retriggers forever at time 0 without
// printing (no system tasks, so it is admitted by the RTL screen). Exercises the
// simulation timeout and process-tree cleanup through the supported path.
module adder4 (
    input  wire [3:0] a,
    input  wire [3:0] b,
    output wire [4:0] sum
);
  reg spin;
  initial spin = 1'b0;
  always @(spin) spin <= ~spin;
  assign sum = a + b;
endmodule
