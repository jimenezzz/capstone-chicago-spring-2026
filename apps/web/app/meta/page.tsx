import DataTable from "../components/DataTable";
import { fetchApi } from "../../lib/api";

export default async function MetaPage() {
  const response = await fetchApi<Array<{ source_name: string; as_of_date: string }>>("/meta/as-of-dates");

  return (
    <main>
      <section className="section-card">
        <h2>Data Freshness</h2>
        <p className="muted">Snapshot dates available by source.</p>
      </section>

      <section className="section-card">
        {!response.ok && <div className="error-box">{response.error}</div>}
        <DataTable data={response.data ?? []} title="As-of date inventory" fileName="as-of-dates.csv" />
      </section>
    </main>
  );
}
