"use client";

import { useMemo, useState } from "react";

import { PriceLineChart, formatCurrency, toNumber } from "./NadacPricingDashboard";

type PredictionPoint = {
  month: number;
  predicted_price: string | number;
};

type PredictionSummary = {
  min_price: string | number | null;
  max_price: string | number | null;
  average_price: string | number | null;
  median_price: string | number | null;
  price_range: string | number | null;
  first_price: string | number | null;
  last_price: string | number | null;
  total_change: string | number | null;
  total_change_pct: string | number | null;
};

type PredictionResponse = {
  ndc11: string;
  months: number;
  summary: PredictionSummary;
  predictions: PredictionPoint[];
};

function formatPercent(value: string | number | null | undefined) {
  const parsed = toNumber(value);
  if (parsed === null) return "-";
  return `${parsed >= 0 ? "+" : ""}${parsed.toFixed(2)}%`;
}

export default function NdcPredictionPanel({ ndc11, months = 12 }: { ndc11: string; months?: number }) {
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const chartPoints = useMemo(
    () =>
      prediction?.predictions
        .map((point, index, points) => {
          const value = toNumber(point.predicted_price);
          const previousValue = index > 0 ? toNumber(points[index - 1].predicted_price) : null;
          const changePct = value !== null && previousValue !== null && previousValue !== 0
            ? ((value - previousValue) / previousValue) * 100
            : null;

          return { label: `+${point.month}m`, value, changePct };
        })
        .filter((point): point is { label: string; value: number; changePct: number | null } => point.value !== null) ?? [],
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
        {!prediction && (
          <button type="button" className="btn-secondary prediction-button" onClick={runPrediction} disabled={loading || !ndc11}>
            {loading ? "Calculating..." : "Run prediction"}
          </button>
        )}
      </div>

      {error && <div className="error-box">{error}</div>}

      {prediction ? (
        <div className="prediction-result">
          <PriceLineChart points={chartPoints} valueLabel="NDC price prediction" />
          <div className="prediction-stat-list">
            <article className="prediction-summary">
              <span>Average</span>
              <strong>{formatCurrency(prediction.summary.average_price)}</strong>
            </article>
            <article className="prediction-summary">
              <span>Median</span>
              <strong>{formatCurrency(prediction.summary.median_price)}</strong>
            </article>
            <article className="prediction-summary">
              <span>Range</span>
              <strong>{formatCurrency(prediction.summary.price_range)}</strong>
            </article>
            <article className="prediction-summary">
              <span>Total change</span>
              <strong>{formatPercent(prediction.summary.total_change_pct)}</strong>
            </article>
          </div>
        </div>
      ) : (
        <p className="prediction-empty">The forecast graph will appear here after the model endpoint returns.</p>
      )}
    </section>
  );
}
