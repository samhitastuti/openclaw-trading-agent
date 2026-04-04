// frontend/src/api.ts
//
// Dev (Vite): by default uses same-origin `/api/...` — Vite proxies to FastAPI (see vite.config.ts).
// This avoids browser → localhost:8000 failures when the API is down or Windows resolves localhost oddly.
// Set VITE_DIRECT_API=true to use VITE_API_URL from the browser instead.
// Prod: set VITE_API_URL to your deployed API origin.

function resolveApiBase(): string {
  const raw =
    typeof import.meta.env.VITE_API_URL === 'string'
      ? import.meta.env.VITE_API_URL.trim()
      : '';
  const direct =
    import.meta.env.VITE_DIRECT_API === 'true' ||
    import.meta.env.VITE_DIRECT_API === '1';

  if (import.meta.env.DEV && !direct) {
    return '';
  }
  if (raw !== '') {
    return raw.replace(/\/$/, '');
  }
  return '';
}

/** Base URL for API calls (empty = same-origin + Vite `/api` proxy in dev). */
export const API_URL = resolveApiBase();

const AUTH_FETCH_TIMEOUT_MS = 25_000;

async function fetchWithTimeout(
  input: string,
  init: RequestInit,
  timeoutMs: number
): Promise<Response> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    return await fetch(input, { ...init, signal: ctrl.signal });
  } finally {
    clearTimeout(t);
  }
}

/** Turn browser "Failed to fetch" into an actionable message. */
function wrapAuthNetworkError(e: unknown): Error {
  if (e instanceof Error && e.name === 'AbortError') {
    return new Error(
      'Request timed out. Start the API on port 8000 (uvicorn) and try again.'
    );
  }
  const msg = e instanceof Error ? e.message : String(e);
  const lower = msg.toLowerCase();
  if (
    e instanceof TypeError ||
    lower.includes('failed to fetch') ||
    lower.includes('networkerror') ||
    lower.includes('load failed')
  ) {
    const hint =
      API_URL === ''
        ? 'Using the dev proxy: start FastAPI on port 8000 (run run_api.ps1 or: python -m uvicorn backend.api.server:app --reload --host 127.0.0.1 --port 8000 from the repo root with PYTHONPATH=.).'
        : `Calling "${API_URL}" from the browser. Start the API on that host/port, try http://127.0.0.1:8000 instead of localhost on Windows, or remove VITE_DIRECT_API to use the dev proxy.`;
    return new Error(`Cannot reach the API (${msg}). ${hint}`);
  }
  return e instanceof Error ? e : new Error(msg);
}

export interface AIClassification {
  intent: string;
  risk_level: 'safe' | 'caution' | 'high_risk' | 'critical';
  confidence: number;
  extracted_data: {
    ticker?: string;
    qty?: number;
    price?: number;
    action?: string;
  };
  risk_factors: string[];
  reasoning: string;
  ai_model: string;
}

export interface PolicyDecision {
  allowed: boolean;
  reason?: string;
  constraints_checked: string[];
}

export interface TradeResponse {
  status: 'success' | 'blocked' | 'SUCCESS' | 'BLOCKED' | 'PENDING' | 'ERROR' | string;
  instruction?: string;
  ai_classification?: AIClassification;
  policy_decision?: PolicyDecision;
  timestamp?: string;
  reason?: string;
}

export async function submitTrade(instruction: string): Promise<TradeResponse> {
  const response = await fetch(`${API_URL}/api/trade`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ instruction }),
  });

  if (!response.ok) {
    throw new Error(`Trade submission failed: ${response.statusText}`);
  }

  return response.json();
}

export async function getAllowedScenario(): Promise<any> {
  const response = await fetch(`${API_URL}/api/demo/allowed-scenario`);
  return response.json();
}

export async function getBlockedSizeScenario(): Promise<any> {
  const response = await fetch(`${API_URL}/api/demo/blocked-scenario-size`);
  return response.json();
}

export async function getBlockedCredentialScenario(): Promise<any> {
  const response = await fetch(`${API_URL}/api/demo/blocked-scenario-credential`);
  return response.json();
}

export async function getPolicy(): Promise<any> {
  const response = await fetch(`${API_URL}/api/policy`);
  return response.json();
}

export async function getAuditTrail(): Promise<any> {
  const response = await fetch(`${API_URL}/api/audit/decisions`);
  return response.json();
}

// ─── Veridict auth (SQLite-backed API) ─────────────────────────────────

export interface AuthUser {
  id: number;
  email: string;
  full_name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

function parseAuthResponse(data: unknown): AuthResponse {
  if (!data || typeof data !== 'object') {
    throw new Error('Invalid response from server. Is the API running on port 8000?');
  }
  const d = data as Record<string, unknown>;
  const token = d.access_token;
  const user = d.user;
  if (typeof token !== 'string' || !token) {
    throw new Error(
      'Login API returned no token. Check that the backend is running and VITE_API_URL / dev proxy is correct.'
    );
  }
  if (!user || typeof user !== 'object') {
    throw new Error('Login API returned no user object.');
  }
  const u = user as Record<string, unknown>;
  if (typeof u.email !== 'string' || typeof u.id !== 'number' || typeof u.full_name !== 'string') {
    throw new Error('Login API returned an invalid user payload.');
  }
  return {
    access_token: token,
    token_type: typeof d.token_type === 'string' ? d.token_type : 'bearer',
    user: { id: u.id, email: u.email, full_name: u.full_name },
  };
}

function errorMessageFromBody(data: unknown, fallback: string): string {
  if (!data || typeof data !== 'object') return fallback;
  const d = data as { detail?: unknown };
  const detail = d.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((x) => (typeof x === 'object' && x && 'msg' in x ? String((x as { msg: string }).msg) : String(x)))
      .join(', ');
  }
  return fallback;
}

export async function registerAccount(
  full_name: string,
  email: string,
  password: string
): Promise<AuthResponse> {
  try {
    const response = await fetchWithTimeout(
      `${API_URL}/api/auth/register`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full_name, email, password }),
      },
      AUTH_FETCH_TIMEOUT_MS
    );
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(errorMessageFromBody(data, 'Registration failed'));
    }
    return parseAuthResponse(data);
  } catch (e) {
    throw wrapAuthNetworkError(e);
  }
}

export async function loginAccount(email: string, password: string): Promise<AuthResponse> {
  try {
    const response = await fetchWithTimeout(
      `${API_URL}/api/auth/login`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      },
      AUTH_FETCH_TIMEOUT_MS
    );
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(errorMessageFromBody(data, 'Login failed'));
    }
    return parseAuthResponse(data);
  } catch (e) {
    throw wrapAuthNetworkError(e);
  }
}
