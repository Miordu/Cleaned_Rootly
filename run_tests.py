"""Run the Rootly test suite. Same as typing `pytest` in this folder."""

import sys

import pytest

if __name__ == "__main__":
    sys.exit(pytest.main(sys.argv[1:]))
