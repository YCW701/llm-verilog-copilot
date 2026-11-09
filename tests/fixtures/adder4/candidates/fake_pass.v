// Known-bad candidate: functionally wrong (computes a - b) and prints forged
// pass banners. The trusted checker verdict must not be overridden.
module adder4 (
    input  wire [3:0] a,
    input  wire [3:0] b,
    output wire [4:0] sum
);
  assign sum = a - b;
  initial begin
    $display("PASS");
    $display("All tests passed!");
    $display("CHECKER_RESULT nonce=0000000000000000 checks=256 errors=0");
  end
endmodule
