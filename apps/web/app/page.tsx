import Link from "next/link";

import { fetchApi } from "../lib/api";

export default async function DashboardPage() {
  const [health, asOfDates] = await Promise.all([
    fetchApi<{ status: string }>("/health"),
    fetchApi<Array<{ source_name: string; as_of_date: string }>>("/meta/as-of-dates"),
  ]);

  return (
    <main>
      <section className="section-card">
        <h2>Workspace snapshot</h2>
        <div className="grid-4">
          <article className="metric-box">
            <p className="metric-label">API status</p>
            <p className="metric-value">
              <span className={`status-pill ${health.ok ? "ok" : "err"}`}>{health.ok ? "Online" : "Offline"}</span>
            </p>
          </article>
          <article className="metric-box">
            <p className="metric-label">Source snapshots</p>
            <p className="metric-value">{asOfDates.data?.length ?? 0}</p>
          </article>
          <article className="metric-box">
            <p className="metric-label">Primary flows</p>
            <p className="metric-value">3</p>
          </article>
          <article className="metric-box">
            <p className="metric-label">Roadmap</p>
            <p className="muted">Models, Admin, Auth (planned)</p>
          </article>
        </div>
      </section>

      <section className="section-card">
        <h3>Analyst flows</h3>
        <div className="grid-4">
          <article className="metric-box">
            <p className="metric-label">NDC Analysis</p>
            <p>
              <Link href="/ndc">Open page</Link>
            </p>
          </article>
          <article className="metric-box">
            <p className="metric-label">CMS Analysis</p>
            <p>
              <Link href="/cms">Open page</Link>
            </p>
          </article>
          <article className="metric-box">
            <p className="metric-label">Dataset Explorer</p>
            <p>
              <Link href="/samples">Open page</Link>
            </p>
          </article>
          <article className="metric-box">
            <p className="metric-label">Data Freshness</p>
            <p>
              <Link href="/meta">Open page</Link>
            </p>
          </article>
        </div>
      </section>

      <section className="section-card">
        <h3>Improvement tips</h3>
        <div className="kpi-badges">
          <span className="badge high">Optimize query filters</span>
          <span className="badge medium">Reduce large pulls</span>
          <span className="badge medium">Use ranking for outliers</span>
          <span className="badge low">Export CSV for sharing</span>
        </div>
      </section>
    </main>
  );
}
