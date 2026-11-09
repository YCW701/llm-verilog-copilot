"""Allow ``python -m verilog_copilot``."""

import sys

from verilog_copilot.cli import main

if __name__ == "__main__":
    sys.exit(main())
