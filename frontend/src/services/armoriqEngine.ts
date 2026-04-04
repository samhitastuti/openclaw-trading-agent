import { API_URL } from '../api';
import { EvaluationResult, DecisionStatus } from '../types';

export const evaluateIntent = async (input: string): Promise<EvaluationResult> => {
  const response = await fetch(`${API_URL}/api/trade`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ instruction: input }),
  });

  if (!response.ok) {
    throw new Error(`Trade evaluation failed: ${response.statusText}`);
  }

  const data = await response.json();

  // Map backend status to frontend DecisionStatus
  const backendStatus = (data.status || '').toLowerCase();
  let status: DecisionStatus;
  if (backendStatus === 'success') {
    status = 'ALLOWED';
  } else if (backendStatus === 'blocked') {
    status = 'BLOCKED';
  } else {
    status = 'WARNING';
  }

  // Extract parsed intent from AI classification
  const extractedData = data.ai_classification?.extracted_data ?? {};
  const rawAction = typeof extractedData.action === 'string' ? extractedData.action : 'UNKNOWN';
  const parsedIntent = {
    action: rawAction.toUpperCase(),
    amount: typeof extractedData.qty === 'number' ? extractedData.qty : 0,
    asset: typeof extractedData.ticker === 'string' ? extractedData.ticker : 'UNKNOWN',
  };

  // Triggered rules come from the AI risk factors list
  const triggeredRules: string[] = data.ai_classification?.risk_factors ?? [];

  // Backend confidence is 0.0–1.0; convert to percentage for the UI
  const rawConfidence: number = data.ai_classification?.confidence ?? 0.5;
  const confidence = Math.round(rawConfidence * 1000) / 10;

  const reason: string =
    data.reason ||
    data.policy_decision?.reason ||
    'Intent evaluated by Armoriq policy engine.';

  return {
    input,
    parsedIntent,
    triggeredRules,
    status,
    reason,
    confidence,
    timestamp: Date.now(),
  };
};
