"use client";

import { useMemo, useState } from "react";

type Dataset = "cms-pricing" | "nadac" | "openfda" | "orange-book" | "purple-book" | "master-dataframe";
type Mode = "raw" | "exact";

type FilterRow = {
  field: string;
  value: string;
};

export default function SamplesQueryForm({
  initialMode,
  initialDataset,
  initialN,
  initialFilters,
}: {
  initialMode: Mode;
  initialDataset: Dataset;
  initialN: string;
  initialFilters: FilterRow[];
}) {
  const [mode, setMode] = useState<Mode>(initialMode);
  const [filters, setFilters] = useState<FilterRow[]>(
    initialFilters.length > 0 ? initialFilters : [{ field: "", value: "" }],
  );

  const visibleFilters = useMemo(
    () => filters.filter((item) => item.field.trim() || item.value.trim()),
    [filters],
  );

  const addFilter = () => {
    setFilters((prev) => [...prev, { field: "", value: "" }]);
  };

  const removeFilter = (index: number) => {
    setFilters((prev) => {
      const next = prev.filter((_, idx) => idx !== index);
      return next.length > 0 ? next : [{ field: "", value: "" }];
    });
  };

  const updateFilter = (index: number, patch: Partial<FilterRow>) => {
    setFilters((prev) => prev.map((item, idx) => (idx === index ? { ...item, ...patch } : item)));
  };

  return (
    <form className="query-form">
      <input type="hidden" name="run" value="1" />

      <label>
        Mode
        <select name="mode" value={mode} onChange={(e) => setMode(e.target.value as Mode)}>
          <option value="raw">Random sample</option>
          <option value="exact">Exact match sample</option>
        </select>
      </label>

      <label>
        Dataset
        <select name="dataset" defaultValue={initialDataset}>
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
        <input name="n" type="number" min={1} max={1000} defaultValue={initialN} />
      </label>

      {mode === "exact" && (
        <div className="filter-builder">
          <div className="filter-builder-head">
            <p>Exact-match filters</p>
            <button type="button" className="btn-inline" onClick={addFilter}>
              Add filter
            </button>
          </div>

          {filters.map((filter, index) => (
            <div className="filter-row" key={`filter-${index}`}>
              <label>
                Field
                <input
                  name={`filter_field_${index}`}
                  value={filter.field}
                  onChange={(e) => updateFilter(index, { field: e.target.value })}
                  placeholder="e.g. ndc11"
                />
              </label>
              <label>
                Value
                <input
                  name={`filter_value_${index}`}
                  value={filter.value}
                  onChange={(e) => updateFilter(index, { value: e.target.value })}
                  placeholder="exact value"
                />
              </label>
              <button type="button" className="btn-inline btn-danger" onClick={() => removeFilter(index)}>
                Remove
              </button>
            </div>
          ))}

          <p className="muted filter-count">{visibleFilters.length} active filter(s)</p>
        </div>
      )}

      <button type="submit">Load dataset</button>
    </form>
  );
}
