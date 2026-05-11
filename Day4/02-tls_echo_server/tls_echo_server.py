# tls_echo_server.py
# Day 1 の echo サーバーに TLS を被せたもの

import socket
import ssl

# ============================================================
# Step 1: SSLContext を作る
# ============================================================
# SSLContext = TLS の設定をまとめたオブジェクト。
# 「どのバージョンの TLS を使うか」「どの証明書を使うか」「どの暗号スイートを許可するか」
# などをここに集約する。
# 
# PROTOCOL_TLS_SERVER は「サーバー側の TLS 全般」を意味する。
# 内部で TLS 1.2 / 1.3 のネゴシエーションを自動でやってくれる。
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

# 証明書(server.crt)と秘密鍵(server.key)を読み込む。
# Part 2 で openssl で作ったやつ。
# サーバーは「証明書を提示する側」なので、これを設定する必要がある。
context.load_cert_chain(certfile="server.crt", keyfile="server.key")

# ============================================================
# Step 2: 普通の TCP ソケットを作る (Day 1 と同じ)
# ============================================================
# ここまでは平文の echo サーバーと完全に同じ。
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("127.0.0.1", 8443))  # HTTPS の慣習で 8443 を使う(443 は root 権限が必要)
sock.listen(5)

print("TLS echo server listening on https://127.0.0.1:8443")
print("(Ctrl+C で停止)")

# ============================================================
# Step 3: TLS でソケットをラップする
# ============================================================
# ここがミソ。普通のソケットを context.wrap_socket() でラップすると、
# 以降の send/recv が「自動的に暗号化・復号される」ソケットになる。
# 
# server_side=True は「自分はサーバー側」と明示するため。
# 
# wrap_socket() を呼んだだけではまだハンドシェイクは始まらない。
# accept() してクライアントが繋いできたタイミングで、
# Part 2 で見た ClientHello / ServerHello のやり取りが始まる。
tls_sock = context.wrap_socket(sock, server_side=True)

while True:
    try:
        # ★ accept() の中で TLS ハンドシェイクが完走する。
        #   ここでクライアントとサーバーが共通鍵を交換し終える。
        #   ハンドシェイクが失敗すると例外が飛ぶ(後述)。
        conn, addr = tls_sock.accept()
        print(f"\n[+] 接続あり: {addr}")
        
        # ハンドシェイク後の情報を表示してみる
        print(f"    使用プロトコル: {conn.version()}")  # 例: TLSv1.3
        print(f"    使用暗号スイート: {conn.cipher()}")  # 例: ('TLS_AES_256_GCM_SHA384', 'TLSv1.3', 256)
        
        # ここから先は Day 1 の echo サーバーと完全に同じコード。
        # send/recv は自動で暗号化されている。
        data = conn.recv(1024)
        print(f"    受信(復号後): {data!r}")
        conn.sendall(data)  # echo back
        conn.close()
        
    except ssl.SSLError as e:
        # TLS ハンドシェイク失敗時にここに来る。
        # 例: クライアントが平文で繋ごうとした、証明書を信頼しなかった、など。
        print(f"[!] TLS エラー: {e}")
    except KeyboardInterrupt:
        print("\nShutting down.")
        break

sock.close()