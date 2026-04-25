import DataTable from "../components/DataTable";
import NadacPricingDashboard, {
  type NadacHistoryPoint,
  type NadacStats,
} from "../components/NadacPricingDashboard";
import NdcPredictionPanel from "../components/NdcPredictionPanel";
import { fetchApi } from "../../lib/api";

type SearchParams = { [key: string]: string | string[] | undefined };

type NdcOverview = {
  brand_name?: string | null;
  generic_name?: string | null;
};

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
  const statsResponse =
    mode === "nadac" && ndc11
      ? await fetchApi<NadacStats>(`/ndc/${encodeURIComponent(ndc11)}/pricing/nadac/stats`, {
          as_of_date: asOfDate,
        })
      : null;
  const overviewResponse =
    mode === "nadac" && ndc11
      ? await fetchApi<NdcOverview>(`/ndc/${encodeURIComponent(ndc11)}`, {
          as_of_date: asOfDate,
        })
      : null;
  const nadacRows = response?.ok && Array.isArray(response.data) ? response.data : [];
  const hasNadacRows = nadacRows.length > 0;

  return (
    <main>
      <section className="section-card ndc-query-banner">
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
          <button type="submit">Search</button>
        </form>
      </section>

      {response && (
        <>
          {!response.ok && (
            <section className="section-card">
              <div className="error-box">{response.error}</div>
            </section>
          )}

          {mode === "nadac" && response.ok ? (
            <>
              {hasNadacRows && (
                <NadacPricingDashboard
                  history={nadacRows as NadacHistoryPoint[]}
                  stats={statsResponse?.ok ? statsResponse.data : null}
                  genericName={overviewResponse?.ok ? overviewResponse.data?.generic_name : null}
                />
              )}
              {statsResponse && !statsResponse.ok && (
                <section className="section-card">
                  <div className="error-box">{statsResponse.error}</div>
                </section>
              )}
              {hasNadacRows && <NdcPredictionPanel ndc11={ndc11} months={12} />}
            </>
          ) : null}

          {response.ok && (
            <section className="section-card">
              <DataTable
                data={response.data ?? []}
                title={mode === "nadac" ? undefined : "NDC overview"}
                fileName={`ndc-${mode}.csv`}
              />
            </section>
          )}
        </>
      )}
    </main>
  );
}
