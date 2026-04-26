export type NadacHistoryPoint = {
  as_of_date: string;
  effective_date: string | null;
  nadac_price: string | number | null;
  record_count?: number;
};

type MonthlyPoint = {
  month: string;
  average_price: string | number;
  min_price: string | number;
  max_price: string | number;
  median_price: string | number;
  point_count: number;
  mom_change: string | number | null;
  mom_change_pct: string | number | null;
};

type StatsSummary = {
  min_price: string | number | null;
  max_price: string | number | null;
  average_price: string | number | null;
  median_price: string | number | null;
  price_std_dev: string | number | null;
  latest_price: string | number | null;
  latest_effective_date: string | null;
  earliest_effective_date: string | null;
  point_count: number;
  raw_record_count: number;
  price_range: string | number | null;
  total_change_pct: string | number | null;
  latest_mom_change: string | number | null;
  latest_mom_change_pct: string | number | null;
  volatility_threshold_pct: string | number;
  moderate_risk_months: number;
  high_risk_months: number;
  volatile_month_count: number;
  max_positive_spike_pct: string | number | null;
  max_negative_drop_pct: string | number | null;
  stability_label: "Stable" | "Moderate Risk" | "High Risk" | string;
};

export type NadacStats = {
  ndc11: string;
  summary: StatsSummary;
  monthly: MonthlyPoint[];
};

function toNumber(value: string | number | null | undefined) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatCurrency(value: string | number | null | undefined) {
  const parsed = toNumber(value);
  if (parsed === null) return "-";
  return parsed.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: parsed >= 10 ? 2 : 4,
    maximumFractionDigits: 6,
  });
}

function formatNumber(value: number) {
  return value.toLocaleString("en-US");
}

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

function riskTone(label: string | null | undefined) {
  if (label === "High Risk") return "high";
  if (label === "Moderate Risk") return "moderate";
  return "stable";
}

function sparkPath(values: number[], width: number, height: number) {
  if (values.length === 0) return "";
  if (values.length === 1) return `M 0 ${height / 2} L ${width} ${height / 2}`;

  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  return values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * width;
      const y = height - ((value - min) / span) * height;
      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");
}

function areaPath(linePath: string, width: number, height: number) {
  if (!linePath) return "";
  return `${linePath} L ${width} ${height} L 0 ${height} Z`;
}

function TinySparkline({ values, tone }: { values: number[]; tone: "up" | "down" | "neutral" }) {
  const width = 112;
  const height = 54;
  const path = sparkPath(values, width, height);
  return (
    <svg className={`mini-spark ${tone}`} viewBox={`0 0 ${width} ${height}`} role="img">
      <path className="mini-spark-area" d={areaPath(path, width, height)} />
      <path className="mini-spark-line" d={path} />
    </svg>
  );
}

function valuesAroundTarget(values: number[], target: string | number | null | undefined, centerTarget = false) {
  const parsedTarget = toNumber(target);
  if (values.length <= 5) return values;
  if (parsedTarget === null) return values.slice(0, 5);

  let selectedIndex = 0;

  if (centerTarget) {
    selectedIndex = values.reduce((bestIndex, value, index) => (
      Math.abs(value - parsedTarget) < Math.abs(values[bestIndex] - parsedTarget) ? index : bestIndex
    ), 0);
  } else {
    selectedIndex = values.findIndex((value, index) => {
      if (index === 0) return value === parsedTarget;
      const previous = values[index - 1];
      return (previous <= parsedTarget && value >= parsedTarget) || (previous >= parsedTarget && value <= parsedTarget);
    });

    if (selectedIndex === -1) {
      selectedIndex = values.reduce((bestIndex, value, index) => (
        Math.abs(value - parsedTarget) < Math.abs(values[bestIndex] - parsedTarget) ? index : bestIndex
      ), 0);
    }
  }

  const start = Math.min(Math.max(0, selectedIndex - 2), Math.max(0, values.length - 5));
  return values.slice(start, start + 5);
}

function PriceLineChart({
  points,
  valueLabel,
  comparisonPoints = [],
}: {
  points: Array<{ label: string; value: number; changePct?: number | null }>;
  valueLabel: string;
  comparisonPoints?: Array<{ label: string; value: number; changePct?: number | null }>;
}) {
  const width = 760;
  const height = 270;
  const padding = { top: 28, right: 36, bottom: 44, left: 92 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const allPoints = [...comparisonPoints, ...points];
  const values = allPoints.map((point) => point.value);
  const min = values.length ? Math.min(...values) : 0;
  const max = values.length ? Math.max(...values) : 1;
  const span = max - min || 1;

  const toCoords = (series: Array<{ label: string; value: number; changePct?: number | null }>, startIndex = 0) =>
    series.map((point, index) => ({
    ...point,
    x: padding.left + (
      allPoints.length > 1
        ? ((startIndex + index) / (allPoints.length - 1)) * chartWidth
        : chartWidth / 2
    ),
    y: padding.top + chartHeight - ((point.value - min) / span) * chartHeight,
  }));

  const coords = toCoords(points, comparisonPoints.length);
  const comparisonCoords = toCoords(comparisonPoints);

  const lineFromCoords = (seriesCoords: typeof coords) => seriesCoords
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
    .join(" ");

  const areaFromCoords = (seriesCoords: typeof coords, linePath: string) => seriesCoords.length
    ? `${linePath} L ${seriesCoords[seriesCoords.length - 1].x.toFixed(2)} ${padding.top + chartHeight} L ${seriesCoords[0].x.toFixed(2)} ${padding.top + chartHeight} Z`
    : "";
  const predictionDisplayCoords =
    comparisonCoords.length > 0 && coords.length > 0
      ? [comparisonCoords[comparisonCoords.length - 1], ...coords]
      : coords;
  const line = lineFromCoords(predictionDisplayCoords);
  const area = areaFromCoords(predictionDisplayCoords, line);
  const comparisonLine = lineFromCoords(comparisonCoords);
  const comparisonArea = areaFromCoords(comparisonCoords, comparisonLine);
  const ticks = Array.from({ length: 4 }, (_, index) => min + (span / 3) * index);
  const axisCoords = [...comparisonCoords, ...coords];
  const labelCount = Math.min(5, axisCoords.length);
  const xAxisLabelIndexes = new Set(
    Array.from({ length: labelCount }, (_, index) =>
      labelCount <= 1 ? 0 : Math.round((index * (axisCoords.length - 1)) / (labelCount - 1)),
    ),
  );

  if (allPoints.length === 0) {
    return <p className="empty-state">No price points available for charting.</p>;
  }

  return (
    <div className="price-chart-shell">
      <svg className="price-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={valueLabel}>
        {ticks.map((tick) => {
          const y = padding.top + chartHeight - ((tick - min) / span) * chartHeight;
          return (
            <g key={tick}>
              <line x1={padding.left} x2={width - padding.right} y1={y} y2={y} className="chart-grid" />
              <text x={padding.left - 14} y={y + 4} className="chart-axis" textAnchor="end">
                {formatCurrency(tick)}
              </text>
            </g>
          );
        })}
        {comparisonCoords.length > 0 && (
          <>
            <path className="chart-area chart-area-muted" d={comparisonArea} />
            <path className="chart-line chart-line-muted" d={comparisonLine} />
          </>
        )}
        <path className="chart-area" d={area} />
        <path className="chart-line" d={line} />
        {comparisonCoords.map((point, index) => (
          <g className="chart-point chart-point-muted" key={`history-${point.label}-${index}`} tabIndex={0}>
            <circle cx={point.x} cy={point.y} r="13" className="chart-hit-area" />
            <circle cx={point.x} cy={point.y} r="4.5" className="chart-dot chart-dot-muted" />
          </g>
        ))}
        {coords.map((point, index) => {
          const tooltipWidth = 158;
          const tooltipHeight = 60;
          const tooltipX = Math.min(
            width - tooltipWidth - 8,
            Math.max(8, point.x - tooltipWidth / 2),
          );
          const tooltipY = point.y > 72 ? point.y - tooltipHeight - 14 : point.y + 16;

          return (
          <g className="chart-point" key={`${point.label}-${index}`} tabIndex={0}>
            <circle cx={point.x} cy={point.y} r="13" className="chart-hit-area" />
            <circle cx={point.x} cy={point.y} r="4.5" className="chart-dot" />
            <g className="chart-tooltip" pointerEvents="none">
              <rect
                x={tooltipX}
                y={tooltipY}
                width={tooltipWidth}
                height={tooltipHeight}
                rx="8"
                className="chart-tooltip-box"
              />
              <text x={tooltipX + 12} y={tooltipY + 17} className="chart-tooltip-label">
                {point.label}
              </text>
              <text x={tooltipX + 12} y={tooltipY + 34} className="chart-tooltip-value">
                {formatCurrency(point.value)}
              </text>
              <text x={tooltipX + 12} y={tooltipY + 50} className={`chart-tooltip-change ${trendClass(point.changePct)}`}>
                MoM {formatPercent(point.changePct)}
              </text>
            </g>
          </g>
          );
        })}
        {axisCoords
          .filter((_, index) => xAxisLabelIndexes.has(index))
          .map((point) => (
            <text key={point.label} x={point.x} y={height - 14} className="chart-axis" textAnchor="middle">
              {point.label}
            </text>
          ))}
      </svg>
    </div>
  );
}

export default function NadacPricingDashboard({
  history,
  stats,
  brandName,
  genericName,
}: {
  history: NadacHistoryPoint[];
  stats: NadacStats | null;
  brandName?: string | null;
  genericName?: string | null;
}) {
  const historyPoints = history
    .filter((row) => row.effective_date && toNumber(row.nadac_price) !== null)
    .map((row) => ({ label: row.effective_date as string, value: toNumber(row.nadac_price) as number }))
    .reverse()
    .map((point, index, points) => {
      const previous = points[index - 1];
      const changePct = previous && previous.value !== 0 ? ((point.value - previous.value) / previous.value) * 100 : null;
      return { ...point, changePct };
    });
  const monthlyValues =
    stats?.monthly
      .map((point) => toNumber(point.average_price))
      .filter((value): value is number => value !== null) ?? [];
  const summary = stats?.summary;
  const latestTone = trendClass(summary?.latest_mom_change_pct);
  const latestSparkValues = monthlyValues.slice(-5);
  const averageSparkValues = valuesAroundTarget(monthlyValues, summary?.average_price);
  const medianSparkValues = valuesAroundTarget(monthlyValues, summary?.median_price, true);
  const drugTitle = genericName || stats?.ndc11;
  const drugSubtitle = genericName ? "Generic name" : "NDC";
  const risk = {
    label: summary?.stability_label ?? "Stable",
    tone: riskTone(summary?.stability_label),
    threshold: formatPercent(summary?.volatility_threshold_pct ?? 5).replace("+", ""),
    volatileMonths: summary?.volatile_month_count ?? 0,
    positiveSpike: formatPercent(summary?.max_positive_spike_pct),
    negativeDrop: formatPercent(summary?.max_negative_drop_pct),
    standardDeviation: formatCurrency(summary?.price_std_dev),
  };

  const cards = [
    { label: "Latest", value: formatCurrency(summary?.latest_price), delta: summary?.latest_effective_date ?? "-", sparkValues: latestSparkValues },
    { label: "Average", value: formatCurrency(summary?.average_price), delta: `${formatNumber(summary?.point_count ?? 0)} points`, sparkValues: averageSparkValues },
    { label: "Median", value: formatCurrency(summary?.median_price), delta: `${formatNumber(summary?.raw_record_count ?? 0)} raw rows`, sparkValues: medianSparkValues },
    { label: "MoM change", value: formatCurrency(summary?.latest_mom_change), delta: formatPercent(summary?.latest_mom_change_pct), tone: latestTone, sparkValues: monthlyValues },
  ];

  return (
    <section className="analytics-band">
      {brandName && (
        <div className="brand-name-banner">
          <span>Brand name</span>
          <strong>{brandName}</strong>
        </div>
      )}

      {drugTitle && (
        <div className="drug-identity">
          <span>{drugSubtitle}</span>
          <strong>{drugTitle}</strong>
        </div>
      )}

      <div className="metric-strip">
        {cards.map((card) => (
          <article className="stat-card" key={card.label}>
            <div>
              <p className="stat-label">{card.label}</p>
              <p className="stat-value">{card.value}</p>
              <p className={`stat-delta ${card.tone ?? "neutral"}`}>{card.delta}</p>
            </div>
            <TinySparkline values={card.sparkValues} tone={(card.tone as "up" | "down" | "neutral") ?? "neutral"} />
          </article>
        ))}
      </div>

      <article className={`risk-card ${risk.tone}`}>
        <div>
          <p className="stat-label">Risk &amp; Stability</p>
          <strong>{risk.label}</strong>
          <p>
            {formatNumber(risk.volatileMonths)} month{risk.volatileMonths === 1 ? "" : "s"} exceeded the{" "}
            {risk.threshold} volatility threshold.
          </p>
        </div>
        <div className="risk-grid" aria-label="NADAC volatility analytics">
          <div><span>Max spike</span><strong className="value-up">{risk.positiveSpike}</strong></div>
          <div><span>Max drop</span><strong className="value-down">{risk.negativeDrop}</strong></div>
          <div><span>Std. dev.</span><strong>{risk.standardDeviation}</strong></div>
        </div>
      </article>

      <div className="chart-grid-layout">
        <article className="chart-panel chart-panel-wide">
          <div className="chart-panel-head">
            <div>
              <h3>NADAC price history</h3>
              <p>Unique effective-date price points from the NADAC source.</p>
            </div>
            <span>{formatNumber(historyPoints.length)} points</span>
          </div>
          <PriceLineChart points={historyPoints} valueLabel="NADAC price history" />
        </article>

        <article className="chart-panel">
          <div className="chart-panel-head">
            <div>
              <h3>Price spread</h3>
              <p>Minimum, maximum, and range.</p>
            </div>
          </div>
          <div className="spread-list">
            <div><span>Minimum</span><strong>{formatCurrency(summary?.min_price)}</strong></div>
            <div><span>Maximum</span><strong>{formatCurrency(summary?.max_price)}</strong></div>
            <div><span>Range</span><strong>{formatCurrency(summary?.price_range)}</strong></div>
            <div><span>Total change</span><strong className={trendClass(summary?.total_change_pct)}>{formatPercent(summary?.total_change_pct)}</strong></div>
          </div>
        </article>
      </div>
    </section>
  );
}

export { PriceLineChart, formatCurrency, toNumber };
