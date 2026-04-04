// frontend/src/api.ts

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
console.log('🔌 API_URL:', API_URL);  // ← ADD THIS LINE
console.log('📦 VITE_API_URL env:', import.meta.env.VITE_API_URL);  // ← ADD THIS LINE

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
