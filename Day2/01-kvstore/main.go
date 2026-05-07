package main

import (
	"bufio"
	"fmt"
	"log"
	"net"
	"strings"
	"sync"
)

// KVStore: Key-Valueを保持するシンプルな構造体
// map[string]string = Goの組み込みハッシュテーブル
type KVStore struct {
	mu   sync.Mutex // 追加 同時アクセスを防ぐ鍵
	data map[string]string
}

// NewKVStore: KVStoreを初期化して返す
// mapはnilで初期化されるので、make()が必要
func NewKVStore() *KVStore {
	return &KVStore{
		data: make(map[string]string),
	}
}

// Set: キーに値を格納する
func (kv *KVStore) Set(key, value string) {
	//kv.mu.Lock()         //鍵をかける。
	//defer kv.mu.Unlock() // 関数が終わる時にかけた鍵を解除する これがないと、デッドロックが起きる。
	kv.data[key] = value
}

// Get: キーに対応する値を返す
// Goのmap: 存在しないキーは ("", false) を返す
func (kv *KVStore) Get(key string) (string, bool) {
	//kv.mu.Lock()         //鍵をかける。
	//defer kv.mu.Unlock() // 関数が終わる時にかけた鍵を解除する これがないと、デッドロックが起きる。
	value, exists := kv.data[key]
	return value, exists
}

// Delete: キーを削除する
func (kv *KVStore) Delete(key string) {
	delete(kv.data, key)
}

// Incr: 読み→加算→書きを1つのロックで包む
func (kv *KVStore) Incr(key string) int {
	kv.mu.Lock()
	defer kv.mu.Unlock()

	// ロックの中で読んで書くので、誰も割り込めない
	val, exists := kv.data[key]
	if !exists {
		val = "0"
	}
	var n int
	fmt.Sscanf(val, "%d", &n)
	n++
	kv.data[key] = fmt.Sprintf("%d", n)
	return n
}

func main() {
	store := NewKVStore()

	listener, err := net.Listen("tcp", ":6379") // Redisと同じポート番号
	if err != nil {
		log.Fatal(err)
	}
	defer listener.Close()
	fmt.Println("KVStore起動 :6379")

	for {
		conn, err := listener.Accept()
		if err != nil {
			continue
		}
		go handleConn(conn, store)
	}
}

func handleConn(conn net.Conn, store *KVStore) {
	defer conn.Close()
	reader := bufio.NewReader(conn)

	for {
		// 1行読む（改行区切り）
		line, err := reader.ReadString('\n')
		if err != nil {
			return
		}
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		// スペースで分割してコマンドを解析
		parts := strings.Fields(line)
		if len(parts) == 0 {
			continue
		}

		// コマンドを大文字に正規化（set → SET）
		cmd := strings.ToUpper(parts[0])

		switch cmd {
		case "SET":
			if len(parts) != 3 {
				conn.Write([]byte("ERR wrong number of args\n"))
				continue
			}
			store.Set(parts[1], parts[2])
			conn.Write([]byte("OK\n"))

		case "GET":
			if len(parts) != 2 {
				conn.Write([]byte("ERR wrong number of args\n"))
				continue
			}
			value, exists := store.Get(parts[1])
			if !exists {
				conn.Write([]byte("(nil)\n"))
			} else {
				conn.Write([]byte(value + "\n"))
			}

		case "DEL":
			if len(parts) != 2 {
				conn.Write([]byte("ERR wrong number of args\n"))
				continue
			}
			store.Delete(parts[1])
			conn.Write([]byte("OK\n"))

		case "INCR":
			if len(parts) != 2 {
				conn.Write([]byte("ERR wrong number of args\n"))
				continue
			}
			n := store.Incr(parts[1]) // 1行で完結、内部でアトミック
			conn.Write([]byte(fmt.Sprintf("%d\n", n)))

		default:
			conn.Write([]byte("ERR unknown command\n"))
		}
	}
}
