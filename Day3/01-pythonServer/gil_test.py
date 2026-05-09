import threading
import time
import multiprocessing

def cpu_heavy(n, label):
    """CPUをぶん回す処理（sleepしない）"""
    start = time.time()
    count = 0
    # 1億回ループ（純粋なCPU演算）
    while count < 100_000_000:
        count += 1
    elapsed = time.time() - start
    print(f'[{label}] 完了: {elapsed:.2f}秒')

if __name__ == '__main__':
    # ── 実験1: シングルスレッド（ベースライン）──
    print('=== 実験1: シングルスレッド（逐次実行）===')
    start = time.time()
    cpu_heavy(100_000_000, 'single-1')
    cpu_heavy(100_000_000, 'single-2')
    print(f'合計: {time.time() - start:.2f}秒\n')

    # ── 実験2: マルチスレッド ──
    # 「2スレッドで並列実行するから半分の時間になる」はずだが...
    print('=== 実験2: マルチスレッド ===')
    start = time.time()
    t1 = threading.Thread(target=cpu_heavy, args=(100_000_000, 'thread-1'))
    t2 = threading.Thread(target=cpu_heavy, args=(100_000_000, 'thread-2'))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print(f'合計: {time.time() - start:.2f}秒\n')

    # ── 実験3: マルチプロセス ──
    print('=== 実験3: マルチプロセス ===')
    start = time.time()
    p1 = multiprocessing.Process(target=cpu_heavy, args=(100_000_000, 'proc-1'))
    p2 = multiprocessing.Process(target=cpu_heavy, args=(100_000_000, 'proc-2'))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    print(f'合計: {time.time() - start:.2f}秒\n')