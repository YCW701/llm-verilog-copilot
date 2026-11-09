// Known-bad candidate: elaborates, but self-retriggers forever at time 0 while
// flooding stdout. Exercises the simulation timeout and bounded log capture.
module adder4 (
    input  wire [3:0] a,
    input  wire [3:0] b,
    output wire [4:0] sum
);
  reg spin;
  initial spin = 1'b0;
  always @(spin) begin
    spin <= ~spin;
    $display("spinning %b", spin);
  end
  assign sum = a + b;
endmodule
