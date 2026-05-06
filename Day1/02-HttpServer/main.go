package main

import (
	"bufio"
	"fmt"
	"log"
	"net"
	"strings"
	"time"
)

func main() {
	listener, err := net.Listen("tcp", ":8080")
	if err != nil {
		log.Fatal("起動エラー:", err)
	}

	defer listener.Close()

	fmt.Println("HTTPサーバー起動 :8080")

	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Println("接続エラー:", err)
			continue
		}
		go handleConnection(conn)
	}
}

func handleConnection(conn net.Conn) {
	defer conn.Close()
	reader := bufio.NewReader(conn)

	var lines []string
	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			return
		}

		line = strings.TrimRight(line, "\r\n")
		if line == "" {
			break
		}
		lines = append(lines, line)
	}

	if len(lines) == 0 {
		return
	}

	parts := strings.Fields(lines[0])
	if len(parts) < 2 {
		return
	}

	method := parts[0]
	path := parts[1]

	fmt.Printf("受信: %s %s\n", method, path)

	var body string
	switch path {
	case "/hello":
		body = "Hello, World!"
	case "/time":
		body = time.Now().Format("2006-01-02 15:04:05")
	default:
		body = `404 Not Found`
	}

	response := fmt.Sprintf(
		"HTTP/1.1 999 OK\r\n"+
			"Content-Type: text/plain\r\n"+
			"Content-Length: %d\r\n"+
			"\r\n"+
			"%s",
		len(body), body,
	)
	conn.Write([]byte(response))

}
