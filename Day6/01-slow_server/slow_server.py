import socket
import threading
import time

def handle_client(conn, addr):
    """1つの TCP 接続を処理する関数。
    Keep-Alive で複数リクエストを受け付ける想定で、while ループで回す。
    """
    request_count = 0

    with conn:
        while True:
            # リクエストを読む。4096バイト
            # 本来は \r\n\r\n まで読むべき.
            data = conn.recv(4096)
            print(f"[{addr}] recv: {len(data)} バイト, 中身: {data!r}")  
            if not data:
                # クライアントが接続を閉じたら抜ける
                break

            request_count += 1
            print(f"[{addr}] request #{request_count} received")


            if request_count == 1:
                print(f"[{addr}] 重い処理を開始(2秒)...")
                time.sleep(2)
                print(f"[{addr}] 重い処理が終了")

            body = f"response to request #{request_count}\n"
            response = (
                "HTTP/1.1 200 OK\r\n"
                f"Content-Length: {len(body)}\r\n"
                "Connection: keep-alive\r\n"
                "\r\n"
                f"{body}"
            )
            conn.sendall(response.encode())

def main():
    # TCP ソケットを作る（Day 1 でやったやつ)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # SO_REUSEADDR: サーバーを止めて再起動するときに「Address already in use」を回避
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 8080))
    server.listen(5)
    print("Listening on http://127.0.0.1:8080")

    while True:
        # 新しい接続を受ける
        conn, addr = server.accept()
        # 別スレッドで処理（複数クライアント対応)
        t = threading.Thread(target=handle_client, args=(conn, addr))
        t.start()


if __name__ == "__main__":
    main()