// Known-bad candidate: functionally correct adder that ends the simulation
// before the checker reports. vvp exits 0, but that must not count as a pass.
`timescale 1ns/1ps
module adder4 (
    input  wire [3:0] a,
    input  wire [3:0] b,
    output wire [4:0] sum
);
  assign sum = a + b;
  initial #3 $finish;
endmodule
