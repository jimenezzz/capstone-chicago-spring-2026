import DataTable from "../components/DataTable";
import { fetchApi } from "../../lib/api";

type SearchParams = { [key: string]: string | string[] | undefined };

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

type Dataset = "cms-pricing" | "nadac" | "openfda" | "orange-book" | "purple-book" | "master-dataframe";
type Mode = "raw" | "exact";

function endpointFor(mode: Mode, dataset: Dataset) {
  if (dataset === "master-dataframe") {
    return mode === "exact" ? "/samples/exact/master-dataframe" : "/samples/master-dataframe";
  }
  return `/samples/${mode}/${dataset}`;
}

export default async function SamplesPage({ searchParams }: { searchParams?: SearchParams }) {
  const mode = (first(searchParams?.mode) as Mode | undefined) ?? "raw";
  const dataset = (first(searchParams?.dataset) as Dataset | undefined) ?? "cms-pricing";
  const n = first(searchParams?.n) ?? "100";
  const filterKey = first(searchParams?.filter_key) ?? "";
  const filterValue = first(searchParams?.filter_value) ?? "";
  const shouldQuery = first(searchParams?.run) === "1";

  const query: Record<string, string | undefined> = { n };
  if (mode === "exact" && filterKey && filterValue) {
    query[filterKey] = filterValue;
  }

  const path = endpointFor(mode, dataset);
  const response = shouldQuery ? await fetchApi<unknown>(path, query) : null;

  return (
    <main>
      <section className="section-card">
        <h2>Dataset Explorer</h2>
        <form className="query-form">
          <input type="hidden" name="run" value="1" />

          <label>
            Mode
            <select name="mode" defaultValue={mode}>
              <option value="raw">Random sample</option>
              <option value="exact">Exact match sample</option>
            </select>
          </label>

          <label>
            Dataset
            <select name="dataset" defaultValue={dataset}>
              <option value="cms-pricing">CMS pricing</option>
              <option value="nadac">NADAC</option>
              <option value="openfda">OpenFDA</option>
              <option value="orange-book">Orange Book</option>
              <option value="purple-book">Purple Book</option>
              <option value="master-dataframe">Master dataframe</option>
            </select>
          </label>

          <label>
            Rows
            <input name="n" type="number" min={1} max={1000} defaultValue={n} />
          </label>

          <label>
            Filter field (exact mode)
            <input name="filter_key" defaultValue={filterKey} placeholder="ndc11" />
          </label>

          <label>
            Filter value (exact mode)
            <input name="filter_value" defaultValue={filterValue} placeholder="00000000000" />
          </label>

          <button type="submit">Load dataset</button>
        </form>
      </section>

      {response && (
        <section className="section-card">
          {!response.ok && <div className="error-box">{response.error}</div>}
          <DataTable data={response.data ?? []} title="Sample records" fileName={`${dataset}-${mode}.csv`} />
        </section>
      )}
    </main>
  );
}
