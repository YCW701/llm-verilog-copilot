// Known-bad candidate: compiles, but drops the carry-out (sum[4] is always 0).
module adder4 (
    input  wire [3:0] a,
    input  wire [3:0] b,
    output wire [4:0] sum
);
  assign sum = {1'b0, a + b};
endmodule
