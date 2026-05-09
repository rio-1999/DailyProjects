import socket
import threading

# ── WSGI仕様に従ったサーバー本体 ──
class WSGIServer:
    def __init__(self, host='', port=8080):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen(5)
        self.app = None  # WSGIアプリ（Flaskなど）をここに入れる
        print(f'WSGIサーバー起動 :{port}')

    def set_app(self, app):
        """Flaskアプリを登録する（gunicorn app:app の app に相当）"""
        self.app = app

    def serve_forever(self):
        while True:
            conn, addr = self.sock.accept()
            t = threading.Thread(target=self.handle, args=(conn,))
            t.daemon = True
            t.start()

    def handle(self, conn):
        with conn:
            # ── Step1: HTTPリクエストを読む（server.pyと同じ） ──
            data = b''
            while True:
                chunk = conn.recv(1024)
                data += chunk
                if b'\r\n\r\n' in data:
                    break

            # ── Step2: environを組み立てる（WSGIの核心） ──
            # GunicornはここでHTTPをパースしてenvironに詰める
            environ = self.build_environ(data)

            # ── Step3: WSGIアプリ（Flask）を呼び出す ──
            response_started = {}

            def start_response(status, headers):
                """FlaskがステータスとヘッダーをこのコールバックでWSGIサーバーに渡す"""
                response_started['status'] = status
                response_started['headers'] = headers

            # ここがGunicornがFlaskを呼ぶ瞬間
            body_iter = self.app(environ, start_response)
            body = b''.join(body_iter)

            # ── Step4: HTTPレスポンスを組み立てて返す ──
            status = response_started.get('status', '200 OK')
            headers = response_started.get('headers', [])

            response_lines = [f'HTTP/1.1 {status}\r\n']
            for key, value in headers:
                response_lines.append(f'{key}: {value}\r\n')
            response_lines.append(f'Content-Length: {len(body)}\r\n')
            response_lines.append('\r\n')

            response = ''.join(response_lines).encode() + body
            conn.sendall(response)

    def build_environ(self, raw_request):
        """HTTPリクエストをWSGI仕様のenviron辞書に変換する"""
        lines = raw_request.decode('utf-8', errors='replace').split('\r\n')
        request_line = lines[0]  # 'GET /hello HTTP/1.1'
        parts = request_line.split(' ')

        method = parts[0] if len(parts) > 0 else 'GET'
        path = parts[1] if len(parts) > 1 else '/'

        # クエリ文字列を分離（/search?q=python → path=/search, query=q=python）
        query_string = ''
        if '?' in path:
            path, query_string = path.split('?', 1)

        # WSGIが要求するenvironのキー（PEP3333で定義されている）
        environ = {
            'REQUEST_METHOD': method,
            'PATH_INFO': path,
            'QUERY_STRING': query_string,
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '8080',
            'wsgi.input': b'',         # リクエストボディ（今回は省略）
            'wsgi.errors': None,
            'wsgi.multithread': True,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
            'wsgi.url_scheme': 'http',
        }

        # ヘッダーをenvironに追加（HTTP_で始まるキーに変換）
        for line in lines[1:]:
            if ': ' in line:
                key, value = line.split(': ', 1)
                # 'Content-Type' → 'HTTP_CONTENT_TYPE'（WSGIの規則）
                environ_key = 'HTTP_' + key.upper().replace('-', '_')
                environ[environ_key] = value

        return environ


# ── WSGIアプリを自前で書く（Flaskなしで動作確認） ──
def my_app(environ, start_response):
    """これがWSGIアプリの最小形。Flaskはこの形を満たした巨大版。"""
    path = environ['PATH_INFO']

    if path == '/hello':
        body = b'Hello from my WSGI app!'
        status = '200 OK'
    elif path == '/environ':
        # environの中身を全部返す（デバッグ用）
        body = '\n'.join(f'{k}: {v}' for k, v in environ.items()).encode()
        status = '200 OK'
    else:
        body = b'404 Not Found'
        status = '404 Not Found'

    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)
    return [body]


if __name__ == '__main__':
    from flask import Flask, request, jsonify

    # 本物のFlaskアプリ
    flask_app = Flask(__name__)

    @flask_app.route('/hello')
    def hello():
        return 'Hello from Flask on my WSGI server!'

    @flask_app.route('/echo')
    def echo():
        # クエリパラメータを受け取って返す
        name = request.args.get('name', 'unknown')
        return jsonify({'name': name, 'server': 'my-wsgi'})

    server = WSGIServer(port=8080)
    server.set_app(flask_app)  # my_appの代わりにFlaskを渡す
    server.serve_forever()