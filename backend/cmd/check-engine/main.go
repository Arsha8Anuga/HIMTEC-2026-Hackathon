package main

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/config"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/engineclient"
	"os"
	"time"
)

func main() {
	config.Load()
	base := os.Getenv("ENGINE_URL")
	if base == "" {
		fmt.Fprintln(os.Stderr, "ENGINE_URL wajib diisi")
		os.Exit(2)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	report := engineclient.New(base).Inspect(ctx)
	json.NewEncoder(os.Stdout).Encode(report)
	fmt.Fprintln(os.Stderr, report.Summary())
	if report.Health != "ok" || len(report.Missing) > 0 || (!report.Fake && report.WHOTablesLoaded != nil && !*report.WHOTablesLoaded) {
		os.Exit(1)
	}
	if report.OpenAPI == "unknown" {
		os.Exit(3)
	}
}
