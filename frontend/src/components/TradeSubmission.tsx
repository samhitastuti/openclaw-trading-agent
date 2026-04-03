// frontend/src/components/TradeSubmission.tsx

import { useState, FormEvent } from 'react';
import { submitTrade, TradeResponse } from '../api';

export function TradeSubmission() {
  const [instruction, setInstruction] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TradeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await submitTrade(instruction);
      setResult(response);
    } catch (err) {
      console.error('Trade submission error:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const isAllowed = result
    ? result.status.toLowerCase() === 'success'
    : false;

  return (
    <div className="trade-submission">
      <h2>🤖 OpenClaw Trading Agent - Submit Trade</h2>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="instruction">Trade Instruction:</label>
          <textarea
            id="instruction"
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="e.g., 'Buy 2 shares of MSFT at $430'"
            rows={3}
          />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? '⏳ Processing...' : '📤 Submit Trade'}
        </button>
      </form>

      {error && (
        <div className="error">
          <h3>❌ Error</h3>
          <p>{error}</p>
        </div>
      )}

      {result && (
        <div className={`result ${result.status.toLowerCase()}`}>
          <h3>{isAllowed ? '✅ ALLOWED' : '🚫 BLOCKED'}</h3>

          {result.reason && (
            <p><strong>Reason:</strong> {result.reason}</p>
          )}

          {/* AI Classification Section */}
          {result.ai_classification && (
            <div className="ai-classification">
              <h4>🤖 AI Classification</h4>
              <table>
                <tbody>
                  <tr>
                    <td><strong>Intent:</strong></td>
                    <td>{result.ai_classification.intent}</td>
                  </tr>
                  <tr>
                    <td><strong>Risk Level:</strong></td>
                    <td>
                      <span className={`risk-${result.ai_classification.risk_level}`}>
                        {result.ai_classification.risk_level.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td><strong>Confidence:</strong></td>
                    <td>{(result.ai_classification.confidence * 100).toFixed(0)}%</td>
                  </tr>
                  <tr>
                    <td><strong>Model:</strong></td>
                    <td>{result.ai_classification.ai_model}</td>
                  </tr>
                </tbody>
              </table>

              {result.ai_classification.risk_factors.length > 0 && (
                <div className="risk-factors">
                  <strong>Risk Factors:</strong>
                  <ul>
                    {result.ai_classification.risk_factors.map((factor, i) => (
                      <li key={i}>⚠️ {factor}</li>
                    ))}
                  </ul>
                </div>
              )}

              {result.ai_classification.extracted_data && (
                <div className="extracted-data">
                  <strong>Extracted Data:</strong>
                  <ul>
                    {result.ai_classification.extracted_data.ticker && (
                      <li>📊 Ticker: {result.ai_classification.extracted_data.ticker}</li>
                    )}
                    {result.ai_classification.extracted_data.qty && (
                      <li>📈 Quantity: {result.ai_classification.extracted_data.qty}</li>
                    )}
                    {result.ai_classification.extracted_data.price && (
                      <li>💰 Price: ${result.ai_classification.extracted_data.price}</li>
                    )}
                    {result.ai_classification.extracted_data.action && (
                      <li>🎯 Action: {result.ai_classification.extracted_data.action}</li>
                    )}
                  </ul>
                </div>
              )}

              <p className="reasoning"><em>"{result.ai_classification.reasoning}"</em></p>
            </div>
          )}

          {/* Policy Decision Section */}
          {result.policy_decision && (
            <div className="policy-decision">
              <h4>🛡️ Policy Decision</h4>
              <p>
                <strong>Status:</strong>{' '}
                {result.policy_decision.allowed ? '✅ ALLOWED - Would Execute' : '🚫 BLOCKED - Enforcement Triggered'}
              </p>
              {result.policy_decision.reason && (
                <p><strong>Reason:</strong> {result.policy_decision.reason}</p>
              )}
              {result.policy_decision.constraints_checked && (
                <div>
                  <strong>Constraints Checked:</strong>
                  <ul>
                    {result.policy_decision.constraints_checked.map((c, i) => (
                      <li key={i}>✓ {c}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {result.timestamp && (
            <p className="timestamp"><small>⏰ {new Date(result.timestamp).toLocaleString()}</small></p>
          )}
        </div>
      )}
    </div>
  );
}
