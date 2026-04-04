import { fetchApi } from "../lib/api";
import { SessionUser } from "../lib/auth";

export default async function DashboardPage() {
  const [health, asOfDates, me] = await Promise.all([
    fetchApi<{ status: string }>("/health"),
    fetchApi<Array<{ source_name: string; as_of_date: string }>>("/meta/as-of-dates"),
    fetchApi<SessionUser>("/auth/me"),
  ]);

  return (
    <main>
      <section className="section-stack">
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
            <p className="metric-label">Signed in as</p>
            <p className="metric-value">{me.data?.username ?? "unknown"}</p>
            <p className="muted">Role: {me.data?.role ?? "unknown"}</p>
          </article>
        </div>
      </section>

      <section className="section-stack">
        <h2 className="section-title-soft section-title-compact">Operational notes</h2>
        <div className="kpi-badges">
          <span className="badge high">Bearer sessions expire after 60 minutes</span>
          <span className="badge medium">Viewer role covers all analysis pages</span>
          <span className="badge medium">Admin role unlocks user management</span>
          <span className="badge low">Pipeline controls can extend the admin tab</span>
        </div>
      </section>
    </main>
  );
}
