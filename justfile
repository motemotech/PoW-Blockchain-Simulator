# C++ Commands
build:
    g++ -std=c++11 -O3 -I include src/blockchain-simulator.cpp src/config.cpp -o ./output/blockchain-simulator

run-btc: build
    ./output/blockchain-simulator

run-btc-dynamic: build
    ./output/blockchain-simulator

run-eth-dynamic: build
    ./output/blockchain-simulator ETH
# Python Environment
venv:
    @echo "To activate virtual environment, run:"
    @echo "source .venv/bin/activate"

# Analysis
get-plot:
    #!/bin/bash
    source .venv/bin/activate && python analysis/fit_final_share_curve.py
