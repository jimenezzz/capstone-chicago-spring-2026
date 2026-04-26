"use client";

import { useEffect, useMemo, useState } from "react";

import {
  PriceLineChart,
  formatCurrency,
  toNumber,
  type NadacHistoryPoint,
} from "./NadacPricingDashboard";

type PredictionPoint = {
  month: number;
  target_month: string | null;
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
  model: PredictionModel;
  model_name: string;
  summary: PredictionSummary;
  predictions: PredictionPoint[];
};

type PredictionModel = "lightgbm" | "arima";

const MODEL_OPTIONS: Array<{ value: PredictionModel; label: string }> = [
  { value: "lightgbm", label: "LightGBM" },
  { value: "arima", label: "ARIMA" },
];

function formatPercent(value: string | number | null | undefined) {
  const parsed = toNumber(value);
  if (parsed === null) return "-";
  return `${parsed >= 0 ? "+" : ""}${parsed.toFixed(2)}%`;
}

function trendClass(value: string | number | null | undefined) {
  const parsed = toNumber(value);
  if (parsed === null || parsed === 0) return "neutral";
  return parsed > 0 ? "up" : "down";
}

export default function NdcPredictionPanel({
  ndc11,
  months = 12,
  history = [],
}: {
  ndc11: string;
  months?: number;
  history?: NadacHistoryPoint[];
}) {
  const [predictionsByKey, setPredictionsByKey] = useState<Record<string, PredictionResponse>>({});
  const [failuresByKey, setFailuresByKey] = useState<Record<string, string>>({});
  const [selectedModel, setSelectedModel] = useState<PredictionModel>("lightgbm");
  const [loadingModels, setLoadingModels] = useState<Partial<Record<PredictionModel, boolean>>>({});
  const [showHistory, setShowHistory] = useState(false);
  const predictionKey = modelPredictionKey(ndc11, months, selectedModel);
  const prediction = predictionsByKey[predictionKey] ?? null;
  const selectedFailure = failuresByKey[predictionKey] ?? null;
  const isLoadingSelected = Boolean(loadingModels[selectedModel]);
  const isLoadingAny = MODEL_OPTIONS.some((option) => loadingModels[option.value]);

  const orderedModelOptions = useMemo(() => {
    return [...MODEL_OPTIONS].sort((first, second) => {
      const firstKey = modelPredictionKey(ndc11, months, first.value);
      const secondKey = modelPredictionKey(ndc11, months, second.value);
      const firstFailed = !predictionsByKey[firstKey] && Boolean(failuresByKey[firstKey]);
      const secondFailed = !predictionsByKey[secondKey] && Boolean(failuresByKey[secondKey]);
      return Number(firstFailed) - Number(secondFailed);
    });
  }, [failuresByKey, months, ndc11, predictionsByKey]);

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

  const historyChartPoints = useMemo(
    () =>
      history
        .filter((row) => row.effective_date && toNumber(row.nadac_price) !== null)
        .map((row) => ({ label: row.effective_date as string, value: toNumber(row.nadac_price) as number }))
        .reverse()
        .map((point, index, points) => {
          const previous = points[index - 1];
          const changePct = previous && previous.value !== 0 ? ((point.value - previous.value) / previous.value) * 100 : null;
          return { ...point, changePct };
        }),
    [history],
  );

  async function fetchPrediction(model: PredictionModel, force = false) {
    const key = modelPredictionKey(ndc11, months, model);
    if (!force && predictionsByKey[key]) {
      return predictionsByKey[key];
    }

    setLoadingModels((current) => ({ ...current, [model]: true }));
    setFailuresByKey((current) => {
      const next = { ...current };
      delete next[key];
      return next;
    });

    try {
      const params = new URLSearchParams({ months: String(months), model });
      const response = await fetch(`/api/ndc/${encodeURIComponent(ndc11)}/prediction?${params.toString()}`, {
        cache: "no-store",
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload?.error ?? payload?.detail ?? "Prediction request failed");
      }
      const nextPrediction = payload.data as PredictionResponse;
      if (!nextPrediction.predictions.length) {
        throw new Error("Prediction returned no forecast points");
      }
      setPredictionsByKey((current) => ({
        ...current,
        [key]: nextPrediction,
      }));
      return nextPrediction;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Prediction request failed";
      setFailuresByKey((current) => ({ ...current, [key]: message }));
      return null;
    } finally {
      setLoadingModels((current) => ({ ...current, [model]: false }));
    }
  }

  useEffect(() => {
    if (!ndc11) return;

    let cancelled = false;
    Promise.all(MODEL_OPTIONS.map((option) => fetchPrediction(option.value))).then((results) => {
      if (cancelled) return;
      const firstSuccessfulModel = results.find((result): result is PredictionResponse => Boolean(result))?.model;
      if (firstSuccessfulModel && !results.some((result) => result?.model === selectedModel)) {
        setSelectedModel(firstSuccessfulModel);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [ndc11, months]);

  return (
    <section className="prediction-band">
      <div className="prediction-head">
        <div>
          <h3>Price prediction</h3>
          <p>Run a 12-month forecast for this NDC using the selected model.</p>
        </div>
        <div className="prediction-actions">
          <label className="history-toggle">
            <input
              type="checkbox"
              checked={showHistory}
              onChange={(event) => setShowHistory(event.target.checked)}
              disabled={historyChartPoints.length === 0}
            />
            <span>Show history</span>
          </label>
          <div className="prediction-model-field">
            <label className="model-select-label" htmlFor={`prediction-model-${ndc11}`}>
              Model
            </label>
            <select
              id={`prediction-model-${ndc11}`}
              className="model-select"
              value={selectedModel}
              onChange={(event) => {
                setSelectedModel(event.target.value as PredictionModel);
              }}
              disabled={isLoadingAny}
            >
              {orderedModelOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <button
            type="button"
            className="btn-secondary prediction-button prediction-icon-button"
            onClick={() => fetchPrediction(selectedModel, true)}
            disabled={isLoadingSelected || !ndc11}
            aria-label="Update prediction"
            title="Update prediction"
          >
            <span aria-hidden="true">↻</span>
          </button>
        </div>
      </div>

      {selectedFailure && !prediction && <div className="error-box">{selectedFailure}</div>}

      {prediction ? (
        <div className="prediction-result">
          <div>
            <p className="prediction-model-name">{prediction.model_name}</p>
            <PriceLineChart
              points={chartPoints}
              comparisonPoints={showHistory ? historyChartPoints : []}
              valueLabel={`${prediction.model_name} NDC price prediction`}
            />
          </div>
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
              <strong className={trendClass(prediction.summary.total_change_pct)}>{formatPercent(prediction.summary.total_change_pct)}</strong>
            </article>
          </div>
        </div>
      ) : (
        <p className="prediction-empty">
          {isLoadingAny ? "Loading model forecasts..." : "No forecast points are available for this model."}
        </p>
      )}
    </section>
  );
}

function modelPredictionKey(ndc11: string, months: number, model: PredictionModel) {
  return `${ndc11}:${months}:${model}`;
}
