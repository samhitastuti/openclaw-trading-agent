// frontend/src/api.ts

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
  const response = await fetch(`${API_URL}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ full_name, email, password }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(errorMessageFromBody(data, 'Registration failed'));
  }
  return data as AuthResponse;
}

export async function loginAccount(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(errorMessageFromBody(data, 'Login failed'));
  }
  return data as AuthResponse;
}