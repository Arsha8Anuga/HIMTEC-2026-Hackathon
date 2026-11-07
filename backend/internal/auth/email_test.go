package auth

import (
	"strings"
	"testing"
	"time"
)

func TestOtpMessage(t *testing.T) {
	m := string(otpMessage("app@contoh.id", "ibu@contoh.id", "123456", time.Unix(0, 0)))
	for _, want := range []string{"To: ibu@contoh.id\r\n", "Subject: Kode masuk Pantau Tumbuh Kembang\r\n", "charset=UTF-8\r\n\r\n", "Kode masuk Anda: 123456"} {
		if !strings.Contains(m, want) {
			t.Fatalf("pesan tanpa %q:\n%s", want, m)
		}
	}
}

func TestSMTPFromEnvRequiresSettings(t *testing.T) {
	for _, k := range []string{"SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM", "SMTP_PORT"} {
		t.Setenv(k, "")
	}
	if _, err := SMTPFromEnv(); err == nil {
		t.Fatal("tanpa SMTP_* seharusnya gagal")
	}
	t.Setenv("SMTP_HOST", "smtp.contoh.id")
	t.Setenv("SMTP_USER", "u")
	t.Setenv("SMTP_PASSWORD", "p")
	t.Setenv("SMTP_FROM", "app@contoh.id")
	t.Setenv("SMTP_PORT", "465")
	if _, err := SMTPFromEnv(); err == nil {
		t.Fatal("port 465 seharusnya ditolak")
	}
	t.Setenv("SMTP_PORT", "")
	if _, err := SMTPFromEnv(); err != nil {
		t.Fatal(err)
	}
}
