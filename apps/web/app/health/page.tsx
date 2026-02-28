import DataTable from "../components/DataTable";
import { fetchApi } from "../../lib/api";

export default async function HealthPage() {
  const health = await fetchApi<{ status: string }>("/health");

  return (
    <main>
      <section className="section-card">
        <h2>System Health</h2>
        <p className="muted">Operational check for API availability and response status.</p>
      </section>

      <section className="section-card">
        {!health.ok && <div className="error-box">{health.error}</div>}
        <DataTable
          data={[
            {
              status: health.data?.status ?? "unknown",
              available: health.ok,
              response_status: health.status,
              checked_url: health.url,
              checked_at: new Date().toISOString(),
            },
          ]}
          title="Health check"
          fileName="health-check.csv"
        />
      </section>
    </main>
  );
}
