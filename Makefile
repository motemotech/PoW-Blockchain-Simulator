build: src/washiblock.cpp src/config.cpp
	g++ -std=c++11 -I include src/washiblock.cpp src/config.cpp -o ./output/washiblock

run:
	./output/washiblock
