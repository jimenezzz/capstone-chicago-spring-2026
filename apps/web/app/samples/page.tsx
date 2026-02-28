import DataTable from "../components/DataTable";
import SamplesQueryForm from "../components/SamplesQueryForm";
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
  const shouldQuery = first(searchParams?.run) === "1";

  const filtersByIndex = new Map<number, { field?: string; value?: string }>();
  for (const [key, val] of Object.entries(searchParams ?? {})) {
    const fieldMatch = key.match(/^filter_field_(\d+)$/);
    const valueMatch = key.match(/^filter_value_(\d+)$/);
    if (fieldMatch) {
      const idx = Number(fieldMatch[1]);
      const entry = filtersByIndex.get(idx) ?? {};
      entry.field = first(val) ?? "";
      filtersByIndex.set(idx, entry);
    } else if (valueMatch) {
      const idx = Number(valueMatch[1]);
      const entry = filtersByIndex.get(idx) ?? {};
      entry.value = first(val) ?? "";
      filtersByIndex.set(idx, entry);
    }
  }

  // Backward compatibility with old single-filter params.
  if (filtersByIndex.size === 0) {
    const legacyField = first(searchParams?.filter_key) ?? "";
    const legacyValue = first(searchParams?.filter_value) ?? "";
    if (legacyField || legacyValue) {
      filtersByIndex.set(0, { field: legacyField, value: legacyValue });
    }
  }

  const filterRows = Array.from(filtersByIndex.entries())
    .sort(([a], [b]) => a - b)
    .map(([, item]) => ({
      field: item.field ?? "",
      value: item.value ?? "",
    }));

  const query: Record<string, string | undefined> = { n };
  if (mode === "exact") {
    for (const row of filterRows) {
      const field = row.field.trim();
      const value = row.value.trim();
      if (field && value) {
        query[field] = value;
      }
    }
  }

  const path = endpointFor(mode, dataset);
  const response = shouldQuery ? await fetchApi<unknown>(path, query) : null;

  return (
    <main>
      <section className="section-card">
        <h2>Dataset Explorer</h2>
        <SamplesQueryForm
          initialMode={mode}
          initialDataset={dataset}
          initialN={n}
          initialFilters={filterRows}
        />
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
