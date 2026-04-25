"use client";

import { useMemo, useState } from "react";

import { PriceLineChart, formatCurrency, toNumber } from "./NadacPricingDashboard";

type PredictionPoint = {
  month: number;
  predicted_price: string | number;
};

type PredictionResponse = {
  ndc11: string;
  months: number;
  predictions: PredictionPoint[];
};

export default function NdcPredictionPanel({ ndc11, months = 12 }: { ndc11: string; months?: number }) {
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const chartPoints = useMemo(
    () =>
      prediction?.predictions
        .map((point) => ({ label: `+${point.month}m`, value: toNumber(point.predicted_price) }))
        .filter((point): point is { label: string; value: number } => point.value !== null) ?? [],
    [prediction],
  );

  async function runPrediction() {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ months: String(months) });
      const response = await fetch(`/api/ndc/${encodeURIComponent(ndc11)}/prediction?${params.toString()}`, {
        cache: "no-store",
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload?.error ?? payload?.detail ?? "Prediction request failed");
      }
      setPrediction(payload.data as PredictionResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Prediction request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="prediction-band">
      <div className="prediction-head">
        <div>
          <h3>Price prediction</h3>
          <p>Run a 12-month placeholder model forecast for this NDC.</p>
        </div>
        <button type="button" className="btn-secondary prediction-button" onClick={runPrediction} disabled={loading || !ndc11}>
          {loading ? "Calculating..." : "Run prediction"}
        </button>
      </div>

      {error && <div className="error-box">{error}</div>}

      {prediction ? (
        <div className="prediction-grid">
          <div className="prediction-summary">
            <span>{prediction.months} months</span>
            <strong>{formatCurrency(prediction.predictions[0]?.predicted_price)}</strong>
            <small>First forecasted month</small>
          </div>
          <PriceLineChart points={chartPoints} valueLabel="NDC price prediction" />
        </div>
      ) : (
        <p className="prediction-empty">The forecast graph will appear here after the model endpoint returns.</p>
      )}
    </section>
  );
}
