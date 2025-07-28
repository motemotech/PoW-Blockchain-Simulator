#include <iostream>
#include <fstream>
#include <random>
#include <queue>
#include <cmath>
#include <iomanip>
#include <climits>
#include <array>
using namespace std;


#define MAX_RN 10
#define MAX_N 1000
#define DIFFICULTY_ADJUSTMENT_INTERVAL 2016  // 2016ブロックごとに調整
#define TARGET_BLOCK_TIME 600000            // 10分（ミリ秒）
#define TARGET_TIMESPAN (DIFFICULTY_ADJUSTMENT_INTERVAL * TARGET_BLOCK_TIME) // 2週間相当
using namespace std;
typedef unsigned long long ull;
typedef long long ll;
const std::array<ll, 10> HASH_RATE_ARRAY = {9, 1, 1, 1, 1, 1, 1, 1, 1, 1};

struct block {
    ll height;
    block* prevBlock;
    int minter; 
    ll time;
    ll rand;
    double difficulty;  // このブロック生成時の難易度
    ll lastEpochTime;   // 前回の難易度調整時刻（2016ブロック前）
};

struct task {
    ll time;
    int flag; // 0 = block, 1 = propagation
    int minter; // 0
    int from; // 1
    int to; // 1
    block* propagatedBlock;
};

ll currentRound;
ll currentTime = 0;
ll delay = 6000; // 6000, 60000, 300000 ブロックの伝搬遅延
ll generationTime = 600000;
block* currentBlock[MAX_N];
task* currentMiningTask[MAX_N];
ll hashrate[MAX_N];
ll totalHashrate;
ll numMain[3][MAX_N];
ll endRound = 100000;
ll propagation[MAX_N][MAX_N];
ll mainLength;
int N = 10;// num of node
int highestHashrateNode = 0;  // 最高ハッシュレートのノードID

bool chooseMainchain(block* block1, block* block2, int from, int to, int tie);
void mainChain(block* block1, int tie);
void simulation(int tie);
void reset();
ll prop(int i, int j);
double calculateDifficulty(block* latestBlock, int nodeId);  // ノード固有の難易度計算関数


std::random_device seed_gen;
std::mt19937_64 engine(10);// 1, 5, 10, 100
std::uniform_real_distribution<double> dist1(0., 1.0);
std::exponential_distribution<double> dist2(1);
std::normal_distribution<double> dist3(0.0, 1.0);

int main(void) {
    cout << "akira" << endl;
 
    hashrate[0] = N - 1;
    for (int i = 1;i < N;i++) {
        hashrate[i] = 1;
    }


    for (int i = 0;i < N;i++) {
        totalHashrate += hashrate[i];
        cout << "hashrate" << i << ": " << hashrate[i] << endl;
    }

    for (int i = 0;i < N;i++) {
        for (int j = 0;j < N;j++) {
            prop(i, j);
        }
    }

    simulation(0);

    cout << "block propagation time: " << delay << endl;


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



ll prop(int i, int j) {
    if (i == j) return 0;
    else return delay;
}

// ノード固有の難易度計算関数の実装
double calculateDifficulty(block* latestBlock, int nodeId) {
    if (latestBlock == nullptr || latestBlock->height == 0) {
        return 1.0; // ジェネシスブロックまたはnullptrの場合は初期難易度
    }
    
    // 2016ブロックごとに調整をチェック
    if (latestBlock->height % DIFFICULTY_ADJUSTMENT_INTERVAL != 0) {
        return latestBlock->difficulty; // 調整タイミングでない場合は現在の難易度を維持
    }
    
    // 初回調整の場合（height < 2016の場合）
    if (latestBlock->height < DIFFICULTY_ADJUSTMENT_INTERVAL) {
        return latestBlock->difficulty; // 十分なブロック履歴がない場合は現在の難易度を維持
    }
    
    // lastEpochTimeを使用して効率的に前回調整時刻を取得
    ll lastEpochTime = latestBlock->lastEpochTime;
    ll actualTimespan = latestBlock->time - lastEpochTime;
    double ratio = (double)actualTimespan / (double)TARGET_TIMESPAN;
    
    cout << "=== Difficulty Adjustment (Node " << nodeId << ") ===" << endl;
    cout << "Block height: " << latestBlock->height << endl;
    cout << "Last epoch time: " << lastEpochTime << " ms" << endl;
    cout << "Current time: " << latestBlock->time << " ms" << endl;
    cout << "Actual timespan: " << actualTimespan << " ms" << endl;
    cout << "Target timespan: " << TARGET_TIMESPAN << " ms" << endl;
    cout << "Ratio (T): " << ratio << endl;
    cout << "Current difficulty: " << latestBlock->difficulty << endl;
    
    double newDifficulty;
    
    if (ratio < 0.25) {
        // ブロック生成が早すぎる → 難易度を4倍にする
        newDifficulty = latestBlock->difficulty * 4.0;
        cout << "Too fast! Difficulty increased by 4x" << endl;
    } else if (ratio > 4.0) {
        // ブロック生成が遅すぎる → 難易度を1/4にする
        newDifficulty = latestBlock->difficulty * 0.25;
        cout << "Too slow! Difficulty decreased by 4x" << endl;
    } else {
        // 比例調整: 新しい難易度 = 現在の難易度 * ratio
        newDifficulty = latestBlock->difficulty / ratio;
        cout << "Proportional adjustment" << endl;
    }
    
    cout << "New difficulty: " << newDifficulty << endl;
    cout << "=================================================" << endl;
    
    return newDifficulty;
}

void mainChain(block* block1, int tie) {
    if (block1->height != endRound) {
        ll height = block1->height;
        block* curBlock = block1;
        while (curBlock->height > 0 && curBlock->height != height - 100) { // 100 block finalization
            curBlock = curBlock->prevBlock;
            if (curBlock == nullptr) cout << "sugeeeee" << endl;
        }
        if(curBlock->height > 0) numMain[tie][curBlock->minter]++;
        mainLength = max(mainLength, curBlock->height);
        return;
    } else {
        block* curBlock = block1;
        while (curBlock->height > mainLength) {
            numMain[tie][curBlock->minter]++;
            curBlock = curBlock->prevBlock;
        }
    }
}

void reset() {
    currentRound = 0;
    currentTime = 0;
    mainLength = 0;
    for (int i = 0;i < N;i++) {
        currentBlock[i] = nullptr;
    }

    return;
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

    std::queue<block*> blockStore;
    std::queue<task*> taskStore;

    ll lastPlotTime = 0;
    ll plotInterval = (endRound / 100) * TARGET_BLOCK_TIME;
    if (plotInterval == 0) plotInterval = TARGET_BLOCK_TIME;

    // CSVファイル用の出力ストリームを作成
    ofstream csvFile("plot_data.csv");
    csvFile << "Time,Proportion" << endl;

    block* genesisBlock = new block;
    blockQue.push(genesisBlock);
    genesisBlock->prevBlock = nullptr;
    genesisBlock->height = 0;
    genesisBlock->minter = -1;
    genesisBlock->difficulty = 1.0;  // ジェネシスブロックの初期難易度設定
    genesisBlock->lastEpochTime = 0;  // ジェネシスブロックの初期時刻

    for (int i = 0;i < N;i++) {
        currentBlock[i] = genesisBlock;

        task* nextBlockTask = new task;
        // 初期難易度を考慮したマイニング時間の計算
        double initialDifficulty = 1.0;
        nextBlockTask->time = (ll) (dist2(engine) * generationTime * totalHashrate / hashrate[i] * initialDifficulty);
        nextBlockTask->flag = 0;
        nextBlockTask->minter = i;
        taskQue.push(nextBlockTask);
        currentMiningTask[i] = nextBlockTask;
    }

    while(taskQue.size() > 0 && currentRound < endRound) {
        task* currentTask = taskQue.top();
        taskQue.pop();
        currentTime = currentTask->time;

        if (currentTime > lastPlotTime + plotInterval) {
            lastPlotTime = currentTime;

            block* mainChainTip = nullptr;
            for (int i = 0; i < N; i++) {
                if (currentBlock[i] != nullptr) {
                    if (mainChainTip == nullptr || currentBlock[i]->height > mainChainTip->height) {
                        mainChainTip = currentBlock[i];
                    }
                }
            }

            if (mainChainTip != nullptr && mainChainTip->height > 0) {
                ll highHashrateBlocks = 0;
                ll totalBlocksInChain = mainChainTip->height;

                block* current = mainChainTip;
                while (current != nullptr && current->height > 0) {
                    if (current->minter == highestHashrateNode) {
                        highHashrateBlocks++;
                    }
                    current = current->prevBlock;
                }

                double proportion = (double)highHashrateBlocks / totalBlocksInChain;
                // 標準出力には詳細情報を出力（デバッグ用）
                cout << "Time: " << currentTime << ", HighHashrateBlocks: " << highHashrateBlocks 
                     << ", TotalBlocks: " << totalBlocksInChain << ", Proportion: " << fixed << setprecision(5) << proportion << endl;
                // CSVファイルには時間と割合のみを出力
                csvFile << currentTime << "," << fixed << setprecision(5) << proportion << endl;
            }
        }

        if (currentTask->flag == 0) { //block generation
            int minter = currentTask->minter;
            if (currentMiningTask[minter] != currentTask) continue;
            block* newBlock;
            if (blockStore.size() > 0) {
                newBlock = blockStore.front();blockStore.pop();
            } else {
                newBlock = new block;
            }
            newBlock->prevBlock = currentBlock[minter];
            newBlock->height = currentBlock[minter]->height + 1;
            newBlock->minter = minter;
            newBlock->time = currentTime;
            newBlock->rand = dist1(engine) * (LLONG_MAX - 10);
            
            // このノードのローカルな難易度を計算
            double localDifficulty = calculateDifficulty(currentBlock[minter], minter);
            newBlock->difficulty = localDifficulty;
            
            // lastEpochTimeの設定
            if (newBlock->height % DIFFICULTY_ADJUSTMENT_INTERVAL == 0 && newBlock->height > 0) {
                // 難易度調整タイミングの場合、前回の調整時刻を設定
                newBlock->lastEpochTime = currentBlock[minter]->lastEpochTime;
            } else {
                // 通常のブロックの場合、親ブロックのlastEpochTimeを継承
                if (newBlock->height == DIFFICULTY_ADJUSTMENT_INTERVAL) {
                    // 初回の難易度調整の場合
                    newBlock->lastEpochTime = 0; // ジェネシスブロック時刻
                } else if (newBlock->height > DIFFICULTY_ADJUSTMENT_INTERVAL && 
                          (currentBlock[minter]->height % DIFFICULTY_ADJUSTMENT_INTERVAL == 0)) {
                    // 親が調整ブロックだった場合、その時刻を記録
                    newBlock->lastEpochTime = currentBlock[minter]->time;
                } else {
                    // 通常の場合、親のlastEpochTimeを継承
                    newBlock->lastEpochTime = currentBlock[minter]->lastEpochTime;
                }
            }
            
            currentBlock[minter] = newBlock;

            blockQue.push(newBlock);
            if (blockQue.size() > 10000) { // dont need to record 10000 blocks ago
                block* deleteBlock = blockQue.front();blockQue.pop();
                blockStore.push(deleteBlock);
            }

            task* nextBlockTask;
            if (taskStore.size() > 0) {
                nextBlockTask = taskStore.front();taskStore.pop();
            } else {
                nextBlockTask = new task;
            }
            // 次のマイニング時間を計算（現在のノードの難易度に基づく）
            double nextDifficulty = calculateDifficulty(newBlock, minter);
            nextBlockTask->time = currentTime + (ll) (dist2(engine) * generationTime * totalHashrate / hashrate[minter] * nextDifficulty);
            nextBlockTask->flag = 0;
            nextBlockTask->minter = minter;
            taskQue.push(nextBlockTask);
            currentMiningTask[minter] = nextBlockTask;

            for (int i = 0;i < N;i++) { // propagation task
                task* nextPropTask;
                if (taskStore.size() > 0) {
                    nextPropTask = taskStore.front();taskStore.pop();
                } else {
                    nextPropTask = new task;
                }
                nextPropTask->time = currentTime + prop(minter, i);
                nextPropTask->flag = 1;
                nextPropTask->to = i;
                nextPropTask->from = minter;
                nextPropTask->propagatedBlock = newBlock;
                taskQue.push(nextPropTask);
            }

            if(currentRound < newBlock->height) {
                currentRound = newBlock->height;
            } else { // fork
                
            }
            // cout << "blockgeneration, current time: "  << currentTime << ", minter"<< newBlock->minter << ", block height: " << newBlock->height << ", difficulty: " << newBlock->difficulty << endl;
        } else { // propagation
            // cout << "block propagation, current time: " << currentTime << ", from: " << currentTask->from << ", to: " << currentTask->to << ", height: " << currentTask->propagatedBlock->height << endl;
            int to = currentTask->to;
            int from = currentTask->from;
            bool mainchainChanged = chooseMainchain(currentTask->propagatedBlock, currentBlock[to], from, to, tie);
            
            // メインチェーンが変更された場合、新しい難易度に基づいてマイニングを再開
            if (mainchainChanged) {
                // 現在のマイニングタスクを無効化（次回の実行時にスキップされる）
                currentMiningTask[to] = nullptr;
                
                // 新しいメインチェーンの最新ブロックに記録されている難易度を使用
                double newDifficulty = currentBlock[to]->difficulty;
                
                // 新しいマイニングタスクを作成
                task* newMiningTask;
                if (taskStore.size() > 0) {
                    newMiningTask = taskStore.front();
                    taskStore.pop();
                } else {
                    newMiningTask = new task;
                }
                
                // 新しい難易度でマイニング時間を計算
                newMiningTask->time = currentTime + (ll) (dist2(engine) * generationTime * totalHashrate / hashrate[to] * newDifficulty);
                newMiningTask->flag = 0;
                newMiningTask->minter = to;
                taskQue.push(newMiningTask);
                currentMiningTask[to] = newMiningTask;
                
                // cout << "Mainchain changed for node " << to << ", restarting mining with difficulty: " << newDifficulty << endl;
            }
        }

        taskStore.push(currentTask);
    }
    
    // CSVファイルをクローズ
    csvFile.close();
}