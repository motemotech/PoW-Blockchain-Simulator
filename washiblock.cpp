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
ll delay = 600000; // 6000, 60000, 300000 ブロックの伝搬遅延
ll generationTime = 600000;
block* currentBlock[MAX_N];
task* currentMiningTask[MAX_N];
ll hashrate[MAX_N];
ll totalHashrate;
ll numMain[3][MAX_N];
ll endRound = 1000000;
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
    cout << "latestBlock->time: " << latestBlock->time << endl;
    cout << "latestBlock->lastEpochTime: " << latestBlock->lastEpochTime << endl;
    ll actualTimespan = latestBlock->time - latestBlock->lastEpochTime;
    cout << "actualTimespan: " << actualTimespan << endl;
    // 2016ブロック分の目標時間と実際にかかった時間の比率を計算
    double ratio = (double)TARGET_TIMESPAN / (double)actualTimespan;
    cout << "ratio: " << ratio << endl;
    // 難易度の急激な変動を防ぐため、調整率を制限 (0.25 ~ 4.0)
    if (ratio > 4.0) ratio = 4.0;
    if (ratio < 0.25) ratio = 0.25;

    double newDifficulty = latestBlock->difficulty * ratio;
    
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

    // メモリ再利用ロジックを無効化
    // std::queue<block*> blockStore;
    // std::queue<task*> taskStore;

    ll lastPlotTime = 0;
    ll plotInterval = (endRound / 100) * TARGET_BLOCK_TIME;
    if (plotInterval == 0) plotInterval = TARGET_BLOCK_TIME;

    // CSVファイル用の出力ストリームを作成
    ofstream csvFile("plot_data.csv");
    csvFile << "BlockTime,Miner0Proportion,Difficulty" << endl;

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
        double baseTime = (double)generationTime * (double)totalHashrate / (double)hashrate[i];
        double adjustedTime = baseTime * initialDifficulty;
        
        ll miningTime = (ll)(dist2(engine) * adjustedTime);
        nextBlockTask->time = miningTime;
        nextBlockTask->flag = 0;
        nextBlockTask->minter = i;
        taskQue.push(nextBlockTask);
        currentMiningTask[i] = nextBlockTask;
    }

    while(taskQue.size() > 0 && currentRound < endRound) {
        task* currentTask = taskQue.top();
        taskQue.pop();
        currentTime = currentTask->time;

        

        if (currentTask->flag == 0) { //block generation
            int minter = currentTask->minter;
            if (currentMiningTask[minter] != currentTask) {
                continue;
            }
            
            block* newBlock = new block;
            
            block* parent = currentBlock[minter];
            newBlock->prevBlock = parent;
            newBlock->height = parent->height + 1;
            newBlock->minter = minter;
            newBlock->time = currentTime;
            newBlock->rand = dist1(engine) * (LLONG_MAX - 10);

            // 親ブロックに基づいて次の難易度を計算
            newBlock->difficulty = calculateDifficulty(parent, minter);
            cout << "newBlock->difficulty: " << newBlock->difficulty << endl;

            // lastEpochTimeの更新
            newBlock->lastEpochTime = parent->lastEpochTime;
            if (newBlock->height % DIFFICULTY_ADJUSTMENT_INTERVAL == 1) {
                // 調整ブロックの場合、次の期間の開始時刻として現在の時刻を記録
                newBlock->lastEpochTime = currentBlock[minter]->time;
            }
            
            currentBlock[minter] = newBlock;

            // --- プロットロジックここから ---
            if (minter == highestHashrateNode) {
                // ネットワーク全体の最も長いチェーンを見つける
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
                    csvFile << newBlock->height << "," << newBlock->time << "," << fixed << setprecision(5) << proportion << "," << newBlock->difficulty << endl;
                }
            }
            // --- プロットロジックここまで ---

            blockQue.push(newBlock);
            // メモリ再利用ロジックは無効化

            task* nextBlockTask = new task;
            
            // 次のマイニング時間を計算（現在のノードの難易度に基づく）
            double nextDifficulty = calculateDifficulty(newBlock, minter);
            // マイニング時間の計算を安全に行い、オーバーフローを防ぐ
            double baseTime = (double)generationTime * (double)totalHashrate / (double)hashrate[minter];
            double adjustedTime = baseTime * nextDifficulty;
            
            double randomFactor = dist2(engine);
            ll miningTime = (ll)(randomFactor * adjustedTime);
            nextBlockTask->time = currentTime + miningTime;
            
            nextBlockTask->flag = 0;
            nextBlockTask->minter = minter;
            taskQue.push(nextBlockTask);
            currentMiningTask[minter] = nextBlockTask;

            for (int i = 0;i < N;i++) { // propagation task
                task* nextPropTask = new task;
                nextPropTask->time = currentTime + prop(minter, i);
                nextPropTask->flag = 1;
                nextPropTask->to = i;
                nextPropTask->from = minter;
                nextPropTask->propagatedBlock = newBlock;
                taskQue.push(nextPropTask);
            }

            if(currentRound < newBlock->height) {
                currentRound = newBlock->height;
                // cout << "blockgeneration, miner: " << minter << ", height: " << newBlock->height << ", difficulty: " << newBlock->difficulty << endl;
            }

        } else { // propagation
            int to = currentTask->to;
            int from = currentTask->from;
            bool mainchainChanged = chooseMainchain(currentTask->propagatedBlock, currentBlock[to], from, to, tie);
            
            if (mainchainChanged) {
                // 新しいメインチェーンの先端ブロックに基づいて、次のマイニングの難易度を計算
                double latestDifficulty = calculateDifficulty(currentBlock[to], to);
                
                task* newMiningTask = new task;
                
                double baseTime = (double)generationTime * (double)totalHashrate / (double)hashrate[to];
                double adjustedTime = baseTime * latestDifficulty;
                
                double randomFactor = dist2(engine);
                ll miningTime = (ll)(randomFactor * adjustedTime);
                newMiningTask->time = currentTime + miningTime;
                newMiningTask->flag = 0;
                newMiningTask->minter = to;
                taskQue.push(newMiningTask);
                currentMiningTask[to] = newMiningTask;
            }
        }
        // メモリリークするが、安全のためオブジェクトは解放しない
        // delete currentTask;
    }

    if (taskQue.empty()) {
        cout << "--- Simulation stopped: Task queue is empty. ---" << endl;
    } else {
        cout << "--- Simulation finished normally. ---" << endl;
    }
    cout << "Final block height: " << currentRound << endl;
    cout << "Current time: " << currentTime << " ms" << endl;
    
    csvFile.close();
}
