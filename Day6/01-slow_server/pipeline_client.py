# pipeline_client.py
# pipelining して 5 個のリクエストを一気に送るクライアント。
# HOL blocking を観測するのが目的。

import socket
import time

def main():
    # サーバーに TCP 接続
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 8080))

    # ★ 5 個のリクエストを「一気に」送る（=pipelining）
    # レスポンスを待たずに、5 個分の HTTP リクエストを連続で書き込む
    request = (
        "GET / HTTP/1.1\r\n"
        "Host: 127.0.0.1\r\n"
        "\r\n"
    )
    pipelined = request * 5  # 5 個分を連結

    start = time.time()  # 計測開始

    # sendall で 5 個分を一気に送信
    s.sendall(pipelined.encode())
    print(f"[{time.time() - start:.3f}s] 5 個のリクエストを送信完了")

    # レスポンスを受け取る。
    # サーバーが 5 個分のレスポンスを返してくるはずなので、
    # 接続が閉じるか、十分なデータが来るまで読み続ける。
    received = b""
    while True:
        chunk = s.recv(4096)
        
        if not chunk:
            break
        received += chunk
        elapsed = time.time() - start
        print(f"[{elapsed:.3f}s] {len(chunk)} バイト受信")

        # 5 個分のレスポンスが揃ったかを雑にチェック
        # "response to request #5" が含まれてたら全部届いたと判断
        if b"response to request #5" in received:
            print(f"[{elapsed:.3f}s] 5 個分のレスポンスが全部届いた")
            break

    total = time.time() - start
    print(f"\n総時間: {total:.3f}s")
    print(f"\n=== 受信内容 ===\n{received.decode()}")

    s.close()


if __name__ == "__main__":
    main()