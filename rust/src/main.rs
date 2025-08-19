enum TaskType {
    BLOCK_GENERATION = 0,
    PROPAGATION = 1,
}

struct Block {
    height: u64,
    prev_block: Option<Box<Block>>,
    minter: i32,
    time: u64,
    rand: u64,
    difficulty: f64,
    last_epoch_time: u64,
    finalized: bool,
}

impl Block {
    fn new() -> Self {
        Block {
            height: 0,
            prev_block: None,
            minter: -1,
            time: 0,
            rand: 0,
            difficulty: 1.0,
            last_epoch_time: 0,
            finalized: false,
        }
    }
}

struct Task {
    time: u64,
    flag: TaskType,
    minter: i32,
    from: i32,
    to: i32,
    propagated_block: Option<Box<Block>>,
}

const N: usize = 20;

fn main() {

   let mut hashrate: Vec<u64> = vec![0; N];
   let mut total_hashrate: u64 = 0;

   hashrate[0] = N as u64 - 1;
   for i in 1..N {
        hashrate[i] = 1;
   }

   for i in 0..N {
        total_hashrate += hashrate[i];
   }

   
}
