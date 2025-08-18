#pragma once

typedef unsigned long long ull;
typedef long long ll;

enum class TaskType {
    BLOCK_GENERATION = 0,
    PROPAGATION = 1
};

struct block {
    ll height;
    block* prevBlock;
    int minter;
    ll time;
    ll rand;
    double difficulty;
    ll lastEpochTime;
    bool finalized = false;

    block() : 
        height(0), 
        prevBlock(nullptr), 
        minter(-1),
        time(0),
        rand(0),
        difficulty(1.0),
        lastEpochTime(0),
        finalized(false) {}
};

struct task {
    ll time;
    TaskType flag;
    int minter;
    int from;
    int to;
    block* propagatedBlock;
};