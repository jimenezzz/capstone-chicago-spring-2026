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
  latest_price: string | number | null;
  latest_effective_date: string | null;
  earliest_effective_date: string | null;
  point_count: number;
  raw_record_count: number;
  price_range: string | number | null;
  latest_mom_change: string | number | null;
  latest_mom_change_pct: string | number | null;
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

function PriceLineChart({
  points,
  valueLabel,
}: {
  points: Array<{ label: string; value: number }>;
  valueLabel: string;
}) {
  const width = 760;
  const height = 270;
  const padding = { top: 28, right: 36, bottom: 44, left: 92 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const values = points.map((point) => point.value);
  const min = values.length ? Math.min(...values) : 0;
  const max = values.length ? Math.max(...values) : 1;
  const span = max - min || 1;

  const coords = points.map((point, index) => ({
    ...point,
    x: padding.left + (points.length > 1 ? (index / (points.length - 1)) * chartWidth : chartWidth / 2),
    y: padding.top + chartHeight - ((point.value - min) / span) * chartHeight,
  }));

  const line = coords
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
    .join(" ");
  const area = coords.length
    ? `${line} L ${coords[coords.length - 1].x.toFixed(2)} ${padding.top + chartHeight} L ${coords[0].x.toFixed(2)} ${padding.top + chartHeight} Z`
    : "";
  const ticks = Array.from({ length: 4 }, (_, index) => min + (span / 3) * index);
  const labelCount = Math.min(5, coords.length);
  const xAxisLabelIndexes = new Set(
    Array.from({ length: labelCount }, (_, index) =>
      labelCount <= 1 ? 0 : Math.round((index * (coords.length - 1)) / (labelCount - 1)),
    ),
  );

  if (points.length === 0) {
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
        <path className="chart-area" d={area} />
        <path className="chart-line" d={line} />
        {coords.map((point, index) => {
          const tooltipWidth = 142;
          const tooltipHeight = 44;
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
            </g>
          </g>
          );
        })}
        {coords
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
}: {
  history: NadacHistoryPoint[];
  stats: NadacStats | null;
}) {
  const historyPoints = history
    .filter((row) => row.effective_date && toNumber(row.nadac_price) !== null)
    .map((row) => ({ label: row.effective_date as string, value: toNumber(row.nadac_price) as number }))
    .reverse();
  const monthlyValues =
    stats?.monthly
      .map((point) => toNumber(point.average_price))
      .filter((value): value is number => value !== null) ?? [];
  const summary = stats?.summary;
  const latestTone = trendClass(summary?.latest_mom_change_pct);

  const cards = [
    { label: "Latest", value: formatCurrency(summary?.latest_price), delta: summary?.latest_effective_date ?? "-" },
    { label: "Average", value: formatCurrency(summary?.average_price), delta: `${formatNumber(summary?.point_count ?? 0)} points` },
    { label: "Median", value: formatCurrency(summary?.median_price), delta: `${formatNumber(summary?.raw_record_count ?? 0)} raw rows` },
    { label: "MoM change", value: formatCurrency(summary?.latest_mom_change), delta: formatPercent(summary?.latest_mom_change_pct), tone: latestTone },
  ];

  return (
    <section className="analytics-band">
      <div className="metric-strip">
        {cards.map((card) => (
          <article className="stat-card" key={card.label}>
            <div>
              <p className="stat-label">{card.label}</p>
              <p className="stat-value">{card.value}</p>
              <p className={`stat-delta ${card.tone ?? "neutral"}`}>{card.delta}</p>
            </div>
            <TinySparkline values={monthlyValues} tone={(card.tone as "up" | "down" | "neutral") ?? "neutral"} />
          </article>
        ))}
      </div>

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
          </div>
        </article>
      </div>
    </section>
  );
}

export { PriceLineChart, formatCurrency, toNumber };
