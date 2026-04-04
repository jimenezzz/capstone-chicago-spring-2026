import DataTable from "../components/DataTable";
import { fetchApi } from "../../lib/api";

type SearchParams = { [key: string]: string | string[] | undefined };

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

export default async function NdcPage({ searchParams }: { searchParams?: SearchParams }) {
  const ndc11 = first(searchParams?.ndc11) ?? "";
  const asOfDate = first(searchParams?.as_of_date) ?? "";
  const mode = first(searchParams?.mode) ?? "overview";

  const path =
    mode === "nadac" && ndc11
      ? `/ndc/${encodeURIComponent(ndc11)}/pricing/nadac`
      : ndc11
        ? `/ndc/${encodeURIComponent(ndc11)}`
        : null;

  const response = path ? await fetchApi<unknown>(path, { as_of_date: asOfDate }) : null;

  return (
    <main>
      <section className="section-card">
        <form className="query-form">
          <label>
            NDC11
            <input name="ndc11" defaultValue={ndc11} placeholder="00000000000" required />
          </label>
          <label>
            View
            <select name="mode" defaultValue={mode}>
              <option value="overview">Overview</option>
              <option value="nadac">NADAC history</option>
            </select>
          </label>
          <label>
            As-of date
            <input name="as_of_date" type="date" defaultValue={asOfDate} />
          </label>
          <button type="submit">Run query</button>
        </form>
      </section>

      {response && (
        <section className="section-card">
          {!response.ok && <div className="error-box">{response.error}</div>}
          <DataTable
            data={response.data ?? []}
            title={mode === "nadac" ? "NADAC pricing history" : "NDC overview"}
            fileName={`ndc-${mode}.csv`}
          />
        </section>
      )}
    </main>
  );
}
