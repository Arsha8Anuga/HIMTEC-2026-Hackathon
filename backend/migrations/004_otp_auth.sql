-- Local OTP-dummy authentication. No plaintext codes or bearer tokens in DB.
CREATE UNIQUE INDEX IF NOT EXISTS users_email_lower_unique ON users(lower(email)) WHERE email IS NOT NULL;
CREATE TABLE IF NOT EXISTS otp_codes (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL,
    purpose TEXT NOT NULL CHECK (purpose IN ('register','login')),
    pending_name TEXT NOT NULL DEFAULT '',
    code_hash TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS otp_email_created ON otp_codes(email,created_at DESC);
CREATE TABLE IF NOT EXISTS auth_sessions (
    token_hash TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS auth_sessions_user ON auth_sessions(user_id);
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
