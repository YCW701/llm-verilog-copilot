// Known-bad candidate: syntax error (missing semicolon), must fail compilation.
module adder4 (
    input  wire [3:0] a,
    input  wire [3:0] b,
    output wire [4:0] sum
);
  assign sum = a + b
endmodule
