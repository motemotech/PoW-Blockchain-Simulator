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
#include "../include/config.h"
using namespace std;

int currentRoundStarter;
ll currentRound;
ll currentTime = 0;
block* currentBlock[MAX_N];
task* currentMiningTask[MAX_N];
ll hashrate[MAX_N]; // ノードのハッシュレート
ll totalHashrate;
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

ll delay;

bool chooseMainchain(block* block1, block* block2, int from, int to, int tie);
void finalizeBlocks(block* block1, int tie);
void saveDataInCsv(string filePath, string fileName, ofstream& csvFile);
void writeDataToCsv(ofstream& csvFile, ll height, ll time, double proportion, double difficulty);
void simulation(int tie, const std::string& timestamp_dir);
void reset();
ll getPropagationTime(int i, int j);
double calculateDifficulty(block* latestBlock, int nodeId);  // ノード固有の難易度計算関数
void openCsvFile(string filePath, string fileName, ofstream& csvFile);
string createTimestampDirectory();

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

int main(void) {
    cout << "Start Blockchain Simulator" << endl;
    Config::initializeDefaults();

    ll highestHashrateNodeMainChainCount = 0;

    // タイムスタンプベースのディレクトリを作成
    std::string timestamp_dir = createTimestampDirectory();

    // w_A, w_O, pi_A, pi_O の値を記録するCSVファイルを作成
    std::string difficulty_type = Config::dynamicDifficultyEnabled ? "dynamic" : "static";
    std::string w_and_pi_filename = timestamp_dir + "/" + std::to_string(Config::nodeCount) + "_" + std::to_string(END_ROUND) + "_" + difficulty_type + "_w_pi.csv";
    ofstream w_and_pi_file(w_and_pi_filename);
    
    if (!w_and_pi_file.is_open()) {
        cerr << "[error] Failed to open w_and_pi CSV file: " << w_and_pi_filename << endl;
        return 1;
    } else {
        cout << "[info] Writing w_and_pi CSV to: " << w_and_pi_filename << endl;
    }
    
    // CSVファイルのヘッダーを書き込み
    w_and_pi_file << "delay,pi_A,pi_O,w_A,w_O" << endl;

    for (ll current_delay : Config::delayValues) {
      // hashrate[0] = Config::nodeCount - 1;
      hashrate[0] = 10000;
       for (int i = 1; i < Config::nodeCount; i++) {
           hashrate[i] = 1;
       }

       totalHashrate = 0;
       for (int i = 0; i < Config::nodeCount; i++) {
           totalHashrate += hashrate[i];
       }
       delay = current_delay;
       cout << "--- Running simulation with delay: " << delay << " ---" << endl;
       reset();
       simulation(0, timestamp_dir);
       
       // シミュレーション後にw_A, w_O, pi_A, pi_Oの値を計算してCSVに書き込み
       double pi_A = (double)startedByA / (double)END_ROUND;
       double pi_O = (double)startedByO / (double)END_ROUND;
       double w_A = (startedByA > 0) ? (double)startedByAAndMinedByA / (double)startedByA : 0.0;
       double w_O = (startedByO > 0) ? (double)startedByOAndMinedByA / (double)startedByO : 0.0;
       
       w_and_pi_file << delay << "," << pi_A << "," << pi_O << "," << w_A << "," << w_O << endl;
       cout << "Recorded: delay=" << delay << ", pi_A=" << pi_A << ", pi_O=" << pi_O 
            << ", w_A=" << w_A << ", w_O=" << w_O << endl;
    }

    cout << "--- All simulations finished. ---" << endl;

    // w_and_pi CSVファイルをクローズ
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

    return false; // メインチェーンは変更されなかった
}

ll getPropagationTime(int i, int j) {
    if (i == j) return 0;
    else return delay;
}

double calculateDifficulty(block* latestBlock, int nodeId) {
    if (latestBlock == nullptr || latestBlock->height == 0) {
        return 1.0;
    }
    
    if (latestBlock->height % DIFFICULTY_ADJUSTMENT_INTERVAL != 0) {
        return latestBlock->difficulty;
    }
    
    if (latestBlock->height < DIFFICULTY_ADJUSTMENT_INTERVAL) {
        return latestBlock->difficulty; 
    }
    
    // cout << "latestBlock->time: " << latestBlock->time << endl;
    // cout << "latestBlock->lastEpochTime: " << latestBlock->lastEpochTime << endl;
    ll actualTimespan = latestBlock->time - latestBlock->lastEpochTime;
    // cout << "actualTimespan: " << actualTimespan << endl;
    double ratio = (double)TARGET_TIMESPAN / (double)actualTimespan;
    // cout << "ratio: " << ratio << endl;
    if (ratio > 4.0) ratio = 4.0;
    if (ratio < 0.25) ratio = 0.25;

    double newDifficulty;
    if (Config::dynamicDifficultyEnabled) {
        newDifficulty = latestBlock->difficulty * ratio;
    } else {
        newDifficulty = 1.0;
    }
    
    return newDifficulty;
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
    ll plotInterval = (END_ROUND * TARGET_GENERATION_TIME) / 100LL;
    if (plotInterval == 0) plotInterval = TARGET_GENERATION_TIME;

    // CSVファイル用の出力ストリームを作成（出力先: ./data 配下）
    ofstream csvFile;
    std::string difficulty_prefix = Config::dynamicDifficultyEnabled ? "dynamic" : "static";
    openCsvFile(timestamp_dir, std::to_string(delay) + "_" + std::to_string(Config::nodeCount) + "_" + std::to_string(END_ROUND) + "_" + difficulty_prefix + "_share", csvFile);
    

    block* genesisBlock = createGenesisBlock();
    blockQue.push(genesisBlock);

    for (int i = 0;i < Config::nodeCount;i++) {
        currentBlock[i] = genesisBlock;

        task* nextBlockTask = new task;
        // 初期難易度を考慮したマイニング時間の計算
        double initialDifficulty = 1.0;
        double baseTime = (double)TARGET_GENERATION_TIME * (double)totalHashrate / (double)hashrate[i];
        double adjustedTime = baseTime * initialDifficulty;
        
        ll miningTime = (ll)(exp_dist(random_value) * adjustedTime);
        nextBlockTask->time = miningTime;
        nextBlockTask->flag = TaskType::BLOCK_GENERATION;
        nextBlockTask->minter = i;
        taskQue.push(nextBlockTask);
        currentMiningTask[i] = nextBlockTask;
    }

    // taskQueが空になるか、currentRoundがEND_ROUNDになるまでループを実行する。
    while(taskQue.size() > 0 && currentRound < END_ROUND) {
        task* currentTask = taskQue.top();
        taskQue.pop();
        currentTime = currentTask->time;

        if (currentTask->flag == TaskType::BLOCK_GENERATION) { //block generation
            int minter = currentTask->minter;
            if (currentMiningTask[minter] != currentTask) {
                continue;
            }
            
            
            block* newBlock;
            if (blockStore.size() > 0) {
                newBlock = blockStore.front();blockStore.pop();
                // cout << "Reusing block from blockStore, address: " << newBlock << endl;
            } else {
                newBlock = new block;
                // cout << "Creating new block, address: " << newBlock << endl;
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

            // cout << "Block created: miner=" << newBlock->minter << ", height=" << newBlock->height 
            //      << ", lastEpochTime=" << newBlock->lastEpochTime << endl;
            newBlock->difficulty = calculateDifficulty(currentBlock[minter], minter);
            if (newBlock->height % DIFFICULTY_ADJUSTMENT_INTERVAL == 1) {
                newBlock->lastEpochTime = currentBlock[minter]->time;
            }
            
            currentBlock[minter] = newBlock;
            // cout << "Updated currentBlock[" << minter << "] to new block" << endl;

            blockQue.push(newBlock);
            if (blockQue.size() > 10000) {
                block* deleteBlock = blockQue.front();blockQue.pop();
                // cout << "Pushing block to blockStore, address: " << deleteBlock << ", height: " << deleteBlock->height << endl;
                blockStore.push(deleteBlock);
            }

            task* nextBlockTask;
            if (taskStore.size() > 0) {
                nextBlockTask = taskStore.front();taskStore.pop();
            } else {
                nextBlockTask = new task;
            }

            double baseTime = (double)TARGET_GENERATION_TIME * (double)totalHashrate / (double)hashrate[minter];
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
                cout << "finalizeBlocks" << endl;
                finalizeBlocks(newBlock, tie);
            }

        } else { // propagation
            int to = currentTask->to;
            int from = currentTask->from;
            bool mainchainChanged = chooseMainchain(currentTask->propagatedBlock, currentBlock[to], from, to, tie);
            
            if (mainchainChanged) {
                double latestDifficulty = calculateDifficulty(currentBlock[to], to);
                
                task* newMiningTask;
                if (taskStore.size() > 0) {
                    newMiningTask = taskStore.front();taskStore.pop();
                } else {
                    newMiningTask = new task;
                }
                
                double baseTime = (double)TARGET_GENERATION_TIME * (double)totalHashrate / (double)hashrate[to];
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

    cout << "highestHashrateNodeMinedBlocks" << endl;
    ll minedCount = 0;
    for (int i = 0; i < END_ROUND; i++) {
        if (highestHashrateNodeMinedBlocks[i]) {
            minedCount++;
        }
        csvFile << i << ": " << (double)minedCount / (double)(i+1) << endl;
    }
    cout << "r_A from data: " << (double)minedCount / (double)END_ROUND << endl;

    csvFile.close();
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
