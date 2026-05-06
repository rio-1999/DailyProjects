package main

// importで複数のパッケージを読み込む
// Goの標準ライブラリだけでTCP通信が実装できる
import (
	"bufio"   // バッファ付きI/O
	"fmt"     // 標準出力
	"log"     // ログ出力（エラー時に使う）
	"net"     // ネットワーク通信
	"strings" // 文字列操作
)

func main() {
	// net.Listen: 指定したアドレスでTCP接続を待ち受ける
	// "tcp"      : プロトコル
	// ":8080"    : ポート番号（IPは省略するとlocalhostになる）
	listener, err := net.Listen("tcp", ":8080")

	// Goのエラーハンドリング：errがnilでなければエラー
	// log.Fatal: エラーを出力してプログラムを終了する
	if err != nil {
		log.Fatal("サーバー起動エラー:", err)
	}

	// defer: この関数が終了するときに実行される
	// listenerを確実にクローズするために使う
	defer listener.Close()
　
	fmt.Println("TCPサーバー起動 :8080")

	// 無限ループでクライアントの接続を待ち続ける
	for {
		// listener.Accept: クライアントからの接続を待つ（ブロッキング）
		// 接続が来るまでここで止まる
		conn, err := listener.Accept()
		if err != nil {
			log.Println("接続エラー:", err)
			continue // エラーでも次の接続を待つ
		}

		fmt.Println("クライアント接続:", conn.RemoteAddr())

		// goroutine: Goの軽量スレッド
		// goキーワードで関数を非同期で実行する
		// これにより複数のクライアントを同時に処理できる
		go handleConnection(conn)
	}
}

// handleConnection: 1つのクライアントとの通信を処理する関数
// net.Conn: TCPコネクションを表すインターフェース
func handleConnection(conn net.Conn) {
	// この関数が終わったらコネクションを閉じる
	defer conn.Close()

	// bufio.NewReader: コネクションをバッファ付きで読み込む
	// バッファとは：データを一時的に溜めておく領域
	// 1バイトずつ読むより効率的
	reader := bufio.NewReader(conn)

	for {
		// ReadString('\n'): 改行文字まで読み込む
		// クライアントがEnterを押すまで待つ
		message, err := reader.ReadString('\n')
		if err != nil {
			fmt.Println("クライアント切断:", conn.RemoteAddr())
			return
		}

		// strings.TrimSpace: 前後の空白・改行を除去する
		message = strings.TrimSpace(message)
		fmt.Printf("受信: %s\n", message)

		// exitと送ってきたら接続を切る
		if message == "exit" {
			conn.Write([]byte("bye\n"))
			return
		}

		// クライアントに同じメッセージを返す（エコー）
		// fmt.Sprintf: 文字列をフォーマットして返す（Printfと違い出力しない）
		response := fmt.Sprintf("echo: %s\n", message)

		// conn.Write: クライアントにデータを送信する
		// []byte(): 文字列をバイト列に変換（ネットワークはバイト列で通信する）
		conn.Write([]byte(response))
	}
}
