# C++ Commands
build:
    g++ -std=c++11 -I include src/washiblock.cpp src/config.cpp -o ./output/washiblock

run-btc: build
    ./output/washiblock

run-eth: build
    ./output/washiblock ETH

# Python Environment
venv:
    @echo "To activate virtual environment, run:"
    @echo "source .venv/bin/activate"

# Analysis
get-plot:
    #!/bin/bash
    source .venv/bin/activate && python analysis/fit_final_share_curve.py
