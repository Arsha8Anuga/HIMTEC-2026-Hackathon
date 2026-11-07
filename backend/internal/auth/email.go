package auth

import (
	"errors"
	"fmt"
	"log"
	"net/smtp"
	"os"
	"strings"
	"time"
)

// SMTPFromEnv builds the OTP deliverer for AUTH_MODE=otp_email from SMTP_HOST, SMTP_PORT,
// SMTP_USER, SMTP_PASSWORD and SMTP_FROM. net/smtp upgrades to STARTTLS (port 587) and
// refuses to send the password over an unencrypted connection to a remote host.
func SMTPFromEnv() (func(email, id, code string), error) {
	host, user, pass, from := os.Getenv("SMTP_HOST"), os.Getenv("SMTP_USER"), os.Getenv("SMTP_PASSWORD"), os.Getenv("SMTP_FROM")
	port := os.Getenv("SMTP_PORT")
	if port == "" {
		port = "587"
	}
	if host == "" || user == "" || pass == "" || from == "" {
		return nil, errors.New("AUTH_MODE=otp_email butuh SMTP_HOST, SMTP_USER, SMTP_PASSWORD, dan SMTP_FROM")
	}
	if port == "465" {
		return nil, errors.New("SMTP_PORT 465 (TLS langsung) tidak didukung; pakai 587 (STARTTLS)")
	}
	if _, err := Email(from); err != nil {
		return nil, fmt.Errorf("SMTP_FROM tidak valid: %w", err)
	}
	auth := smtp.PlainAuth("", user, pass, host)
	return func(to, id, code string) {
		// The code never goes to the log; a failed send only means the parent asks again after 60 s.
		if err := smtp.SendMail(host+":"+port, auth, from, []string{to}, otpMessage(from, to, code, time.Now())); err != nil {
			log.Printf("OTP email gagal dikirim (challenge %s): %v", id, err)
		}
	}, nil
}

func otpMessage(from, to, code string, now time.Time) []byte {
	lines := []string{
		"From: Pantau Tumbuh Kembang <" + from + ">",
		"To: " + to,
		"Subject: Kode masuk Pantau Tumbuh Kembang",
		"Date: " + now.Format(time.RFC1123Z),
		"MIME-Version: 1.0",
		"Content-Type: text/plain; charset=UTF-8",
		"",
		"Kode masuk Anda: " + code,
		"",
		"Kode berlaku 5 menit dan hanya dapat dipakai sekali.",
		"Jangan berikan kode ini kepada siapa pun, termasuk petugas.",
		"Abaikan email ini bila Anda tidak meminta kode.",
	}
	return []byte(strings.Join(lines, "\r\n") + "\r\n")
}
