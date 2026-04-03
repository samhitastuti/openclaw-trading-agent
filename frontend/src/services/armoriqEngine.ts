import { EvaluationResult } from '../types';

const ASSETS = ['AAPL', 'BTC', 'ETH', 'TSLA', 'NVDA', 'SOL'];

export const evaluateIntent = async (input: string): Promise<EvaluationResult> => {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 700));

  const lowerInput = input.toLowerCase();
  
  // Simple parsing logic
  let action = 'UNKNOWN';
  if (lowerInput.includes('buy')) action = 'BUY';
  if (lowerInput.includes('sell')) action = 'SELL';
  if (lowerInput.includes('transfer')) action = 'TRANSFER';

  const amountMatch = lowerInput.match(/\d+/);
  const amount = amountMatch ? parseInt(amountMatch[0]) : 0;

  const asset = ASSETS.find(a => lowerInput.includes(a.toLowerCase())) || 'UNKNOWN';

  const triggeredRules: string[] = [];
  let status: EvaluationResult['status'] = 'ALLOWED';
  let reason = 'Intent verified against Armoriq standard policies.';
  let confidence = 98.5;

  // Rule 1: Amount > 10,000 -> Warning
  if (amount > 10000) {
    triggeredRules.push('High value transaction threshold (>10k)');
    status = 'WARNING';
    reason = 'Transaction exceeds standard liquidity thresholds.';
    confidence = 85.2;
  }

  // Rule 2: Amount > 25,000 -> Blocked
  if (amount > 25000) {
    triggeredRules.push('Critical value limit exceeded (>25k)');
    status = 'BLOCKED';
    reason = 'Security protocol: Transaction blocked due to extreme value risk.';
    confidence = 99.1;
  }

  // Rule 3: "urgent" / "all money" -> Blocked
  if (lowerInput.includes('urgent') || lowerInput.includes('all money') || lowerInput.includes('all funds')) {
    triggeredRules.push('Emotional/Urgency sentiment detected');
    status = 'BLOCKED';
    reason = 'Potential social engineering or panic execution detected.';
    confidence = 94.8;
  }

  // Rule 4: Unknown asset -> Warning
  if (asset === 'UNKNOWN' && action !== 'UNKNOWN') {
    triggeredRules.push('Unverified asset identifier');
    if (status !== 'BLOCKED') {
      status = 'WARNING';
      reason = 'Executing on unverified asset. Proceed with extreme caution.';
      confidence = 72.4;
    }
  }

  if (action === 'UNKNOWN') {
    status = 'WARNING';
    reason = 'Could not clearly identify execution intent.';
    confidence = 45.0;
  }

  return {
    input,
    parsedIntent: { action, amount, asset },
    triggeredRules,
    status,
    reason,
    confidence,
    timestamp: Date.now(),
  };
};
