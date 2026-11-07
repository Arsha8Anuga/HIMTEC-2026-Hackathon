// Package llm calls a local Ollama server (POST /api/chat, non-streaming).
package llm

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"regexp"
	"strings"
	"time"
)

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type Client struct {
	URL   string
	Model string
	HTTP  *http.Client
}

func New(url, model string, timeout time.Duration) *Client {
	return &Client{URL: strings.TrimRight(url, "/"), Model: model, HTTP: &http.Client{Timeout: timeout}}
}

// Thinking models (e.g. qwen3) may prepend their reasoning; it never reaches the parent.
var think = regexp.MustCompile(`(?s)<think>.*?</think>`)

func (c *Client) Chat(ctx context.Context, messages []Message) (string, error) {
	body, _ := json.Marshal(map[string]any{
		"model": c.Model, "messages": messages, "stream": false,
		"options": map[string]any{"temperature": 0.2},
	})
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.URL+"/api/chat", bytes.NewReader(body))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := c.HTTP.Do(req)
	if err != nil {
		return "", fmt.Errorf("ollama tidak dapat dihubungi: %w", err)
	}
	defer resp.Body.Close()
	raw, err := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if err != nil {
		return "", err
	}
	var out struct {
		Message Message `json:"message"`
		Error   string  `json:"error"`
	}
	if err = json.Unmarshal(raw, &out); err != nil {
		return "", fmt.Errorf("respons ollama bukan JSON: %w", err)
	}
	if resp.StatusCode != http.StatusOK || out.Error != "" {
		return "", fmt.Errorf("ollama HTTP %d: %s", resp.StatusCode, out.Error)
	}
	text := strings.TrimSpace(think.ReplaceAllString(out.Message.Content, ""))
	if text == "" {
		return "", errors.New("ollama mengembalikan jawaban kosong")
	}
	return text, nil
}
