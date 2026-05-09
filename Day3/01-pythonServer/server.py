import socket
import threading

# ── Day1のGoと対比して読む ──
# net.Listen("tcp", ":8080") の Python版
def create_server(host='', port=8080):
    # AF_INET = IPv4, SOCK_STREAM = TCP（UDPならSOCK_DGRAM）
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # TIME_WAIT状態のポートを即再利用できるようにする
    # これがないと「Address already in use」エラーが出る
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    sock.bind((host, port))
    sock.listen(5)  # バックログ: 同時に待てる接続数
    return sock

def handle_connection(conn, addr):
    """1接続を担当する関数 ← GoのhandleConn相当"""
    with conn:
        # リクエスト読み取り（簡易版：空行まで）
        data = b''
        while True:
            chunk = conn.recv(1024)
            data += chunk
            if b'\r\n\r\n' in data:  # ヘッダー終端を検出
                break
        
        # パース：1行目だけ取り出す
        request_line = data.decode('utf-8', errors='replace').split('\r\n')[0]
        parts = request_line.split(' ')
        
        if len(parts) < 2:
            return
        
        method, path = parts[0], parts[1]
        print(f"[{threading.current_thread().name}] {method} {path}")
        
        # ルーティング（Day1と同じ構造）
        if path == '/hello':
            body = 'Hello from Python!'
        elif path == '/slow':
            # ★ Phase2でここが重要になる
            import time
            time.sleep(2)
            body = 'Slow response done'
        else:
            body = '404 Not Found'
        
        # HTTPレスポンス組み立て（\r\nに注意 ← Day1で学んだやつ）
        response = (
            f'HTTP/1.1 200 OK\r\n'
            f'Content-Type: text/plain\r\n'
            f'Content-Length: {len(body.encode())}\r\n'
            f'\r\n'
            f'{body}'
        )
        conn.sendall(response.encode())

def main():
    server = create_server()
    print('Python HTTPサーバー起動 :8080')
    
    while True:
        conn, addr = server.accept()
        # go handleConn(conn, store) の Python版
        t = threading.Thread(target=handle_connection, args=(conn, addr))
        t.daemon = True
        t.start()

if __name__ == '__main__':
    main()