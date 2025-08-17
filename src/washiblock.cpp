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
using namespace std;

typedef unsigned long long ull;
typedef long long ll;

#define MAX_RN 10
#define MAX_N 1000
#define DIFFICULTY_ADJUSTMENT_INTERVAL 2016  // 2016ブロックごとに調整
// #define TARGET_TIMESPAN (DIFFICULTY_ADJUSTMENT_INTERVAL * TARGET_BLOCK_TIME) // 2週間相当
const ll END_ROUND = 1000000;
const ll TARGET_BLOCK_TIME = 600000;
const ll TARGET_TIMESPAN = DIFFICULTY_ADJUSTMENT_INTERVAL * TARGET_BLOCK_TIME;
using namespace std;

// trueにすると動的難易度調整が有効になり、falseにすると難易度が1.0に固定されます。
// これに応じて、出力されるファイル名も変わります。
const bool DYNAMIC_DIFFICULTY_ENABLED = false;

// const std::array<ll, 20> HASH_RATE_ARRAY = {19, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1};
// const std::array<ll, 40> HASH_RATE_ARRAY = {39, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1};

struct block {
    ll height;
    block* prevBlock;
    int minter; 
    ll time;
    ll rand;
    double difficulty;  // このブロック生成時の難易度
    ll lastEpochTime;   // 前回の難易度調整時刻（2016ブロック前）
    bool finalized = false;
    
    // コンストラクタを追加してメンバを初期化
    block() : height(0), prevBlock(nullptr), minter(-1),
              time(0), rand(0), difficulty(1.0), lastEpochTime(0), finalized(false) {}
};

struct task {
    ll time;
    int flag; // 0 = block, 1 = propagation
    int minter; // 0
    int from; // 1
    int to; // 1
    block* propagatedBlock;
};

int currentRoundStarter;
ll currentRound;
ll currentTime = 0;
ll delay = 60000; // 6000, 60000, 300000 ブロックの伝搬遅延
ll generationTime = 600000;
block* currentBlock[MAX_N];
task* currentMiningTask[MAX_N];
ll hashrate[MAX_N];
ll totalHashrate;
ll numMain[3][MAX_N];
ll propagation[MAX_N][MAX_N];
ll mainLength;
int N = 40;// num of node
int highestHashrateNode = 0;  // 最高ハッシュレートのノードID
// 各マイナーが currentRound を更新した回数を記録
ll currentRoundUpdateCount[MAX_N];

// 各マイナーのブロックが144ブロックファイナリティを達成した回数を記録
// ll roundWinCount[MAX_N];

ll startedByA;
ll startedByO;
ll startedByAAndMinedByA;
ll startedByOAndMinedByO;
ll startedByAAndMinedByO;
ll startedByOAndMinedByA;

bool roundStarted[END_ROUND];
int roundStartedBy[END_ROUND];

ll highestHashrateNodeMainChainCount = 0;

bool highestHashrateNodeMinedBlocks[END_ROUND];

bool chooseMainchain(block* block1, block* block2, int from, int to, int tie);
void finalizeBlocks(block* block1, int tie);
void saveDataInCsv(string filePath, string fileName, ofstream& csvFile);
void writeDataToCsv(ofstream& csvFile, ll height, ll time, double proportion, double difficulty);
void simulation(int tie);
void reset();
ll getPropagationTime(int i, int j);
double calculateDifficulty(block* latestBlock, int nodeId);  // ノード固有の難易度計算関数

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
    cout << "akira" << endl;
    //const std::array<ll, 24> delay_values = {
        //300000, 600000, 1500000, 3000000, 4500000, 6000000, 7500000, 
        //9000000, 1050000, 1200000, 1350000, 1500000, 1650000, 
        //1800000, 1950000, 2100000, 2250000, 2400000, 2550000,
       //2700000, 2850000, 3000000, 4500000, 6000000
    //};
    const std::array<ll, 4> delay_values = {
   	3000000, 4500000, 6000000
    };

    // w_A, w_O, pi_A, pi_O の値を記録するCSVファイルを作成
    const std::string output_dir = "tmp_data";
    struct stat st;
    if (stat(output_dir.c_str(), &st) != 0) {
        mkdir(output_dir.c_str(), 0777);
    }
    
    std::string filename_suffix = DYNAMIC_DIFFICULTY_ENABLED ? "w_and_pi.csv" : "static_w_and_pi.csv";
    std::string w_and_pi_filename = output_dir + "/" + std::to_string(END_ROUND) + filename_suffix;
    ofstream w_and_pi_file(w_and_pi_filename);
    
    if (!w_and_pi_file.is_open()) {
        cerr << "[error] Failed to open w_and_pi CSV file: " << w_and_pi_filename << endl;
        return 1;
    } else {
        cout << "[info] Writing w_and_pi CSV to: " << w_and_pi_filename << endl;
    }
    
    // CSVファイルのヘッダーを書き込み
    w_and_pi_file << "delay,pi_A,pi_O,w_A,w_O" << endl;

    // hashrate[0] = N - 1;
    // for (int i = 1;i < N;i++) {
    //     hashrate[i] = 1;
    // }


    // for (int i = 0;i < N;i++) {
    //      for (int j = 0;j < N;j++) {
    //          getPropagationTime(i, j);
    //      }
    // }

    // simulation(0);

    // cout << "block propagation time: " << delay << endl;

    for (ll current_delay : delay_values) {
      hashrate[0] = 50;
       for (int i = 1; i < N; i++) {
           hashrate[i] = 1;
       }

       totalHashrate = 0;
       for (int i = 0; i < N; i++) {
           totalHashrate += hashrate[i];
       }
       delay = current_delay;
       cout << "--- Running simulation with delay: " << delay << " ---" << endl;
       reset();
       simulation(0);
       
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
    if (DYNAMIC_DIFFICULTY_ENABLED) {
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
        cout << "finalizeBlocks" << endl;
        block* curBlock = block1;
        // while (curBlock->height > mainLength) {
        //     numMain[tie][curBlock->minter]++;
        //     curBlock = curBlock->prevBlock;
        // }

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
    for (int i = 0;i < N;i++) {
        currentBlock[i] = nullptr;
        currentRoundUpdateCount[i] = 0; // リセット
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

void openCsvFile(string filePath, string fileName, ofstream& csvFile) {
    // ディレクトリが存在しない場合は作成
    struct stat st;
    if (stat(filePath.c_str(), &st) != 0) {
        mkdir(filePath.c_str(), 0777);
    }
    
    // ファイル名のサフィックスを決定
    std::string filename_suffix;
    if (!DYNAMIC_DIFFICULTY_ENABLED) {
        filename_suffix = "_static_plot.csv";
    } else {
        filename_suffix = "_plot.csv";
    }
    
    // 完全なファイル名を構築
    std::string fullFileName = filePath + "/" + fileName + filename_suffix;
    
    // CSVファイルを開く
    csvFile.open(fullFileName);
    if (!csvFile.is_open()) {
        cerr << "[error] Failed to open CSV file: " << fullFileName << endl;
    } else {
        cout << "[info] Writing CSV to: " << fullFileName << endl;
    }
}

void simulation(int tie) {
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
    ll plotInterval = (END_ROUND * TARGET_BLOCK_TIME) / 100LL;
    if (plotInterval == 0) plotInterval = TARGET_BLOCK_TIME;

    // CSVファイル用の出力ストリームを作成（出力先: ./data 配下）
    const std::string output_dir = "tmp_data";
    ofstream csvFile;
    openCsvFile(output_dir, std::to_string(delay) + "_" + std::to_string(generationTime) + "_" + std::to_string(END_ROUND), csvFile);
    

    // ========== 最初のブロックを生成 ==========
    block* genesisBlock = createGenesisBlock();
    blockQue.push(genesisBlock);

    // ========== 最初のマイナーのタスクを設定 ==========
    // Setting up the initial block to each miner
    // baseTimeは、ターゲットとなる生成間隔に対して、ノードのハッシュレート割合の逆数をかけたもの。
    // なので、平均的にどれくらいの時間でそのノードがブロックをマイニングするか表したもの
    // adjustedTimeは、baseTimeに対して難易度をかけて調整したもの。
    // minigTimeは、指数分布に従うようにしている
    // taskQueという優先度付きキューは、timeの早い順に並んでいる。
    // この場合は、minigTimeの小さい順 <- これはcompare関数で決められている。
    for (int i = 0;i < N;i++) {
        currentBlock[i] = genesisBlock;

        task* nextBlockTask = new task;
        // 初期難易度を考慮したマイニング時間の計算
        double initialDifficulty = 1.0;
        double baseTime = (double)generationTime * (double)totalHashrate / (double)hashrate[i];
        double adjustedTime = baseTime * initialDifficulty;
        
        ll miningTime = (ll)(exp_dist(random_value) * adjustedTime);
        nextBlockTask->time = miningTime;
        nextBlockTask->flag = 0;
        nextBlockTask->minter = i;
        taskQue.push(nextBlockTask);
        currentMiningTask[i] = nextBlockTask;
    }

    // taskQueが空になるか、currentRoundがEND_ROUNDになるまでループを実行する。
    while(taskQue.size() > 0 && currentRound < END_ROUND) {
        task* currentTask = taskQue.top();
        taskQue.pop();
        currentTime = currentTask->time;

        if (currentTask->flag == 0) { //block generation
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
            
            // double nextDifficulty = calculateDifficulty(newBlock, minter);
            // cout << "newBlock->difficulty: " << newBlock->difficulty << endl;
            // cout << "nextDifficulty: " << nextDifficulty << endl;
            double baseTime = (double)generationTime * (double)totalHashrate / (double)hashrate[minter];
            // cout << "baseTime: " << baseTime << endl;
            double adjustedTime = baseTime * newBlock->difficulty;
            // cout << "adjustedTime: " << adjustedTime << endl;
            
            double randomFactor = exp_dist(random_value);
            // cout << "randomFactor: " << randomFactor << endl;
            ll miningTime = (ll)(randomFactor * adjustedTime);
            // cout << "miningTime: " << miningTime << endl;
            // cout << "currentTime: " << currentTime << endl;
            nextBlockTask->time = currentTime + miningTime;
            
            nextBlockTask->flag = 0;
            nextBlockTask->minter = minter;
            taskQue.push(nextBlockTask);
            currentMiningTask[minter] = nextBlockTask;
            // cout << "nextBlockTask->time: " << nextBlockTask->time << endl;

            for (int i = 0;i < N;i++) { // propagation task
                task* nextPropTask;
                if (taskStore.size() > 0) {
                    nextPropTask = taskStore.front();taskStore.pop();
                } else {
                    nextPropTask = new task;
                }
                nextPropTask->time = currentTime + getPropagationTime(minter, i);
                nextPropTask->flag = 1;
                nextPropTask->to = i;
                nextPropTask->from = minter;
                nextPropTask->propagatedBlock = newBlock;
                taskQue.push(nextPropTask);
                // cout << "nextPropTask->time: " << nextPropTask->time << endl;
            }

            // wとpiの精度改善案
            // 144 heightごとにファイナライズするので、初めて、そのheightの高さをmineしたマイナーを配列などで記録していく。
            // ファイナライズするときに、その高さを初めてマイニングしたマイナーとの比較を行っていく。
            if (!roundStarted[newBlock->height]) {
                roundStarted[newBlock->height] = true;
                roundStartedBy[newBlock->height] = minter;
                // cout << "roundStartedBy[" << newBlock->height << "]: " << minter << endl;
                finalizeBlocks(newBlock, tie);
            }
            if (currentRound < newBlock->height) {
                currentRound = newBlock->height;
            }
            // if(currentRound < newBlock->height) {
            //     // cout << "currentRound: " << currentRound << ", newBlock->height: " << newBlock->height  << "roundStarter: " << minter << endl;
            //     currentRound = newBlock->height;
            //     // currentRound を更新したマイナーをカウント
            //     // つまり、　Roundを開始したマイナーのこと
            //     if (minter >= 0 && minter < N) {
            //         currentRoundUpdateCount[minter]++;
            //     }
            //     currentRoundStarter = minter;
                
            //     // currentRoundが更新された際に、144ブロック前のブロックをファイナライズ
            //     finalizeBlocks(newBlock, tie);
                
            //     // cout << "blockgeneration, miner: " << minter << ", height: " << newBlock->height << ", difficulty: " << newBlock->difficulty << ", time: " << currentTime << endl;
            // }

            if (newBlock->height == 100000) {
                cout << "finalizeBlocks" << endl;
                finalizeBlocks(newBlock, tie);
            }

        } else { // propagation
            int to = currentTask->to;
            int from = currentTask->from;
            bool mainchainChanged = chooseMainchain(currentTask->propagatedBlock, currentBlock[to], from, to, tie);
            
            if (mainchainChanged) {
                // 新しいメインチェーンの先端ブロックに基づいて、次のマイニングの難易度を計算
                double latestDifficulty = calculateDifficulty(currentBlock[to], to);
                
                task* newMiningTask;
                if (taskStore.size() > 0) {
                    newMiningTask = taskStore.front();taskStore.pop();
                } else {
                    newMiningTask = new task;
                }
                
                double baseTime = (double)generationTime * (double)totalHashrate / (double)hashrate[to];
                double adjustedTime = baseTime * latestDifficulty;
                
                double randomFactor = exp_dist(random_value);
                ll miningTime = (ll)(randomFactor * adjustedTime);
                newMiningTask->time = currentTime + miningTime;
                newMiningTask->flag = 0;
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
    
    // csvFile << "RoundWinCount" << endl;
    // csvFile << "MinerID,Count" << endl;
    // for (int i = 0; i < N; i++) {
    //     csvFile << i << "," << roundWinCount[i] << endl;
    // }
    // csvFile << endl;
    
    // // 2. すべてのminterのcurrentRoundUpdateCount
    // csvFile << "CurrentRoundUpdateCount" << endl;
    // csvFile << "MinerID,Count" << endl;
    // for (int i = 0; i < N; i++) {
    //     csvFile << i << "," << currentRoundUpdateCount[i] << endl;
    // }
    // csvFile << endl;
    
    // // 3. highestHashrateNodeMinedBlocksの配列
    // csvFile << "HighestHashrateNodeMinedBlocks" << endl;
    // csvFile << "BlockHeight,WasMinedByHighestHashrateNode" << endl;
    // for (ll height = 1; height <= currentRound; height++) {
    //     if (height < END_ROUND) {
    //         csvFile << height << "," << (highestHashrateNodeMinedBlocks[height] ? "1" : "0") << endl;
    //     }
    // }

    csvFile.close();
}
