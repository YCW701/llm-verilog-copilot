// Known-good candidate: 4-bit unsigned adder with carry-out.
module adder4 (
    input  wire [3:0] a,
    input  wire [3:0] b,
    output wire [4:0] sum
);
  assign sum = a + b;
endmodule
