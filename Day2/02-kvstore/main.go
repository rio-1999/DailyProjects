package main

import (
	"bufio"
	"fmt"
	"log"
	"net"
	"os"
	"strings"
	"sync"
)

type KVStore struct {
	mu      sync.Mutex
	data    map[string]string
	logFile *os.File // 追記用ファイル
}

func NewKVStore(path string) *KVStore {
	kv := &KVStore{
		data: make(map[string]string),
	}

	// 既存のログファイルがあれば再生して状態を復元
	kv.replay(path)

	// 追記モードでファイルを開く（なければ作る）
	f, err := os.OpenFile(path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Fatal(err)
	}
	kv.logFile = f
	return kv
}

// replay: ログファイルを1行ずつ読んでメモリに再適用する
func (kv *KVStore) replay(path string) {
	f, err := os.Open(path)
	if err != nil {
		return // ファイルがなければ初回起動なので無視
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := scanner.Text()
		parts := strings.Fields(line)
		if len(parts) == 0 {
			continue
		}
		switch parts[0] {
		case "SET":
			kv.data[parts[1]] = parts[2]
		case "DEL":
			delete(kv.data, parts[1])
		}
	}
	fmt.Println("ログから状態を復元しました")
}

// appendLog: ファイルに1行追記する（内部用）
func (kv *KVStore) appendLog(line string) {
	fmt.Fprintln(kv.logFile, line)
}

func (kv *KVStore) Set(key, value string) {
	kv.mu.Lock()
	defer kv.mu.Unlock()
	kv.data[key] = value
	kv.appendLog(fmt.Sprintf("SET %s %s", key, value)) // 書く前にログ
}

func (kv *KVStore) Get(key string) (string, bool) {
	kv.mu.Lock()
	defer kv.mu.Unlock()
	value, exists := kv.data[key]
	return value, exists
}

func (kv *KVStore) Delete(key string) {
	kv.mu.Lock()
	defer kv.mu.Unlock()
	delete(kv.data, key)
	kv.appendLog(fmt.Sprintf("DEL %s", key))
}

func (kv *KVStore) Incr(key string) int {
	kv.mu.Lock()
	defer kv.mu.Unlock()
	val, exists := kv.data[key]
	if !exists {
		val = "0"
	}
	var n int
	fmt.Sscanf(val, "%d", &n)
	n++
	kv.data[key] = fmt.Sprintf("%d", n)
	kv.appendLog(fmt.Sprintf("SET %s %d", key, n))
	return n
}

func main() {
	store := NewKVStore("kv.log") // ログファイル名

	listener, err := net.Listen("tcp", ":6379")
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
		line, err := reader.ReadString('\n')
		if err != nil {
			return
		}
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		parts := strings.Fields(line)
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
			n := store.Incr(parts[1])
			conn.Write([]byte(fmt.Sprintf("%d\n", n)))

		default:
			conn.Write([]byte("ERR unknown command\n"))
		}
	}
}
