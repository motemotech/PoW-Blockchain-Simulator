#pragma once

#include "types.h"
#include <vector>

// 最大ノード数
#define MAX_N 1000

constexpr ll END_ROUND = 100000;

// ブロックの生成間隔
constexpr ll TARGET_GENERATION_TIME = 600000;

// ブロックの難易度調整間隔
constexpr ll DIFFICULTY_ADJUSTMENT_INTERVAL = 2016;

// ブロックの難易度調整間隔のブロック数
constexpr ll TARGET_TIMESPAN = DIFFICULTY_ADJUSTMENT_INTERVAL * TARGET_GENERATION_TIME;

namespace Config {
    constexpr int DEFAULT_NODE_COUNT = 100;
    constexpr bool DEFAULT_DYNAMIC_DIFFICULTY = true;
    constexpr ll DEFAULT_DELAY = TARGET_GENERATION_TIME / 10;

    // const std::vector<ll> DEFAULT_DELAY_VALUES = {
    //     TARGET_GENERATION_TIME / 10,
    //     TARGET_GENERATION_TIME / 5,
    //     TARGET_GENERATION_TIME,
    //     TARGET_GENERATION_TIME * 5,
    //     TARGET_GENERATION_TIME * 10,
    // };

    const std::vector<ll> DEFAULT_DELAY_VALUES = {
        TARGET_GENERATION_TIME / 10,
        TARGET_GENERATION_TIME / 9,
        TARGET_GENERATION_TIME / 8,
        TARGET_GENERATION_TIME / 7,
        TARGET_GENERATION_TIME / 6,
        TARGET_GENERATION_TIME / 5,
        TARGET_GENERATION_TIME / 4,
        TARGET_GENERATION_TIME / 3,
        TARGET_GENERATION_TIME / 2,
        TARGET_GENERATION_TIME,
        static_cast<ll>(TARGET_GENERATION_TIME * 1.5),
        TARGET_GENERATION_TIME * 2,
        static_cast<ll>(TARGET_GENERATION_TIME * 2.5),
        TARGET_GENERATION_TIME * 3,
        static_cast<ll>(TARGET_GENERATION_TIME * 3.5),
        TARGET_GENERATION_TIME * 4,
        static_cast<ll>(TARGET_GENERATION_TIME * 4.5),
        TARGET_GENERATION_TIME * 5,
        static_cast<ll>(TARGET_GENERATION_TIME * 5.5),
        TARGET_GENERATION_TIME * 6,
        static_cast<ll>(TARGET_GENERATION_TIME * 6.5),
        TARGET_GENERATION_TIME * 7,
        static_cast<ll>(TARGET_GENERATION_TIME * 7.5),
        TARGET_GENERATION_TIME * 8,
        static_cast<ll>(TARGET_GENERATION_TIME * 8.5),
        TARGET_GENERATION_TIME * 9,
        static_cast<ll>(TARGET_GENERATION_TIME * 9.5),
        TARGET_GENERATION_TIME * 10,
    };

    extern int nodeCount;
    extern bool dynamicDifficultyEnabled;
    extern ll propagationDelay;
    extern std::vector<ll> delayValues;

    void initializeDefaults();
}
 
