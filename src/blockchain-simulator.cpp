#include <iostream>
#include <fstream>
#include <random>
#include <queue>
#include <cmath>
#include <iomanip>
#include <climits>
#include <array>
#include <string>
#include <sys/stat.h>
#include <sys/types.h>
#include <functional>
#include <chrono>
#include <sstream>
#include <map>
#include <vector>
#include "../include/config.h"
using namespace std;

int currentRoundStarter;
ll currentRound;
ll currentTime = 0;
block* currentBlock[MAX_N];
task* currentMiningTask[MAX_N];
double hashrate[MAX_N]; // ノードのハッシュレート
double totalHashrate;
ll numMain[3][MAX_N];
ll mainLength;
int highestHashrateNode = 0;  // 最高ハッシュレートのノードID

ll startedByA;
ll startedByO;
ll startedByAAndMinedByA;
ll startedByOAndMinedByO;
ll startedByAAndMinedByO;
ll startedByOAndMinedByA;

bool roundStarted[END_ROUND];
int roundStartedBy[END_ROUND];
bool highestHashrateNodeMinedBlocks[END_ROUND];

// 各マイナーのマイニングシェア追跡用配列（0番目から9番目まで）
bool nodeMinedBlocks[10][END_ROUND];  // 各マイナーが各ブロック高でマイニングしたかどうか
ll nodeMinedCount[10];  // 各マイナーがマイニングしたブロック数

// uncle block検出用のデータ構造
map<ll, vector<block*>> blocksByHeight;  // 高さ別のブロック一覧

// ブロック生成間隔記録用のデータ構造
vector<ll> blockGenerationIntervals;  // 各ブロックの生成間隔（ブロック生成イベント間の時間差）
ll lastBlockGenerationTime;  // 最後にブロックが生成された時刻

ll delay;

bool chooseMainchain(block* block1, block* block2, int from, int to, int tie);
void finalizeBlocks(block* block1, int tie);
void saveDataInCsv(string filePath, string fileName, ofstream& csvFile);
void writeDataToCsv(ofstream& csvFile, ll height, ll time, double proportion, double difficulty);
void simulation(int tie, const std::string& timestamp_dir);
void reset();
ll getPropagationTime(int i, int j);
double calculateDifficulty(block* latestBlock);  // ブロックチェーンタイプに応じた難易度計算関数
double calculateDifficultyBTC(block* latestBlock);  // Bitcoin用難易度計算
double calculateDifficultyETH(block* latestBlock);  // Ethereum用難易度計算
bool hasUncleBlock(block* currentBlock);  // uncle block検出関数
void openCsvFile(string filePath, string fileName, ofstream& csvFile);
string createTimestampDirectory();

// 各ノードのマイニングシェアCSVファイルを作成する関数
void createNodeShareCsvFiles(const std::string& timestamp_dir, int tie);
void writeNodeShareData(const std::string& timestamp_dir, int tie);

// tieパラメータに基づいてルール名を取得する関数
string getRuleName(int tie) {
    switch (tie) {
        case 0:
            return "first_seen";
        case 1:
            return "random";
        case 2:
            return "last_generated";
        default:
            return "unknown";
    }
}

// 乱数生成のためのシード値を生成する
std::random_device seed_gen;
// 乱数生成を行う
std::mt19937_64 random_value(10);// 1, 5, 10, 100
std::uniform_real_distribution<double> uni_dist(0., 1.0);
std::exponential_distribution<double> exp_dist(1);
std::normal_distribution<double> normal_dist(0.0, 1.0);

// ジェネシスブロックを作成する関数
block* createGenesisBlock() {
    block* genesisBlock = new block;
    genesisBlock->prevBlock = nullptr;
    genesisBlock->height = 0;
    genesisBlock->minter = -1;
    genesisBlock->difficulty = 1.0;  // ジェネシスブロックの初期難易度設定
    genesisBlock->lastEpochTime = 0;  // ジェネシスブロックの初期時刻
    genesisBlock->finalized = true;
    return genesisBlock;
}

int main(int argc, char* argv[]) {
    cout << "Start Blockchain Simulator" << endl;
    
    // コマンドライン引数でブロックチェーンタイプを指定
    BlockchainType blockchainType = BlockchainType::BITCOIN;  // デフォルト
    if (argc > 1) {
        std::string arg = argv[1];
        if (arg == "BTC" || arg == "bitcoin") {
            blockchainType = BlockchainType::BITCOIN;
        } else if (arg == "ETH" || arg == "ethereum") {
            blockchainType = BlockchainType::ETHEREUM;
        } else {
            cout << "Usage: " << argv[0] << " [BTC|ETH|bitcoin|ethereum]" << endl;
            cout << "Using default: Bitcoin" << endl;
        }
    }
    
    // 選択されたブロックチェーンタイプで設定を初期化
    Config::setBlockchainType(blockchainType);
    
    // 現在の設定を表示
    Config::printCurrentConfig();

    ll highestHashrateNodeMainChainCount = 0;

    // タイムスタンプベースのディレクトリを作成
    std::string timestamp_dir = createTimestampDirectory();

    // w_A, w_O, pi_A, pi_O の値を記録するCSVファイルを作成
    std::string blockchain_type = Config::getBlockchainTypeName();
    std::string difficulty_type = Config::dynamicDifficultyEnabled ? "dynamic" : "static";
    std::string rule_name = getRuleName(Config::tieRule);
    std::string w_and_pi_filename = timestamp_dir + "/" + blockchain_type + "_" + std::to_string(Config::nodeCount) + "_" + std::to_string(END_ROUND) + "_" + rule_name + "_" + difficulty_type + "_w_pi.csv";
    ofstream w_and_pi_file(w_and_pi_filename);
    
    if (!w_and_pi_file.is_open()) {
        cerr << "[error] Failed to open w_and_pi CSV file: " << w_and_pi_filename << endl;
        return 1;
    } else {
        cout << "[info] Writing w_and_pi CSV to: " << w_and_pi_filename << endl;
    }
    
    // CSVファイルのヘッダーを書き込み
    w_and_pi_file << "delay,pi_A,pi_O,w_A,w_O,avg_block_interval" << endl;

    for (ll current_delay : Config::delayValues) {
        // ===== ハッシュレート設定（コメントアウト可能） =====
        
        // 設定A: node 0のハッシュレートを10%にする設定
        hashrate[0] = 30.0;
        for (int i = 1; i < Config::nodeCount; i++) {
            hashrate[i] = 70.0 / (Config::nodeCount - 1);
        }
        
        // 設定B: node 0のハッシュレートを50%にする設定
        // hashrate[0] = 50.0;
        // for (int i = 1; i < Config::nodeCount; i++) {
        //     hashrate[i] = 50.0 / (Config::nodeCount - 1);
        // }
        
        // 設定C: node 0のハッシュレートを90%にする設定
        // hashrate[0] = 90.0;
        // for (int i = 1; i < Config::nodeCount; i++) {
        //     hashrate[i] = 10.0 / (Config::nodeCount - 1);
        // }

        // 設定D: 9つのノードが異なるハッシュレートを持つ設定（実データベース）
        // double hashrateSum = 0;
        // hashrate[0] = 27.9383;
        // hashrateSum += hashrate[0];
        // hashrate[1] = 15.3179;
        // hashrateSum += hashrate[1];
        // hashrate[2] = 12.4277;
        // hashrateSum += hashrate[2];
        // hashrate[3] = 10.9827;
        // hashrateSum += hashrate[3];
        // hashrate[4] = 8.47784;
        // hashrateSum += hashrate[4];
        // hashrate[5] = 4.62428;
        // hashrateSum += hashrate[5];
        // hashrate[6] = 4.04624;
        // hashrateSum += hashrate[6];
        // hashrate[7] = 3.85356;
        // hashrateSum += hashrate[7];
        // hashrate[8] = 2.40848;
        // hashrateSum += hashrate[8];
        // hashrate[9] = 1.92678;
        // hashrateSum += hashrate[9];
        // cout << "hashrateSum: " << hashrateSum << endl;
        // for (int i = 10; i < Config::nodeCount; i++) {
        //     hashrate[i] = (100 - hashrateSum) / (Config::nodeCount - 9);
        // }
        // cout << "hashrate[10]: " << hashrate[10] << endl;
        
        // ===== ハッシュレート設定終了 =====

       totalHashrate = 0;
       for (int i = 0; i < Config::nodeCount; i++) {
           totalHashrate += hashrate[i];
       }
       cout << "totalHashrate: " << totalHashrate << endl;
       cout << "hashrate[0]: " << hashrate[0]/totalHashrate << endl;
       delay = current_delay;
       cout << "--- Running simulation with delay: " << delay << " (" << getRuleName(Config::tieRule) << " rule) ---" << endl;
       reset();
       simulation(Config::tieRule, timestamp_dir);
       
       // シミュレーション後にw_A, w_O, pi_A, pi_Oの値を計算してCSVに書き込み
       double pi_A = (double)startedByA / (double)END_ROUND;
       double pi_O = (double)startedByO / (double)END_ROUND;
       double w_A = (startedByA > 0) ? (double)startedByAAndMinedByA / (double)startedByA : 0.0;
       double w_O = (startedByO > 0) ? (double)startedByOAndMinedByA / (double)startedByO : 0.0;
       
       // ブロック生成間隔の平均値を計算
       double avgBlockInterval = 0.0;
       if (!blockGenerationIntervals.empty()) {
           ll totalInterval = 0;
           for (ll interval : blockGenerationIntervals) {
               totalInterval += interval;
           }
           avgBlockInterval = (double)totalInterval / (double)blockGenerationIntervals.size();
       }
       
       w_and_pi_file << delay << "," << pi_A << "," << pi_O << "," << w_A << "," << w_O << "," << avgBlockInterval << endl;
       cout << "Recorded: delay=" << delay << ", pi_A=" << pi_A << ", pi_O=" << pi_O 
            << ", w_A=" << w_A << ", w_O=" << w_O << ", avg_interval=" << avgBlockInterval 
            << " ms (" << blockGenerationIntervals.size() << " blocks)" << endl;
    }

    cout << "--- All simulations finished. ---" << endl;

    w_and_pi_file.close();
    cout << "[info] w_and_pi CSV file closed successfully." << endl;

    return 0;
}

bool chooseMainchain(block* block1, block* block2, int from, int to, int tie) {
    block* originalBlock = currentBlock[to];
    
    if (block1->height > block2->height) {
        currentBlock[to] = block1;
        return (originalBlock != block1);
    }

    if (block1->height == block2->height){
        if (tie == 1 && block2->minter != to && block1->rand < block2->rand) { // for the random rule
            currentBlock[to] = block1;
            return (originalBlock != block1);
        }

        if (tie == 2 && block2->minter != to && block1->time > block2->time) {
            currentBlock[to] = block1;
            return (originalBlock != block1);
        }
    }

    return false;
}

ll getPropagationTime(int i, int j) {
    if (i == j) return 0;
    else return delay;
}

double calculateDifficulty(block* latestBlock) {
    switch (Config::currentBlockchainType) {
        case BlockchainType::BITCOIN:
            return calculateDifficultyBTC(latestBlock);
        case BlockchainType::ETHEREUM:
            return calculateDifficultyETH(latestBlock);
        default:
            return calculateDifficultyBTC(latestBlock);
    }
}

// stale block数は0で計算
double calculateDifficultyBTC(block* latestBlock) {
    if (latestBlock == nullptr || latestBlock->height == 0) {
        return 1.0;
    }
    
    if (latestBlock->height % Config::difficultyAdjustmentInterval != 0) {
        return latestBlock->difficulty;
    }
    
    if (latestBlock->height < Config::difficultyAdjustmentInterval) {
        return latestBlock->difficulty; 
    }

    ll actualTimespan = latestBlock->time - latestBlock->lastEpochTime;
    double ratio = (double)BTC_TARGET_TIMESPAN / (double)actualTimespan;
    if (ratio > 4.0) ratio = 4.0;
    if (ratio < 0.25) ratio = 0.25;

    double newDifficulty;
    if (Config::dynamicDifficultyEnabled) {
        newDifficulty = latestBlock->difficulty * ratio;
    } else {
        newDifficulty = 1.0;
    }

    // cout << "newDifficulty: " << newDifficulty << endl;
    
    return newDifficulty;
}

// uncle blockがあるかどうかのみで判断しているので、この難易度調整において考慮しているstale block数は1になる。
double calculateDifficultyETH(block* latestBlock) {
    if (latestBlock == nullptr || latestBlock->height == 0) {
        return 1.0;
    }

    if (latestBlock->prevBlock == nullptr) {
        return latestBlock->difficulty;
    }

    block* parentBlock = latestBlock->prevBlock;
    
    ll timeDiff = latestBlock->time - parentBlock->time;
    
    ll timeDiffSeconds = timeDiff / 1000;
    
    ll adjustmentFactor = std::max(1LL - timeDiffSeconds / 10LL, -99LL);

    double difficultyAdjustment = latestBlock->difficulty / 2048.0 * (double)adjustmentFactor;

    // 実際のuncle block検出を使用
    bool uncleExists = hasUncleBlock(latestBlock);
    // uncle adjustmentを現在の難易度に比例させる（実際のEthereumでは難易度に対して相対的に小さな値）
    // 実際のEthereumでは約 difficulty/2048 程度の影響なので、同様の比率を適用
    double uncleAdjustment = uncleExists ? (latestBlock->difficulty / 2048.0) : 0.0;

    double newDifficulty = latestBlock->difficulty + difficultyAdjustment + uncleAdjustment;

    if (newDifficulty < 0.1) {
        newDifficulty = 0.1;  // 最小値を0.1に修正
    }

    // cout << "newDifficulty: " << newDifficulty << endl;

    return newDifficulty;
}

// uncle block検出関数
bool hasUncleBlock(block* currentBlock) {
    if (currentBlock == nullptr || currentBlock->prevBlock == nullptr) {
        return false;
    }
    
    ll parentHeight = currentBlock->prevBlock->height;
    
    // 親ブロックと同じ高さで、異なるブロックが存在するかチェック
    if (blocksByHeight.find(parentHeight) != blocksByHeight.end()) {
        const vector<block*>& blocksAtHeight = blocksByHeight[parentHeight];
        
        // 同じ高さに2つ以上のブロックがある場合、uncle blockが存在する
        if (blocksAtHeight.size() > 1) {
            // さらに詳細な条件: 同じ親の親を持つブロックが複数存在するかチェック
            for (const block* otherBlock : blocksAtHeight) {
                if (otherBlock != currentBlock->prevBlock && 
                    otherBlock->prevBlock != nullptr &&
                    currentBlock->prevBlock->prevBlock != nullptr &&
                    otherBlock->prevBlock == currentBlock->prevBlock->prevBlock) {
                    return true;  // uncle blockが存在
                }
            }
        }
    }
    
    return false;
}

void finalizeBlocks(block* block1, int tie) {
    if (block1->height != END_ROUND) {
        ll height = block1->height; 
        block* curBlock = block1;
        
        // 144ブロックファイナリティ: 144ブロック前まで遡る
        // 144ブロックは、約1440min = 24時間 = 1日、つまり、一日分のブロック高が積みあがったらファイナライズすると考える。
        while (curBlock->height > 0 && curBlock->height != height - 144) {
            curBlock = curBlock->prevBlock;
            if (curBlock == nullptr) cout << "sugeeeee" << endl;
        }
        
        // 144ブロック前より前のブロックで、finalizedがfalseのもののみを処理
        if (curBlock != nullptr && curBlock->height > 0) {
            block* finalizedBlock = curBlock;
            while (finalizedBlock != nullptr && finalizedBlock->height > 0 && !finalizedBlock->finalized) {
                finalizedBlock->finalized = true;
                
                if (finalizedBlock->minter == highestHashrateNode && roundStartedBy[finalizedBlock->height] == highestHashrateNode) {
                    startedByA++;
                    startedByAAndMinedByA++;
                    highestHashrateNodeMinedBlocks[finalizedBlock->height] = true;
                } else if (finalizedBlock->minter == highestHashrateNode && roundStartedBy[finalizedBlock->height] != highestHashrateNode) {
                    startedByO++;
                    startedByOAndMinedByA++;
                    highestHashrateNodeMinedBlocks[finalizedBlock->height] = true;
                } else if (finalizedBlock->minter != highestHashrateNode && roundStartedBy[finalizedBlock->height] == highestHashrateNode) {
                    startedByA++;
                    startedByAAndMinedByO++;
                } else if (finalizedBlock->minter != highestHashrateNode && roundStartedBy[finalizedBlock->height] != highestHashrateNode) {
                    startedByO++;
                    startedByOAndMinedByO++;
                }
                
                // 各マイナー（0番目から9番目まで）のマイニングシェアを記録
                if (finalizedBlock->minter >= 0 && finalizedBlock->minter < 10) {
                    nodeMinedBlocks[finalizedBlock->minter][finalizedBlock->height] = true;
                    nodeMinedCount[finalizedBlock->minter]++;
                }
                
                finalizedBlock = finalizedBlock->prevBlock;
            }
        }
        
        if(curBlock->height > 0) numMain[tie][curBlock->minter]++;
        mainLength = max(mainLength, curBlock->height);
        return;
    } else {
        block* curBlock = block1;

        if (curBlock != nullptr && curBlock->height > 0) {
            block* finalizedBlock = curBlock;
            while (finalizedBlock != nullptr && finalizedBlock->height > 0 && !finalizedBlock->finalized) {
                finalizedBlock->finalized = true;
                
                if (finalizedBlock->minter == highestHashrateNode && roundStartedBy[finalizedBlock->height] == highestHashrateNode) {
                    startedByA++;
                    startedByAAndMinedByA++;
                    highestHashrateNodeMinedBlocks[finalizedBlock->height] = true;
                } else if (finalizedBlock->minter == highestHashrateNode && roundStartedBy[finalizedBlock->height] != highestHashrateNode) {
                    startedByO++;
                    startedByOAndMinedByA++;
                    highestHashrateNodeMinedBlocks[finalizedBlock->height] = true;
                } else if (finalizedBlock->minter != highestHashrateNode && roundStartedBy[finalizedBlock->height] == highestHashrateNode) {
                    startedByA++;
                    startedByAAndMinedByO++;
                } else if (finalizedBlock->minter != highestHashrateNode && roundStartedBy[finalizedBlock->height] != highestHashrateNode) {
                    startedByO++;
                    startedByOAndMinedByO++;
                }
                
                // 各マイナー（0番目から9番目まで）のマイニングシェアを記録
                if (finalizedBlock->minter >= 0 && finalizedBlock->minter < 10) {
                    nodeMinedBlocks[finalizedBlock->minter][finalizedBlock->height] = true;
                    nodeMinedCount[finalizedBlock->minter]++;
                }
                
                finalizedBlock = finalizedBlock->prevBlock;
            }
        }
    }
}

void reset() {
    currentRound = 0;
    currentTime = 0;
    mainLength = 0;
    for (int i = 0;i < Config::nodeCount;i++) {
        currentBlock[i] = nullptr;
        startedByA = 0;
        startedByO = 0;
        startedByAAndMinedByA = 0;
        startedByOAndMinedByO = 0;
        startedByAAndMinedByO = 0;
        startedByOAndMinedByA = 0;
    }

    for (int i = 0;i < END_ROUND; i++) {
        highestHashrateNodeMinedBlocks[i] = false;
        roundStarted[i] = false;
        roundStartedBy[i] = -1;
    }

    // 各マイナーのマイニングシェア追跡用変数を初期化
    for (int miner = 0; miner < 10; miner++) {
        nodeMinedCount[miner] = 0;
        for (int i = 0; i < END_ROUND; i++) {
            nodeMinedBlocks[miner][i] = false;
        }
    }

    // uncle block検出用のデータ構造をクリア
    blocksByHeight.clear();

    // ブロック生成間隔記録用のデータ構造をクリア
    blockGenerationIntervals.clear();
    lastBlockGenerationTime = -1;  // 初回は-1で初期化

    return;
}

void simulation(int tie, const std::string& timestamp_dir) {
    auto compare = [](task* a, task* b) {
      return a->time > b->time;
    };
    std::priority_queue<
      task*,
      std::vector<task*>,
      decltype(compare) // 比較関数オブジェクトを指定
    > taskQue {compare};
    
    std::queue<block*> blockQue;

    // メモリ再利用ロジックを無効化
    std::queue<block*> blockStore;
    std::queue<task*> taskStore;

    ll lastPlotTime = 0;
    ll plotInterval = (END_ROUND * Config::targetGenerationTime) / 100LL;
    if (plotInterval == 0) plotInterval = Config::targetGenerationTime;

    // CSVファイル用の出力ストリームを作成（出力先: ./data 配下）
    ofstream csvFile;
    std::string blockchain_prefix = Config::getBlockchainTypeName();
    std::string difficulty_prefix = Config::dynamicDifficultyEnabled ? "dynamic" : "static";
    std::string rule_name = getRuleName(tie);
    openCsvFile(timestamp_dir, blockchain_prefix + "_" + std::to_string(delay) + "_" + std::to_string(Config::nodeCount) + "_" + std::to_string(END_ROUND) + "_" + rule_name + "_" + difficulty_prefix + "_share", csvFile);
    

    block* genesisBlock = createGenesisBlock();
    blockQue.push(genesisBlock);

    for (int i = 0;i < Config::nodeCount;i++) {
        currentBlock[i] = genesisBlock;

        task* nextBlockTask = new task;
        double initialDifficulty = 1.0;
        double baseTime = (double)Config::targetGenerationTime * (double)totalHashrate / (double)hashrate[i];
        double adjustedTime = baseTime * initialDifficulty;
        
        ll miningTime = (ll)(exp_dist(random_value) * adjustedTime);
        nextBlockTask->time = miningTime;
        nextBlockTask->flag = TaskType::BLOCK_GENERATION;
        nextBlockTask->minter = i;
        taskQue.push(nextBlockTask);
        currentMiningTask[i] = nextBlockTask;
    }

    while(taskQue.size() > 0 && currentRound < END_ROUND) {
        task* currentTask = taskQue.top();
        taskQue.pop();
        currentTime = currentTask->time;

        if (currentTask->flag == TaskType::BLOCK_GENERATION) {
            int minter = currentTask->minter;
            if (currentMiningTask[minter] != currentTask) {
                continue;
            }
            
            
            block* newBlock;
            if (blockStore.size() > 0) {
                newBlock = blockStore.front();blockStore.pop();
            } else {
                newBlock = new block;
            }
            
            // 再利用したブロックのメンバを適切に初期化
            newBlock->prevBlock = currentBlock[minter];
            newBlock->height = currentBlock[minter]->height + 1;
            newBlock->minter = minter;
            newBlock->time = currentTime;
            newBlock->rand = uni_dist(random_value) * (LLONG_MAX - 10);
            newBlock->lastEpochTime = currentBlock[minter]->lastEpochTime;
            newBlock->difficulty = currentBlock[minter]->difficulty;  // 初期値として設定
            newBlock->finalized = false;  // デフォルト値

            newBlock->difficulty = calculateDifficulty(currentBlock[minter]);
            if (newBlock->height % Config::difficultyAdjustmentInterval == 1) {
                newBlock->lastEpochTime = currentBlock[minter]->time;
            }
            
            currentBlock[minter] = newBlock;

            // uncle block検出用にブロックを記録
            blocksByHeight[newBlock->height].push_back(newBlock);

            // ブロック生成イベント間の時間間隔を記録（初回を除く）
            if (lastBlockGenerationTime != -1) {
                ll generationInterval = newBlock->time - lastBlockGenerationTime;
                blockGenerationIntervals.push_back(generationInterval);
            }
            lastBlockGenerationTime = newBlock->time;

            blockQue.push(newBlock);
            if (blockQue.size() > 10000) {
                block* deleteBlock = blockQue.front();blockQue.pop();
                blockStore.push(deleteBlock);
            }

            task* nextBlockTask;
            if (taskStore.size() > 0) {
                nextBlockTask = taskStore.front();taskStore.pop();
            } else {
                nextBlockTask = new task;
            }

            double baseTime = (double)Config::targetGenerationTime * (double)totalHashrate / (double)hashrate[minter];
            double adjustedTime = baseTime * newBlock->difficulty;
            
            double randomFactor = exp_dist(random_value);
            ll miningTime = (ll)(randomFactor * adjustedTime);
            nextBlockTask->time = currentTime + miningTime;
            
            nextBlockTask->flag = TaskType::BLOCK_GENERATION;
            nextBlockTask->minter = minter;
            taskQue.push(nextBlockTask);
            currentMiningTask[minter] = nextBlockTask;

            for (int i = 0;i < Config::nodeCount;i++) { // propagation task
                task* nextPropTask;
                if (taskStore.size() > 0) {
                    nextPropTask = taskStore.front();taskStore.pop();
                } else {
                    nextPropTask = new task;
                }
                nextPropTask->time = currentTime + getPropagationTime(minter, i);
                nextPropTask->flag = TaskType::PROPAGATION;
                nextPropTask->to = i;
                nextPropTask->from = minter;
                nextPropTask->propagatedBlock = newBlock;
                taskQue.push(nextPropTask);
            }

            if (!roundStarted[newBlock->height]) {
                roundStarted[newBlock->height] = true;
                roundStartedBy[newBlock->height] = minter;
                finalizeBlocks(newBlock, tie);
            }
            if (currentRound < newBlock->height) {
                currentRound = newBlock->height;
            }

            if (newBlock->height == 100000) {
                finalizeBlocks(newBlock, tie);
            }

        } else { // propagation
            int to = currentTask->to;
            int from = currentTask->from;
            bool mainchainChanged = chooseMainchain(currentTask->propagatedBlock, currentBlock[to], from, to, tie);
            
            if (mainchainChanged) {
                double latestDifficulty = calculateDifficulty(currentBlock[to]);
                
                task* newMiningTask;
                if (taskStore.size() > 0) {
                    newMiningTask = taskStore.front();taskStore.pop();
                } else {
                    newMiningTask = new task;
                }
                
                double baseTime = (double)Config::targetGenerationTime * (double)totalHashrate / (double)hashrate[to];
                double adjustedTime = baseTime * latestDifficulty;
                
                double randomFactor = exp_dist(random_value);
                ll miningTime = (ll)(randomFactor * adjustedTime);
                newMiningTask->time = currentTime + miningTime;
                newMiningTask->flag = TaskType::BLOCK_GENERATION;
                newMiningTask->minter = to;
                taskQue.push(newMiningTask);
                currentMiningTask[to] = newMiningTask;
            }
        }
        taskStore.push(currentTask);
    }

    if (taskQue.empty()) {
        cout << "--- Simulation stopped: Task queue is empty. ---" << endl;
    } else {
        cout << "--- Simulation finished normally. ---" << endl;
    }
    cout << "Final block height: " << currentRound << endl;
    cout << "Current time: " << currentTime << " ms" << endl;
    // 各マイナーが currentRound を更新した回数を出力
    cout << "CurrentRound update counts by miner:" << endl;
    if (startedByA > 0) {
        cout << "w_A: " << (double)startedByAAndMinedByA / (double)startedByA << endl;
    } else {
        cout << "w_A: 0" << endl;
    }
    if (startedByO > 0) {
        cout << "w_O: " << (double)startedByOAndMinedByA / (double)startedByO << endl;
    } else {
        cout << "w_O: 0" << endl;
    }
    cout << "startedByA: " << startedByA << endl;
    cout << "startedByO: " << startedByO << endl;
    cout << "startedByAAndMinedByA: " << startedByAAndMinedByA << endl;
    cout << "startedByOAndMinedByO: " << startedByOAndMinedByO << endl;
    cout << "startedByAAndMinedByO: " << startedByAAndMinedByO << endl;
    cout << "startedByOAndMinedByA: " << startedByOAndMinedByA << endl;

    cout << "pi_A and pi_O" << endl;
    cout << "pi_A: " << (double)startedByA / (double)END_ROUND << endl;
    cout << "pi_O: " << (double)startedByO / (double)END_ROUND << endl;

    double w_A = (double)startedByAAndMinedByA / (double)startedByA;
    double w_O = (double)startedByOAndMinedByA / (double)startedByO;
    double pi_A = (double)startedByA / (double)END_ROUND;
    double pi_O = (double)startedByO / (double)END_ROUND;

    double r_A = pi_A * w_A + (1 - pi_A) * w_O;

    cout << "r_A calculated by experiment data: " << r_A << endl;

    ll minedCount = 0;
    for (int i = 0; i < END_ROUND; i++) {
        if (highestHashrateNodeMinedBlocks[i]) {
            minedCount++;
        }
        csvFile << i << ": " << (double)minedCount / (double)(i+1) << endl;
    }
    cout << "r_A from data: " << (double)minedCount / (double)END_ROUND << endl;

    csvFile.close();
    
    // 各マイナー（0番目から9番目まで）のマイニングシェアCSVファイルを作成
    createNodeShareCsvFiles(timestamp_dir, tie);
    writeNodeShareData(timestamp_dir, tie);
}

string createTimestampDirectory() {
    // 現在時刻を取得
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    
    // タイムスタンプを文字列に変換
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time_t), "%Y%m%d_%H%M%S");
    std::string timestamp = ss.str();
    
    // ディレクトリパスを構築
    std::string dir_path = "data/" + timestamp;
    
    // ディレクトリを作成
    struct stat st;
    if (stat("data", &st) != 0) {
        mkdir("data", 0777);
    }
    if (stat(dir_path.c_str(), &st) != 0) {
        mkdir(dir_path.c_str(), 0777);
    }
    
    return dir_path;
}

void openCsvFile(string filePath, string fileName, ofstream& csvFile) {
    // ディレクトリが存在しない場合は作成
    struct stat st;
    if (stat(filePath.c_str(), &st) != 0) {
        mkdir(filePath.c_str(), 0777);
    }
    
    // 完全なファイル名を構築（delta_node数_endround数.csv の形式）
    std::string fullFileName = filePath + "/" + fileName + ".csv";
    
    // CSVファイルを開く
    csvFile.open(fullFileName);
    if (!csvFile.is_open()) {
        cerr << "[error] Failed to open CSV file: " << fullFileName << endl;
    } else {
        cout << "[info] Writing CSV to: " << fullFileName << endl;
    }
}

// 各ノードのマイニングシェアCSVファイルを作成する関数
void createNodeShareCsvFiles(const std::string& timestamp_dir, int tie) {
    std::string blockchain_prefix = Config::getBlockchainTypeName();
    std::string difficulty_prefix = Config::dynamicDifficultyEnabled ? "dynamic" : "static";
    std::string rule_name = getRuleName(tie);
    
    // 各マイナー（0番目から9番目まで）のCSVファイルを作成
    for (int miner = 0; miner < 10; miner++) {
        std::string miner_filename = "miner_" + std::to_string(miner) + "_" + blockchain_prefix + "_" + 
                                   std::to_string(delay) + "_" + std::to_string(Config::nodeCount) + "_" + 
                                   std::to_string(END_ROUND) + "_" + rule_name + "_" + difficulty_prefix + "_share";
        
        ofstream miner_csv_file;
        openCsvFile(timestamp_dir, miner_filename, miner_csv_file);
        
        if (miner_csv_file.is_open()) {
            cout << "[info] Created miner " << miner << " share CSV file" << endl;
            miner_csv_file.close();
        }
    }
}

// 各マイナーのマイニングシェアデータを書き込む関数
void writeNodeShareData(const std::string& timestamp_dir, int tie) {
    std::string blockchain_prefix = Config::getBlockchainTypeName();
    std::string difficulty_prefix = Config::dynamicDifficultyEnabled ? "dynamic" : "static";
    std::string rule_name = getRuleName(tie);
    
    // 各マイナー（0番目から9番目まで）のデータを書き込み
    for (int miner = 0; miner < 10; miner++) {
        std::string miner_filename = "miner_" + std::to_string(miner) + "_" + blockchain_prefix + "_" + 
                                   std::to_string(delay) + "_" + std::to_string(Config::nodeCount) + "_" + 
                                   std::to_string(END_ROUND) + "_" + rule_name + "_" + difficulty_prefix + "_share";
        
        ofstream miner_csv_file;
        openCsvFile(timestamp_dir, miner_filename, miner_csv_file);
        
        if (miner_csv_file.is_open()) {
            ll minerMinedCountSoFar = 0;
            for (int i = 0; i < END_ROUND; i++) {
                if (nodeMinedBlocks[miner][i]) {
                    minerMinedCountSoFar++;
                }
                miner_csv_file << i << ": " << (double)minerMinedCountSoFar / (double)(i+1) << endl;
            }
            miner_csv_file.close();
            cout << "[info] Wrote miner " << miner << " share data: " << nodeMinedCount[miner] << " blocks mined" << endl;
        }
    }
}
