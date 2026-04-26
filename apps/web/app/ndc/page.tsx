import DataTable from "../components/DataTable";
import NadacPricingDashboard, {
  type NadacHistoryPoint,
  type NadacStats,
} from "../components/NadacPricingDashboard";
import { NadacSearchHistoryRecorder } from "../components/NadacSearchHistory";
import NdcPredictionPanel from "../components/NdcPredictionPanel";
import { fetchApi } from "../../lib/api";

type SearchParams = { [key: string]: string | string[] | undefined };

type NdcOverview = {
  brand_name?: string | null;
  generic_name?: string | null;
};

type NdcSearchResult = {
  ndc11: string;
  brand_name?: string | null;
  generic_name?: string | null;
  ndc_description?: string | null;
  latest_nadac_price?: string | number | null;
  latest_effective_date?: string | null;
  as_of_date?: string | null;
};

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

function nadacHistoryHref(ndc11: string, asOfDate: string) {
  const params = new URLSearchParams({ ndc11, mode: "nadac" });
  if (asOfDate) {
    params.set("as_of_date", asOfDate);
  }
  return `/ndc?${params.toString()}`;
}

export default async function NdcPage({ searchParams }: { searchParams?: SearchParams }) {
  const ndc11 = first(searchParams?.ndc11) ?? "";
  const drugName = first(searchParams?.drug_name) ?? "";
  const asOfDate = first(searchParams?.as_of_date) ?? "";
  const mode = first(searchParams?.mode) ?? "nadac";

  const path =
    mode === "nadac" && ndc11
      ? `/ndc/${encodeURIComponent(ndc11)}/pricing/nadac`
      : ndc11
        ? `/ndc/${encodeURIComponent(ndc11)}`
        : null;

  const response = path ? await fetchApi<unknown>(path, { as_of_date: asOfDate }) : null;
  const nameSearchResponse =
    drugName.trim().length >= 2
      ? await fetchApi<NdcSearchResult[]>("/ndc/search", {
          name: drugName,
          as_of_date: asOfDate,
        })
      : null;
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
        <div className="ndc-query-grid">
          <form className="query-form">
            <label>
              NDC11
              <input name="ndc11" defaultValue={ndc11} placeholder="00000000000" required />
            </label>
            <label>
              View
              <select name="mode" defaultValue={mode}>
                <option value="nadac">NADAC history</option>
                <option value="overview">Overview</option>
              </select>
            </label>
            <label>
              As-of date
              <input name="as_of_date" type="date" defaultValue={asOfDate} />
            </label>
            <button type="submit">Search NDC</button>
          </form>

          <form className="query-form ndc-name-search-form">
            <label>
              Drug name
              <input name="drug_name" defaultValue={drugName} placeholder="atorvastatin" minLength={2} />
            </label>
            <label>
              As-of date
              <input name="as_of_date" type="date" defaultValue={asOfDate} />
            </label>
            <button type="submit">Search by name</button>
          </form>
        </div>
      </section>

      {drugName.trim().length === 1 && (
        <section className="section-card">
          <p className="empty-state">Enter at least 2 characters to search by drug name.</p>
        </section>
      )}

      {nameSearchResponse && (
        <section className="section-card">
          <h3>Drug name matches</h3>
          {!nameSearchResponse.ok && <div className="error-box">{nameSearchResponse.error}</div>}
          {nameSearchResponse.ok && (nameSearchResponse.data?.length ?? 0) === 0 && (
            <p className="empty-state">No drugs matched that name search.</p>
          )}
          {nameSearchResponse.ok && (nameSearchResponse.data?.length ?? 0) > 0 && (
            <DataTable
              data={nameSearchResponse.data?.map((row) => ({
                ndc11: row.ndc11,
                brand_name: row.brand_name,
                generic_name: row.generic_name,
                ndc_description: row.ndc_description,
                latest_nadac_price: row.latest_nadac_price,
                latest_effective_date: row.latest_effective_date,
                history: nadacHistoryHref(row.ndc11, asOfDate),
              }))}
              fileName="ndc-name-search.csv"
            />
          )}
        </section>
      )}

      {response && (
        <>
          {!response.ok && (
            <section className="section-card">
              <div className="error-box">{response.error}</div>
            </section>
          )}

          {mode === "nadac" && response.ok ? (
            <>
              <NadacSearchHistoryRecorder
                ndc11={ndc11}
                asOfDate={asOfDate}
                genericName={overviewResponse?.ok ? overviewResponse.data?.generic_name : null}
                latestPrice={statsResponse?.ok ? statsResponse.data?.summary.latest_price : null}
                latestEffectiveDate={statsResponse?.ok ? statsResponse.data?.summary.latest_effective_date : null}
                resultCount={nadacRows.length}
              />
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
              {hasNadacRows && (
                <NdcPredictionPanel
                  ndc11={ndc11}
                  months={12}
                  history={nadacRows as NadacHistoryPoint[]}
                />
              )}
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
