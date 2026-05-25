package main

import (
	"errors"
	"fmt"
)

func main() {
	fmt.Println(divide(8, 6))
	fmt.Println(divide(100, 5))
	q2, r2, err := divide(8, 0) // 0 で割る
	if err != nil {
		fmt.Printf("エラーが発生しました。%s\n", err)
		return
	}
	fmt.Println(q2, r2, err)
}

func divide(a int, b int) (int, int, error) {
	if b == 0 {
		return 0, 0, errors.New("0では割れません")
	}
	ans := a / b
	mod := a % b
	return ans, mod, nil
}
