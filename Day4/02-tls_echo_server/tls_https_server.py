# tls_https_server.py

import socket
import ssl

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="server.crt", keyfile="server.key")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("127.0.0.1", 8443))
sock.listen(5)

tls_sock = context.wrap_socket(sock, server_side=True)
print("https://127.0.0.1:8443 で待ち受け中")

while True:
    try:
        conn, addr = tls_sock.accept()
        # ブラウザからの HTTP リクエストを受け取る
        request = conn.recv(4096).decode('utf-8', errors='replace')
        print(f"\n--- 受信したリクエスト ---\n{request}\n--- ここまで ---")

        # HTTP レスポンスを手で組み立てる(Day 1 の応用)
        body = "<html><body><h1>TLS 動作確認</h1><p>これは暗号化されて送られています。</p></body></html>"
        response = (
            "HTTP/1.1 200 OK\r\n"
            f"Content-Length: {len(body.encode())}\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            "\r\n"
            f"{body}"
        )
        conn.sendall(response.encode())
        conn.close()
    except ssl.SSLError as e:
        print(f"TLS エラー: {e}")
    except KeyboardInterrupt:
        break

sock.close()