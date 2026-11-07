package engineclient

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// Engine Python hanya menerima HTTP/JSON; Go mengirim seluruh riwayat, tanpa menyimpan skor medis.
type Client struct {
	BaseURL string
	HTTP    *http.Client
}
type EngineError struct {
	Code    string            `json:"code"`
	Message string            `json:"message"`
	Fields  map[string]string `json:"fields"`
}

func (e *EngineError) Error() string { return e.Code + ": " + e.Message }

// Failure distinguishes engine transport/protocol errors from database errors.
// It is internal Go state, not an additional field in the public API.
type Failure struct {
	Operation string
	Err       error
}

func (e *Failure) Error() string { return "engine " + e.Operation + ": " + e.Err.Error() }
func (e *Failure) Unwrap() error { return e.Err }

func New(baseURL string) *Client {
	return &Client{BaseURL: strings.TrimRight(baseURL, "/"), HTTP: &http.Client{Timeout: 3 * time.Second}}
}
func (c *Client) Do(ctx context.Context, method, path string, payload any, out any) (err error) {
	defer func() {
		if err != nil {
			err = &Failure{Operation: method + " " + path, Err: err}
		}
	}()
	var reader io.Reader
	if payload != nil {
		b, err := json.Marshal(payload)
		if err != nil {
			return err
		}
		reader = bytes.NewReader(b)
	}
	req, err := http.NewRequestWithContext(ctx, method, c.BaseURL+path, reader)
	if err != nil {
		return err
	}
	if payload != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	resp, err := c.HTTP.Do(req)
	if err != nil {
		return fmt.Errorf("panggilan engine: %w", err)
	}
	defer resp.Body.Close()
	const maxResponseBytes = 4 << 20
	b, err := io.ReadAll(io.LimitReader(resp.Body, maxResponseBytes+1))
	if err != nil {
		return err
	}
	if len(b) > maxResponseBytes {
		return errors.New("response engine melebihi 4 MiB")
	}
	var envelope struct {
		Data  json.RawMessage `json:"data"`
		Error json.RawMessage `json:"error"`
	}
	if err = json.Unmarshal(b, &envelope); err != nil {
		return fmt.Errorf("response engine bukan JSON: %w", err)
	}
	if len(envelope.Error) == 0 {
		return errors.New("response engine tidak punya field error")
	}
	if !bytes.Equal(bytes.TrimSpace(envelope.Error), []byte("null")) {
		var remote EngineError
		if err = json.Unmarshal(envelope.Error, &remote); err != nil || remote.Code == "" || remote.Message == "" {
			return errors.New("format error engine tidak valid")
		}
		// Only genuine input validation is safe to return as a client error.
		if resp.StatusCode == http.StatusUnprocessableEntity && remote.Code == "VALIDATION_ERROR" {
			return &remote
		}
		return fmt.Errorf("HTTP engine %d (%s): %s", resp.StatusCode, remote.Code, remote.Message)
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP engine %d", resp.StatusCode)
	}
	if len(envelope.Data) == 0 || bytes.Equal(bytes.TrimSpace(envelope.Data), []byte("null")) {
		return errors.New("response engine tidak punya data yang dapat digunakan")
	}
	if out != nil {
		return json.Unmarshal(envelope.Data, out)
	}
	return nil
}
func (c *Client) Get(ctx context.Context, path string, out any) error {
	return c.Do(ctx, http.MethodGet, path, nil, out)
}
func (c *Client) Post(ctx context.Context, path string, input, out any) error {
	return c.Do(ctx, http.MethodPost, path, input, out)
}
func ReferencePath(indicator, sex string, from, to int) string {
	q := url.Values{}
	q.Set("indicator", indicator)
	q.Set("sex", sex)
	q.Set("x_from", fmt.Sprint(from))
	q.Set("x_to", fmt.Sprint(to))
	return "/reference?" + q.Encode()
}
