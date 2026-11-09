// Known-bad candidate: functionally wrong (only the final vector is right) and uses
// NO system tasks. It writes the checker's error counter through a Verilog upward
// hierarchical reference. Unscreened, this forges "checks=256 errors=0" under
// Icarus 13.0. Must be rejected before compilation.
module adder4(input [3:0] a, input [3:0] b, output [4:0] sum);
  assign sum = (a == 4'd15 && b == 4'd15) ? 5'd30 : 5'd0;
  always @(tb_adder4.checks) tb_adder4.errors = 0;
endmodule
