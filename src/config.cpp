#include "../include/config.h"

namespace Config {
    int nodeCount = DEFAULT_NODE_COUNT;
    bool dynamicDifficultyEnabled = DEFAULT_DYNAMIC_DIFFICULTY;
    ll propagationDelay = DEFAULT_DELAY;
    std::vector<ll> delayValues = DEFAULT_DELAY_VALUES;

    void initializeDefaults() {
        nodeCount = DEFAULT_NODE_COUNT;
        dynamicDifficultyEnabled = DEFAULT_DYNAMIC_DIFFICULTY;
        propagationDelay = DEFAULT_DELAY;
        delayValues = DEFAULT_DELAY_VALUES;
    }
    
}