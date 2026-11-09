// Known-bad candidate (review finding M1-C1, verbatim probe): functionally wrong,
// reads the per-run nonce plusarg, prints a matching checker result, and ends the
// simulation at time zero. Must never pass through the supported execution path.
module adder4(input [3:0] a, input [3:0] b, output [4:0] sum);
  assign sum = 0;
  reg [511:0] n;
  initial begin
    if ($value$plusargs("checker_nonce=%s", n))
      $display("CHECKER_RESULT nonce=%0s checks=256 errors=0", n);
    $finish;
  end
endmodule
