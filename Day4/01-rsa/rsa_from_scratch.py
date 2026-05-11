
# RSAに必要な数学のパーツを作る

def gcd(a, b):
    """
    最大公約数(Greatest Common Divisor)をユークリッドの互除法で求める。
    なぜ必要? → RSAでは「e と φ(n) が互いに素」という条件を確認するため。
    """
    while b:
        a, b = b, a % b  # a を b で割った余りで置き換えていくと、いずれ b=0 になる
    return a


def extended_gcd(a, b):
    """
    拡張ユークリッドの互除法。
    ax + by = gcd(a, b) となる x, y を求める。
    なぜ必要? → 秘密鍵 d を求めるため。d は e のモジュラ逆数で、これを求めるのに使う。
    """
    if b == 0:
        return a, 1, 0
    g, x1, y1 = extended_gcd(b, a % b)
    # 再帰の戻り値から、現在のステップでの x, y を逆算する
    x = y1
    y = x1 - (a // b) * y1
    return g, x, y


def modinv(a, m):
    """
    a の m を法とする逆元(モジュラ逆数)を求める。
    つまり (a * x) % m == 1 となる x を返す。
    なぜ必要? → 秘密鍵 d は e の逆元: (e * d) % φ(n) == 1
    """
    g, x, _ = extended_gcd(a, m)
    if g != 1:
        raise Exception("逆元が存在しない(a と m が互いに素ではない)")
    return x % m  # 負の数になるかもしれないので m で正の範囲に戻す


# 鍵を生成する

def generate_keys():
    """
    RSAの鍵ペアを生成する。
    小さな素数を使う。
    """
    # ★ ここがRSAの安全性の根拠:
    #   「大きな2つの素数 p, q を掛け合わせた n から、p, q を逆算するのは
    #    現実的な時間では不可能」という事実。
    #   小さな数だと簡単に因数分解できてしまうので、本番では巨大な素数を使う。
    p = 1009
    q = 9973

    # n は公開する。これが「公開鍵の一部」。
    n = p * q  # 3233

    # φ(n) = オイラーのトーシェント関数。
    # 「n 未満で n と互いに素な自然数の個数」。
    # p, q が素数のときは (p-1)(q-1) になる(これは数学的に証明されている)。
    # ★ φ(n) は秘密にしないといけない。これがバレると秘密鍵が逆算できる。
    phi = (p - 1) * (q - 1)  # 3120

    # e は公開鍵指数。φ(n) と互いに素ならなんでもいい。
    # 慣習的に 65537 (= 2^16 + 1) がよく使われる。今回は手計算しやすい 17 にする。
    e = 17
    assert gcd(e, phi) == 1, "e と φ(n) は互いに素でなければならない"

    # d は秘密鍵指数。e のモジュラ逆数。
    # (e * d) % phi == 1 となる d。
    d = modinv(e, phi)

    # 公開鍵: (e, n)  ← これは全世界に公開してOK
    # 秘密鍵: (d, n)  ← これは絶対に漏らしてはいけない
    return (e, n), (d, n)


public_key, private_key = generate_keys()
print(f"公開鍵 (e, n): {public_key}")
print(f"秘密鍵 (d, n): {private_key}")

# 暗号化と復号

def encrypt(message, public_key):
    """
    暗号化: cipher = (message ^ e) mod n
    """
    e, n = public_key
    # pow(base, exp, mod) は (base ** exp) % mod を効率的に計算する組み込み関数。
    # 普通に ** で計算すると巨大な数になってメモリが死ぬので、必ず pow を使う。
    return pow(message, e, n)


def decrypt(cipher, private_key):
    """
    復号: message = (cipher ^ d) mod n
    """
    d, n = private_key
    return pow(cipher, d, n)


# 試してみる
message = 123  # まずは数値で。文字列は後でやる。
print(f"\n元のメッセージ: {message}")

cipher = encrypt(message, public_key)
print(f"暗号文: {cipher}")

decrypted = decrypt(cipher, private_key)
print(f"復号結果: {decrypted}")

assert message == decrypted, "復号失敗!"
print("✅ 暗号化と復号に成功!")

# 文字列の暗号化

def bytes_to_int(data: bytes) -> int:
    """
    バイト列を整数に変換する。
    例: b"hi" → 0x6869 → 26729
    """
    # 'big' はビッグエンディアン(先頭バイトが上位桁)
    return int.from_bytes(data, 'big')


def int_to_bytes(n: int) -> bytes:
    """
    整数をバイト列に戻す。
    """
    # 必要なバイト数を計算: ビット長を8で割って切り上げ
    length = (n.bit_length() + 7) // 8
    return n.to_bytes(length, 'big')


# 試す
message = b"hi"
m_int = bytes_to_int(message)
print(f"\n'hi' を整数に: {m_int}")  # 26729

cipher = encrypt(m_int, public_key)
print(f"暗号化: {cipher}")

decrypted_int = decrypt(cipher, private_key)
decrypted = int_to_bytes(decrypted_int)
print(f"復号: {decrypted}")  # b'hi'