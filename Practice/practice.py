import struct

# struct.pack で 「数字 → バイト列」 に変換できる
# "!HH" の意味:
#   ! = ネットワークバイトオーダー(ビッグエンディアン)
#   H = unsigned short (2バイト整数)
# つまり「2バイト整数を2つ並べる」という意味

packet = struct.pack("!HH", 19034, 0x0100)
print(packet)         # バイト列として表示
print(packet.hex())   # 16進数で表示(人間に読みやすい)
print(len(packet))    # 何バイトか