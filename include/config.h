#pragma once

#include "types.h"
#include <vector>

// 最大ノード数
#define MAX_N 1000

constexpr ll END_ROUND = 100000;

// ブロックチェーンタイプ
enum class BlockchainType {
    BITCOIN = 0,
    ETHEREUM = 1
};

// ブロックの生成間隔
constexpr ll BTC_TARGET_GENERATION_TIME = 600000;
constexpr ll ETH_TARGET_GENERATION_TIME = 15000;

// ブロックの難易度調整間隔
constexpr ll BTC_DIFFICULTY_ADJUSTMENT_INTERVAL = 2016;
constexpr ll ETH_DIFFICULTY_ADJUSTMENT_INTERVAL = 1;

// ブロックの難易度調整間隔のブロック数
constexpr ll BTC_TARGET_TIMESPAN = BTC_DIFFICULTY_ADJUSTMENT_INTERVAL * BTC_TARGET_GENERATION_TIME;
constexpr ll ETH_TARGET_TIMESPAN = ETH_DIFFICULTY_ADJUSTMENT_INTERVAL * ETH_TARGET_GENERATION_TIME;

namespace Config {
    constexpr int DEFAULT_NODE_COUNT = 1000;
    constexpr bool DEFAULT_DYNAMIC_DIFFICULTY = true;
    constexpr ll DEFAULT_DELAY = BTC_TARGET_GENERATION_TIME / 10;
    constexpr int DEFAULT_TIE_RULE = 0;  // デフォルトはfirst-seen rule

    // const std::vector<ll> BTC_DEFAULT_DELAY_VALUES = {
    //     TARGET_GENERATION_TIME / 10,
    //     TARGET_GENERATION_TIME / 5,
    //     TARGET_GENERATION_TIME,
    //     TARGET_GENERATION_TIME * 5,
    //     TARGET_GENERATION_TIME * 10,
    // };

    const std::vector<ll> BTC_DEFAULT_DELAY_VALUES = {
        //BTC_TARGET_GENERATION_TIME / 10,
        //BTC_TARGET_GENERATION_TIME / 9,
        //BTC_TARGET_GENERATION_TIME / 8,
        //BTC_TARGET_GENERATION_TIME / 7,
        //BTC_TARGET_GENERATION_TIME / 6,
        //BTC_TARGET_GENERATION_TIME / 5,
        //BTC_TARGET_GENERATION_TIME / 4,
        //BTC_TARGET_GENERATION_TIME / 3,
        //BTC_TARGET_GENERATION_TIME / 2,
        //BTC_TARGET_GENERATION_TIME,
        //static_cast<ll>(BTC_TARGET_GENERATION_TIME * 1.5),
        //BTC_TARGET_GENERATION_TIME * 2,
        //static_cast<ll>(BTC_TARGET_GENERATION_TIME * 2.5),
        //BTC_TARGET_GENERATION_TIME * 3,
        //static_cast<ll>(BTC_TARGET_GENERATION_TIME * 3.5),
        //BTC_TARGET_GENERATION_TIME * 4,
        //static_cast<ll>(BTC_TARGET_GENERATION_TIME * 4.5),
        //BTC_TARGET_GENERATION_TIME * 5,
        //static_cast<ll>(BTC_TARGET_GENERATION_TIME * 5.5),
        //BTC_TARGET_GENERATION_TIME * 6,
        //static_cast<ll>(BTC_TARGET_GENERATION_TIME * 6.5),
        //BTC_TARGET_GENERATION_TIME * 7,
        //static_cast<ll>(BTC_TARGET_GENERATION_TIME * 7.5),
        //BTC_TARGET_GENERATION_TIME * 8,
        //static_cast<ll>(BTC_TARGET_GENERATION_TIME * 8.5),
        BTC_TARGET_GENERATION_TIME * 9,
        static_cast<ll>(BTC_TARGET_GENERATION_TIME * 9.5),
        BTC_TARGET_GENERATION_TIME * 10,
    };

    const std::vector<ll> ETH_DEFAULT_DELAY_VALUES = {
        ETH_TARGET_GENERATION_TIME / 10,
        ETH_TARGET_GENERATION_TIME / 9,
        ETH_TARGET_GENERATION_TIME / 8,
        ETH_TARGET_GENERATION_TIME / 7,
        ETH_TARGET_GENERATION_TIME / 6,
        ETH_TARGET_GENERATION_TIME / 5,
        ETH_TARGET_GENERATION_TIME / 4,
        ETH_TARGET_GENERATION_TIME / 3,
            ETH_TARGET_GENERATION_TIME / 2,
        ETH_TARGET_GENERATION_TIME,
        static_cast<ll>(ETH_TARGET_GENERATION_TIME * 1.5),
        ETH_TARGET_GENERATION_TIME * 2,
        static_cast<ll>(ETH_TARGET_GENERATION_TIME * 2.5),
        ETH_TARGET_GENERATION_TIME * 3,
        static_cast<ll>(ETH_TARGET_GENERATION_TIME * 3.5),
        ETH_TARGET_GENERATION_TIME * 4,
        static_cast<ll>(ETH_TARGET_GENERATION_TIME * 4.5),
        ETH_TARGET_GENERATION_TIME * 5,
        static_cast<ll>(ETH_TARGET_GENERATION_TIME * 5.5),
        ETH_TARGET_GENERATION_TIME * 6,
        static_cast<ll>(ETH_TARGET_GENERATION_TIME * 6.5),
        ETH_TARGET_GENERATION_TIME * 7,
        static_cast<ll>(ETH_TARGET_GENERATION_TIME * 7.5),
        ETH_TARGET_GENERATION_TIME * 8,
        static_cast<ll>(ETH_TARGET_GENERATION_TIME * 8.5),
        ETH_TARGET_GENERATION_TIME * 9,
        static_cast<ll>(ETH_TARGET_GENERATION_TIME * 9.5),
        ETH_TARGET_GENERATION_TIME * 10,
    };

    extern BlockchainType currentBlockchainType;
    extern int nodeCount;
    extern bool dynamicDifficultyEnabled;
    extern ll propagationDelay;
    extern std::vector<ll> delayValues;
    extern ll difficultyAdjustmentInterval;
    extern ll targetGenerationTime;
    extern int tieRule;  // tieルールの設定値

    void initializeBTCDefaults();
    void initializeETHDefaults();
    void setBlockchainType(BlockchainType type);
    const char* getBlockchainTypeName();
    void printCurrentConfig();  // 現在の設定を表示
}
 
