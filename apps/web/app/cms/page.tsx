import DataTable from "../components/DataTable";
import { fetchApi } from "../../lib/api";

type SearchParams = { [key: string]: string | string[] | undefined };

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

function buildCmsTarget(mode: string, ndc11: string, hcpcs: string) {
  switch (mode) {
    case "crosswalk-ndc":
      return ndc11 ? { path: `/cms/crosswalk/ndc/${encodeURIComponent(ndc11)}` } : null;
    case "crosswalk-hcpcs":
      return hcpcs ? { path: `/cms/crosswalk/hcpcs/${encodeURIComponent(hcpcs)}` } : null;
    case "pricing-hcpcs":
      return hcpcs ? { path: `/cms/pricing/hcpcs/${encodeURIComponent(hcpcs)}` } : null;
    case "pricing-ndc":
      return ndc11 ? { path: `/cms/pricing/ndc/${encodeURIComponent(ndc11)}` } : null;
    case "pricing-query":
      return { path: "/cms/pricing" };
    default:
      return null;
  }
}

export default async function CmsPage({ searchParams }: { searchParams?: SearchParams }) {
  const mode = first(searchParams?.mode) ?? "crosswalk-ndc";
  const ndc11 = first(searchParams?.ndc11) ?? "";
  const hcpcs = first(searchParams?.hcpcs) ?? "";
  const asOfDate = first(searchParams?.as_of_date) ?? "";

  const target = buildCmsTarget(mode, ndc11, hcpcs);
  const response = target ? await fetchApi<unknown>(target.path, { ndc11, hcpcs, as_of_date: asOfDate }) : null;

  return (
    <main>
      <section className="section-card">
        <h2>CMS Analysis</h2>
        <form className="query-form">
          <label>
            Route
            <select name="mode" defaultValue={mode}>
              <option value="crosswalk-ndc">Crosswalk by NDC</option>
              <option value="crosswalk-hcpcs">Crosswalk by HCPCS</option>
              <option value="pricing-hcpcs">Pricing by HCPCS</option>
              <option value="pricing-ndc">Pricing by NDC</option>
              <option value="pricing-query">Flexible pricing query</option>
            </select>
          </label>
          <label>
            NDC11
            <input name="ndc11" defaultValue={ndc11} placeholder="00000000000" />
          </label>
          <label>
            HCPCS
            <input name="hcpcs" defaultValue={hcpcs} placeholder="J0000" />
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
          <DataTable data={response.data ?? []} title="CMS result set" fileName="cms-results.csv" />
        </section>
      )}
    </main>
  );
}
