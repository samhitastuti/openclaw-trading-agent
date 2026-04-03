export type DecisionStatus = 'PENDING' | 'ALLOWED' | 'WARNING' | 'BLOCKED';

export interface EvaluationResult {
  input: string;
  parsedIntent: {
    action: string;
    amount: number;
    asset: string;
  };
  triggeredRules: string[];
  status: DecisionStatus;
  reason: string;
  confidence: number;
  timestamp: number;
}

export interface LogEntry {
  id: string;
  input: string;
  status: DecisionStatus;
  timestamp: number;
  decision: string;
  confidence: number;
  risks: string[];
}
