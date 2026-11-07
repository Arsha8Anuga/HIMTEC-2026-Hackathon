package main

import (
	"context"
	"log"
	"net"
	"net/http"
	"os"
	"time"

	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/auth"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/config"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/engineclient"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/handler"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/repository"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/service"
)

func main() {
	// Jalankan dari backend/: go run ./cmd/server. File .env disimpan di akar repository.
	config.Load()
	databaseURL := os.Getenv("DATABASE_URL")
	engineURL := os.Getenv("ENGINE_URL")
	if databaseURL == "" {
		log.Fatal("DATABASE_URL wajib diisi; lihat ../.env.example")
	}
	if engineURL == "" {
		log.Fatal("ENGINE_URL wajib diisi; lihat ../.env.example")
	}
	mode := os.Getenv("AUTH_MODE")
	if mode != "" && mode != "demo" && mode != "otp_dummy" {
		log.Fatal("AUTH_MODE harus demo atau otp_dummy")
	}
	address := ":8080"
	if mode == "otp_dummy" {
		address = "127.0.0.1:8080"
	}
	listener, err := net.Listen("tcp", address)
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
	engine := engineclient.New(engineURL)
	svc, err := service.New(store, engine, "data")
	if err != nil {
		log.Fatalf("memuat data statis: %v", err)
	}
	cors := os.Getenv("CORS_ORIGIN")
	if cors == "" {
		cors = "http://localhost:5173"
	}
	var authentication *auth.Service
	if mode == "otp_dummy" {
		authentication, err = auth.New(store.DB, func(email, id, code string) {
			log.Printf("[OTP DUMMY - LOKAL] email=%s challenge_id=%s kode=%s (berlaku 5 menit)", email, id, code)
		})
		if err != nil {
			log.Fatal(err)
		}
		log.Print("AUTH_MODE=otp_dummy: login wajib; server hanya di 127.0.0.1; OTP hanya dicetak di terminal")
	} else {
		log.Print("AUTH_MODE=demo: tanpa login; gunakan AUTH_MODE=otp_dummy untuk autentikasi")
	}
	probeCtx, probeCancel := context.WithTimeout(context.Background(), 3*time.Second)
	log.Print(engine.Inspect(probeCtx).Summary())
	probeCancel()
	routes := (&handler.Handler{Svc: svc, CORSOrigin: cors, Auth: authentication}).Routes()
	server := &http.Server{Addr: ":8080", Handler: routes, ReadHeaderTimeout: 5 * time.Second}
	log.Printf("Backend Go siap pada http://localhost:8080/api/v1 (engine: %s)", engineURL)
	log.Fatal(server.Serve(listener))
}
