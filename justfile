# C++ Commands
build:
    g++ -std=c++11 -I include src/washiblock.cpp src/config.cpp -o ./output/washiblock

run: build
    ./output/washiblock

# Python Environment
venv:
    @echo "To activate virtual environment, run:"
    @echo "source .venv/bin/activate"

# Analysis
get-plot:
    #!/bin/bash
    source .venv/bin/activate && python analysis/fit_final_share_curve.py
