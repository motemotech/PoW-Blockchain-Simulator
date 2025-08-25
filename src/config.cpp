#include "../include/config.h"
#include <iostream>

namespace Config {
    BlockchainType currentBlockchainType = BlockchainType::BITCOIN;
    int nodeCount = DEFAULT_NODE_COUNT;
    bool dynamicDifficultyEnabled = DEFAULT_DYNAMIC_DIFFICULTY;
    ll propagationDelay = DEFAULT_DELAY;
    std::vector<ll> delayValues = BTC_DEFAULT_DELAY_VALUES;
    ll difficultyAdjustmentInterval = BTC_DIFFICULTY_ADJUSTMENT_INTERVAL;
    ll targetGenerationTime = BTC_TARGET_GENERATION_TIME;
    int tieRule = DEFAULT_TIE_RULE;  // tieルールの設定値

    void initializeBTCDefaults() {
        currentBlockchainType = BlockchainType::BITCOIN;
        nodeCount = DEFAULT_NODE_COUNT;
        dynamicDifficultyEnabled = DEFAULT_DYNAMIC_DIFFICULTY;
        propagationDelay = DEFAULT_DELAY;
        delayValues = BTC_DEFAULT_DELAY_VALUES;
        difficultyAdjustmentInterval = BTC_DIFFICULTY_ADJUSTMENT_INTERVAL;
        targetGenerationTime = BTC_TARGET_GENERATION_TIME;
        tieRule = DEFAULT_TIE_RULE;
    }

    void initializeETHDefaults() {
        currentBlockchainType = BlockchainType::ETHEREUM;
        nodeCount = DEFAULT_NODE_COUNT;
        dynamicDifficultyEnabled = true;  // Ethereumはデフォルトで動的難易度調整
        propagationDelay = DEFAULT_DELAY;   
        delayValues = ETH_DEFAULT_DELAY_VALUES;
        difficultyAdjustmentInterval = ETH_DIFFICULTY_ADJUSTMENT_INTERVAL;
        targetGenerationTime = ETH_TARGET_GENERATION_TIME;
        tieRule = DEFAULT_TIE_RULE;
    }

    void setBlockchainType(BlockchainType type) {
        if (type == BlockchainType::BITCOIN) {
            initializeBTCDefaults();
        } else if (type == BlockchainType::ETHEREUM) {
            initializeETHDefaults();
        }
    }

    const char* getBlockchainTypeName() {
        switch (currentBlockchainType) {
            case BlockchainType::BITCOIN:
                return "BTC";
            case BlockchainType::ETHEREUM:
                return "ETH";
            default:
                return "UNKNOWN";
        }
    }

    void printCurrentConfig() {
        std::cout << "=== Current Configuration ===" << std::endl;
        std::cout << "Blockchain Type: " << getBlockchainTypeName() << std::endl;
        std::cout << "Node Count: " << nodeCount << std::endl;
        std::cout << "Dynamic Difficulty: " << (dynamicDifficultyEnabled ? "Enabled" : "Disabled") << std::endl;
        std::cout << "Target Generation Time: " << targetGenerationTime << " ms" << std::endl;
        std::cout << "Difficulty Adjustment Interval: " << difficultyAdjustmentInterval << " blocks" << std::endl;
        std::cout << "Propagation Delay: " << propagationDelay << " ms" << std::endl;
        std::cout << "Number of Delay Values: " << delayValues.size() << std::endl;
        std::cout << "Tie Rule: " << tieRule << " (" << (tieRule == 0 ? "first-seen" : tieRule == 1 ? "random" : "last-generated") << ")" << std::endl;
        std::cout << "============================" << std::endl;
    }
    
}
