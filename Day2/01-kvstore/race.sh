#!/bin/bash
# 1000回並列でINCRを叩く
# 期待値: 1000
# 実際: ???

# counterをリセット
echo "SET counter 0" | nc localhost 6379

# 100並列 × 10回 = 1000回INCRを実行
for i in $(seq 1 100); do
    (
        for j in $(seq 1 10); do
            echo "INCR counter" | nc localhost 6379 > /dev/null
        done
    ) &
done

wait  # 全部終わるまで待つ

echo -n "最終値(期待値=1000): "
echo "GET counter" | nc localhost 6379