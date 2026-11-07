package config

import (
	"bufio"
	"os"
	"strings"
)

func LoadEnv(path string) {
	f, err := os.Open(path)
	if err != nil {
		return
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		k, v, ok := strings.Cut(line, "=")
		if !ok {
			continue
		}
		k = strings.TrimSpace(k)
		v = strings.Trim(strings.TrimSpace(v), "\"'")
		if os.Getenv(k) == "" {
			_ = os.Setenv(k, v)
		}
	}
}

func Load() { LoadEnv("../.env"); LoadEnv(".env") }
