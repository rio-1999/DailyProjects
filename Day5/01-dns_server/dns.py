import struct
import random

# --- DNSヘッダーを組み立てる ---

# ID: ランダムな2バイト整数
query_id = random.randint(0, 65535)

# FLAGS: 0x0100 = 「標準クエリ、再帰解決希望」
flags = 0x0100

# QDCOUNT: 1 (質問を1つ送る)
qdcount = 1

# ANCOUNT, NSCOUNT, ARCOUNT: クエリ時は全部0
ancount = 0
nscount = 0
arcount = 0

# !HHHHHH = ネットワークバイトオーダーで2バイト整数を6個並べる
header = struct.pack("!HHHHHH", query_id, flags, qdcount, ancount, nscount, arcount)

print(f"ヘッダーの長さ: {len(header)} バイト")
print(f"16進ダンプ:    {header.hex()}")
print(f"ID:            {query_id} (0x{query_id:04x})")


def encode_domain(domain: str) -> bytes:
    """
    "google.com" を b"\x06google\x03com\x00" に変換する
    """
    parts = domain.split(".")
    qname = b""

    for part in parts:
        length = len(part)
        qname += struct.pack("!B", length)
        qname += part.encode('ascii')

    return qname + struct.pack("!B", 0)


# テスト
print(encode_domain("google.com").hex())
# 期待される出力: 06676f6f676c6503636f6d00
#   06 = 長さ6
#   676f6f676c65 = "google" のASCII
#   03 = 長さ3
#   636f6d = "com" のASCII
#   00 = 終端

# --- 質問セクションを組み立てる ---

domain = "github.com"
qname = encode_domain(domain)

qtype = 1   # A レコード (IPv4)
qclass = 1  # IN (Internet)

# QTYPEとQCLASSをパックして、QNAMEの後ろに連結
question = qname + struct.pack("!HH", qtype, qclass)

print(f"質問セクションの長さ: {len(question)} バイト")
print(f"16進ダンプ:          {question.hex()}")

# --- ヘッダー + 質問 = DNSクエリパケット完成 ---
query_packet = header + question

print()
print(f"DNSクエリパケット全体の長さ: {len(query_packet)} バイト")
print(f"16進ダンプ:")
print(query_packet.hex())

import socket

# --- UDPソケットを作る ---
# AF_INET = IPv4
# SOCK_DGRAM = UDP (TCPは SOCK_STREAM)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# タイムアウトを設定(返事が来なかったら諦める)
sock.settimeout(5.0)

# --- 8.8.8.8 の 53番ポートに送る ---
# 8.8.8.8 = Google Public DNS
# 53     = DNSの標準ポート
dns_server = ("8.8.8.8", 53)

print(f"クエリ送信中... → {dns_server}")
sock.sendto(query_packet, dns_server)

# --- レスポンスを受け取る ---
# 4096バイトのバッファで受信(普通のDNSレスポンスは余裕で収まる)
response, addr = sock.recvfrom(4096)

print(f"レスポンス受信! 送信元: {addr}")
print(f"レスポンスの長さ: {len(response)} バイト")
print(f"16進ダンプ:")
print(response.hex())

sock.close()

def parse_header(response: bytes) -> dict:
    """
    最初の12バイトを読んで、ヘッダーの情報を辞書で返す
    """
    # !HHHHHH で6個の2バイト整数を取り出す
    # 戻り値: {"id": ..., "flags": ..., "qdcount": ..., "ancount": ..., ...}
    fields = struct.unpack("!HHHHHH", response[:12])

    header = {
        "id":      fields[0], # 識別子
        "flags":   fields[1], # フラグ（QR, Opcode, AA, TC, RD, RA, Z, RCODE）
        "qdcount": fields[2], # 質問数
        "ancount": fields[3], # 回答レコード数
        "nscount": fields[4], # 権威リソースレコード数
        "arcount": fields[5], # 追加リソースレコード数
    }
    
    return header


# テスト
header_info = parse_header(response)
print(header_info)
# 期待される出力例:
# {"id": 41280, "flags": 33152, "qdcount": 1, "ancount": 6, "nscount": 0, "arcount": 0}


def skip_question(response: bytes, offset: int) -> int:
    """
    response の offset 位置から質問セクションを読み飛ばして、
    その次のフィールドが始まる位置(=回答セクションの開始位置)を返す
    
    引数:
        response: DNSレスポンス全体
        offset: 質問セクションが始まる位置(普通は12)
    
    戻り値:
        質問セクションの後ろの位置(=回答セクションの開始位置)
    """
    # ヒント1: response[offset] を見て、それが \x00 でなければ offset を増やす
    #         \x00 が見つかったら、その位置を覚える
    # ヒント2: \x00 の後ろに4バイト (QTYPE + QCLASS) があることを忘れずに

    qtype = 2
    qclass = 2

    while response[offset] != 0:
        offset += 1
    return offset + 1 + qtype + qclass


# テスト
answer_start = skip_question(response, 12)
print(f"回答セクションの開始位置: {answer_start}")
# 期待される値: 28
# (なぜ28? ヘッダー12バイト + QNAME 12バイト + QTYPE 2バイト + QCLASS 2バイト = 28)

def parse_answer(response: bytes, offset: int) -> tuple[str, int]:
    # --- NAMEを読む ---
    if (response[offset] & 0xc0) == 0xc0:
        # 圧縮ポインタ → 2バイト
        offset += 2
    else:
        # 普通のラベル列 → \x00 まで読む
        while response[offset] != 0:
            offset += 1
        offset += 1  # \x00 自体もスキップ
    
    # --- TYPE, CLASS, TTL, RDLENGTH を読む(固定10バイト) ---
    type_, class_, ttl, rdlength = struct.unpack("!HHIH", response[offset:offset+10])
    offset += 10
    
    # --- RDATA を読む ---
    rdata = response[offset:offset+rdlength]
    print(rdata)
    if type_ == 1:
        ip = ".".join(str(b) for b in rdata)
    else:
        ip = f"Type:{type_} data"
    
    # --- 次の位置を返す ---
    return ip, offset+rdlength


# テスト
ip, next_offset = parse_answer(response, 28)
print(f"IP: {ip}")
print(f"次のレコード: {next_offset}")
# 期待される出力:
# IP: 142.250.23.139
# 次のレコード: 44

# --- 全部繋げてDNSレスポンスをパースする ---

header_info = parse_header(response)
print(f"=== ヘッダー ===")
print(f"ID: {header_info['id']}")
print(f"回答数: {header_info['ancount']}")
print()

# 質問セクションをスキップして、回答セクションの開始位置を得る
offset = skip_question(response, 12)
print(f"=== 回答セクション (offset={offset}から) ===")

# ANCOUNT 個の回答を順番にパース
ips = []
for i in range(header_info["ancount"]):
    ip, offset = parse_answer(response, offset)
    ips.append(ip)
    print(f"  {i+1}個目: {ip}  (次のoffset={offset})")

print()
print(f"=== 結果 ===")
print(f"{domain} の IPアドレス:")
for ip in ips:
    print(f"  - {ip}")