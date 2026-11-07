package main

import (
	"bufio"
	"context"
	"log"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/engineclient"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/handler"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/repository"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/service"
)

func loadEnv(path string) {
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
func main() {
	// Jalankan dari backend/: go run ./cmd/server. File .env disimpan di akar repository.
	loadEnv(filepath.Join("..", ".env"))
	loadEnv(".env")
	databaseURL := os.Getenv("DATABASE_URL")
	engineURL := os.Getenv("ENGINE_URL")
	if databaseURL == "" {
		log.Fatal("DATABASE_URL wajib diisi; lihat ../.env.example")
	}
	if engineURL == "" {
		log.Fatal("ENGINE_URL wajib diisi; lihat ../.env.example")
	}
	listener, err := net.Listen("tcp", ":8080")
	if err != nil {
		log.Fatalf("tidak dapat memakai port 8080; periksa backend lama/proses lain yang masih berjalan: %v", err)
	}
	defer listener.Close()
	store, err := repository.Open(databaseURL)
	if err != nil {
		log.Fatal(err)
	}
	defer store.DB.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := store.Migrate(ctx, "migrations"); err != nil {
		log.Fatalf("migrasi PostgreSQL gagal: %v", err)
	}
	svc, err := service.New(store, engineclient.New(engineURL), "data")
	if err != nil {
		log.Fatalf("memuat data statis: %v", err)
	}
	cors := os.Getenv("CORS_ORIGIN")
	if cors == "" {
		cors = "http://localhost:5173"
	}
	routes := (&handler.Handler{Svc: svc, CORSOrigin: cors}).Routes()
	server := &http.Server{Addr: ":8080", Handler: routes, ReadHeaderTimeout: 5 * time.Second}
	log.Printf("Backend Go siap pada http://localhost:8080/api/v1 (engine: %s)", engineURL)
	log.Fatal(server.Serve(listener))
}
