"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type Row = Record<string, unknown>;

const STOPWORDS = new Set([
  "a",
  "an",
  "and",
  "as",
  "at",
  "by",
  "for",
  "from",
  "in",
  "of",
  "on",
  "or",
  "the",
  "to",
  "with",
]);

const ALWAYS_UPPER = new Set(["ndc", "nadac", "cms", "hcpcs"]);
const CATEGORICAL_COLUMNS = new Set(["hcpcs", "ndcraw", "applicationnumbernorm", "packagendc11"]);
const JSON_TOGGLE_COLUMNS = new Set(["sourcerow"]);
const DATE_COLUMNS = new Set([
  "asofdate",
  "createdat",
  "updatedat",
  "ingestedat",
  "nadacdate",
  "effectivedate",
]);

function toRows(data: unknown): Row[] {
  if (Array.isArray(data)) {
    return data.map((item) => {
      if (item && typeof item === "object" && !Array.isArray(item)) {
        return item as Row;
      }
      return { value: item };
    });
  }

  if (data && typeof data === "object") {
    return [data as Row];
  }

  if (data === null || data === undefined) {
    return [];
  }

  return [{ value: data }];
}

function toCell(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}

function toDisplayCell(value: unknown): string {
  const cell = toCell(value);
  return cell.trim().length === 0 ? "-" : cell;
}

function formatColumnLabel(column: string): string {
  const words = column
    .replaceAll("_", " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  return words
    .map((word, index) => {
      const lower = word.toLowerCase();
      const isMiddle = index > 0 && index < words.length - 1;

      if (ALWAYS_UPPER.has(lower)) {
        return lower.toUpperCase();
      }
      for (const acronym of ALWAYS_UPPER) {
        if (lower.startsWith(acronym)) {
          return `${acronym.toUpperCase()}${word.slice(acronym.length)}`;
        }
      }

      if (isMiddle && STOPWORDS.has(lower)) {
        return lower;
      }

      const first = word.slice(0, 1).toUpperCase();
      const rest = word.slice(1).toLowerCase();
      return `${first}${rest}`;
    })
    .join(" ");
}

function normalizeToken(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function isCategoricalColumn(column: string): boolean {
  return CATEGORICAL_COLUMNS.has(normalizeToken(column));
}

function isJsonToggleColumn(column: string): boolean {
  return JSON_TOGGLE_COLUMNS.has(normalizeToken(column));
}

function isDateColumn(column: string): boolean {
  const token = normalizeToken(column);
  return DATE_COLUMNS.has(token) || token.includes("date");
}

function formatDateOnly(value: unknown): string | null {
  const raw = toCell(value).trim();
  if (!raw) return null;

  // If the value already starts with an ISO date token, use it directly to avoid TZ drift.
  const isoDateMatch = raw.match(/^(\d{4}-\d{2}-\d{2})/);
  if (isoDateMatch) {
    return isoDateMatch[1];
  }

  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return null;

  const yyyy = parsed.getUTCFullYear();
  const mm = String(parsed.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(parsed.getUTCDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function tryFormatJson(value: unknown): { ok: boolean; compact: string; pretty: string } {
  if (value === null || value === undefined) {
    return { ok: false, compact: "", pretty: "" };
  }

  if (typeof value === "object") {
    const pretty = JSON.stringify(value, null, 2);
    return { ok: true, compact: JSON.stringify(value), pretty };
  }

  if (typeof value === "string") {
    const text = value.trim();
    if (!(text.startsWith("{") || text.startsWith("["))) {
      return { ok: false, compact: value, pretty: value };
    }
    try {
      const parsed = JSON.parse(text);
      const pretty = JSON.stringify(parsed, null, 2);
      return { ok: true, compact: JSON.stringify(parsed), pretty };
    } catch {
      return { ok: false, compact: value, pretty: value };
    }
  }

  return { ok: false, compact: toCell(value), pretty: toCell(value) };
}

function hashString(value: string): number {
  let hash = 0;
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash * 31 + value.charCodeAt(i)) >>> 0;
  }
  return hash;
}

function colorForIndex(index: number, seedHue: number): string {
  const hue = (seedHue + index * 137.508) % 360;
  return `hsl(${hue} 68% 82%)`;
}

function textColorForIndex(index: number, seedHue: number): string {
  const hue = (seedHue + index * 137.508) % 360;
  return `hsl(${hue} 52% 20%)`;
}

function compareValues(a: unknown, b: unknown, direction: "asc" | "desc"): number {
  const aText = toCell(a);
  const bText = toCell(b);

  const aNum = Number(aText);
  const bNum = Number(bText);
  const aIsNum = Number.isFinite(aNum) && aText.trim().length > 0;
  const bIsNum = Number.isFinite(bNum) && bText.trim().length > 0;

  const base = aIsNum && bIsNum ? aNum - bNum : aText.localeCompare(bText);
  return direction === "asc" ? base : -base;
}

function downloadCsv(filename: string, columns: string[], rows: Row[]) {
  const escapeCsv = (value: string) => {
    if (value.includes(",") || value.includes("\n") || value.includes("\"")) {
      return `"${value.replaceAll('"', '""')}"`;
    }
    return value;
  };

  const header = columns.map(escapeCsv).join(",");
  const body = rows
    .map((row) => columns.map((col) => escapeCsv(toCell(row[col]))).join(","))
    .join("\n");

  const blob = new Blob([`${header}\n${body}`], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export default function DataTable({
  data,
  title,
  fileName = "results.csv",
}: {
  data: unknown;
  title?: string;
  fileName?: string;
}) {
  const rows = useMemo(() => toRows(data), [data]);

  const columns = useMemo(() => {
    const set = new Set<string>();
    for (const row of rows) {
      Object.keys(row).forEach((key) => set.add(key));
    }
    return Array.from(set);
  }, [rows]);

  const [search, setSearch] = useState("");
  const [filterColumn, setFilterColumn] = useState("");
  const [filterValue, setFilterValue] = useState("");
  const [sortColumn, setSortColumn] = useState("");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const [pageSize, setPageSize] = useState("25");
  const [page, setPage] = useState(1);
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({});
  const [expandedJsonCells, setExpandedJsonCells] = useState<Record<string, boolean>>({});
  const headerRefs = useRef<Record<string, HTMLTableCellElement | null>>({});
  const filterMenuRef = useRef<HTMLDetailsElement>(null);

  useEffect(() => {
    const closeFilterMenu = (event: MouseEvent) => {
      const menu = filterMenuRef.current;
      if (menu?.open && event.target instanceof Node && !menu.contains(event.target)) {
        menu.open = false;
      }
    };

    document.addEventListener("mousedown", closeFilterMenu);
    return () => document.removeEventListener("mousedown", closeFilterMenu);
  }, []);

  const processedRows = useMemo(() => {
    let result = [...rows];

    if (search.trim()) {
      const term = search.trim().toLowerCase();
      result = result.filter((row) =>
        columns.some((col) => toCell(row[col]).toLowerCase().includes(term)),
      );
    }

    if (filterColumn && filterValue.trim()) {
      const term = filterValue.trim().toLowerCase();
      result = result.filter((row) => toCell(row[filterColumn]).toLowerCase().includes(term));
    }

    if (sortColumn) {
      result.sort((a, b) => compareValues(a[sortColumn], b[sortColumn], sortDirection));
    }

    return result;
  }, [rows, search, columns, filterColumn, filterValue, sortColumn, sortDirection]);

  const totalPages = Math.max(1, Math.ceil(processedRows.length / (Math.max(1, Number(pageSize) || 25))));
  const currentPage = Math.min(page, totalPages);

  const pagedRows = useMemo(() => {
    const size = Math.max(1, Number(pageSize) || 25);
    const start = (currentPage - 1) * size;
    return processedRows.slice(start, start + size);
  }, [processedRows, currentPage, pageSize]);

  const categoricalColorMap = useMemo(() => {
    const map = new Map<string, { bg: string; fg: string }>();
    const seen = new Set<string>();
    const values: string[] = [];

    for (const row of rows) {
      for (const col of columns) {
        if (!isCategoricalColumn(col)) continue;
        const display = toDisplayCell(row[col]);
        if (display === "-") continue;
        const key = `${col}::${display}`;
        if (!seen.has(key)) {
          seen.add(key);
          values.push(key);
        }
      }
    }

    const seed = hashString(`${columns.join("|")}#${rows.length}`);
    const seedHue = seed % 360;

    values.forEach((key, index) => {
      map.set(key, {
        bg: colorForIndex(index, seedHue),
        fg: textColorForIndex(index, seedHue),
      });
    });

    return map;
  }, [columns, rows]);

  if (rows.length === 0) {
    return <p className="empty-state">No records returned for this query.</p>;
  }

  const startColumnResize = (column: string, clientX: number) => {
    const headerCell = headerRefs.current[column];
    const startWidth = columnWidths[column] ?? headerCell?.offsetWidth ?? 140;
    const minWidth = 90;

    const previousUserSelect = document.body.style.userSelect;
    const previousCursor = document.body.style.cursor;
    document.body.style.userSelect = "none";
    document.body.style.cursor = "col-resize";

    const onMouseMove = (event: MouseEvent) => {
      const delta = event.clientX - clientX;
      const nextWidth = Math.max(minWidth, Math.round(startWidth + delta));
      setColumnWidths((prev) => ({ ...prev, [column]: nextWidth }));
    };

    const onMouseUp = () => {
      document.body.style.userSelect = previousUserSelect;
      document.body.style.cursor = previousCursor;
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
  };

  const resetColumnWidth = (column: string) => {
    setColumnWidths((prev) => {
      if (!(column in prev)) return prev;
      const copy = { ...prev };
      delete copy[column];
      return copy;
    });
  };

  const toggleJsonCell = (cellKey: string) => {
    setExpandedJsonCells((prev) => ({ ...prev, [cellKey]: !prev[cellKey] }));
  };

  const toggleSort = (column: string) => {
    setPage(1);
    if (sortColumn === column) {
      setSortDirection((direction) => (direction === "asc" ? "desc" : "asc"));
      return;
    }
    setSortColumn(column);
    setSortDirection("asc");
  };

  const activeFilterCount = (search.trim() ? 1 : 0) + (filterColumn && filterValue.trim() ? 1 : 0);

  return (
    <div className="data-table-wrap">
      {title && <h3>{title}</h3>}

      <div className="table-meta">
        <p>
          Showing <strong>{pagedRows.length}</strong> of <strong>{processedRows.length}</strong> matching rows
          ({rows.length} total).
        </p>
        <div className="table-controls">
          <details className="table-filter-menu" ref={filterMenuRef}>
            <summary className="table-icon-button" title="Filter table" aria-label="Filter table">
              <span aria-hidden="true">Filter</span>
              {activeFilterCount > 0 && <strong>{activeFilterCount}</strong>}
            </summary>
            <div className="table-filter-popover">
              <label>
                Search all fields
                <input value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} placeholder="Find text in results" />
              </label>

              <label>
                Filter column
                <select value={filterColumn} onChange={(e) => { setFilterColumn(e.target.value); setPage(1); }}>
                  <option value="">None</option>
                  {columns.map((col) => (
                    <option value={col} key={col}>{formatColumnLabel(col)}</option>
                  ))}
                </select>
              </label>

              <label>
                Filter value
                <input
                  value={filterValue}
                  onChange={(e) => {
                    setFilterValue(e.target.value);
                    setPage(1);
                  }}
                  placeholder="Contains..."
                />
              </label>
            </div>
          </details>

          <button
            type="button"
            className="table-icon-button"
            onClick={() => downloadCsv(fileName, columns, processedRows)}
            title="Export CSV"
            aria-label="Export CSV"
          >
            <svg aria-hidden="true" className="table-download-icon" viewBox="0 0 24 24">
              <path d="M12 3v11" />
              <path d="m7 10 5 5 5-5" />
              <path d="M5 19h14" />
            </svg>
          </button>
        </div>
      </div>

      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((col) => {
                const width = columnWidths[col];
                const sizeStyle = width
                  ? { width: `${width}px`, minWidth: `${width}px`, maxWidth: `${width}px` }
                  : undefined;

                return (
                  <th
                    key={col}
                    ref={(cell) => {
                      headerRefs.current[col] = cell;
                    }}
                    style={sizeStyle}
                  >
                    <div className="th-content">
                      <button
                        type="button"
                        className="th-sort-button"
                        onClick={() => toggleSort(col)}
                        title={`Sort by ${formatColumnLabel(col)}`}
                      >
                        <span>{formatColumnLabel(col)}</span>
                        {sortColumn === col && (
                          <span className="sort-indicator" aria-hidden="true">
                            {sortDirection === "asc" ? "↑" : "↓"}
                          </span>
                        )}
                      </button>
                      <span
                        className="col-resize-handle"
                        role="separator"
                        aria-label={`Resize ${formatColumnLabel(col)} column`}
                        title="Drag to resize, double-click to reset"
                        onMouseDown={(event) => {
                          event.preventDefault();
                          startColumnResize(col, event.clientX);
                        }}
                        onDoubleClick={(event) => {
                          event.preventDefault();
                          resetColumnWidth(col);
                        }}
                      />
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {pagedRows.map((row, idx) => (
              <tr key={`${idx}-${toCell(row[columns[0]])}`}>
                {columns.map((col) => {
                  const raw = toCell(row[col]);
                  const display = toDisplayCell(row[col]);
                  const isEmpty = raw.trim().length === 0;
                  const categorical = isCategoricalColumn(col) && !isEmpty;
                  const jsonToggle = isJsonToggleColumn(col) && !isEmpty;
                  const dateLike = isDateColumn(col) && !isEmpty;
                  const colorKey = `${col}::${display}`;
                  const colors = categoricalColorMap.get(colorKey);
                  const json = jsonToggle ? tryFormatJson(row[col]) : null;
                  const dateDisplay = dateLike ? formatDateOnly(row[col]) : null;
                  const cellKey = `${idx}:${col}:${toCell(row[columns[0]])}`;
                  const isExpanded = !!expandedJsonCells[cellKey];

                  const compactJson = json?.ok ? json.compact : "";
                  const previewJson =
                    compactJson.length > 180 ? `${compactJson.slice(0, 180)}...` : compactJson;

                  return (
                    <td
                      key={col}
                      className={isEmpty ? "cell-empty" : undefined}
                      style={
                        columnWidths[col]
                          ? {
                              width: `${columnWidths[col]}px`,
                              minWidth: `${columnWidths[col]}px`,
                              maxWidth: `${columnWidths[col]}px`,
                            }
                          : undefined
                      }
                    >
                      {categorical && colors ? (
                        <span
                          className="category-pill"
                          style={{ backgroundColor: colors.bg, color: colors.fg }}
                          title={display}
                        >
                          {display}
                        </span>
                      ) : json?.ok ? (
                        <div className="json-cell">
                          <code className="json-preview">{isExpanded ? json.pretty : previewJson}</code>
                          <button
                            type="button"
                            className="json-toggle"
                            onClick={() => toggleJsonCell(cellKey)}
                          >
                            {isExpanded ? "Hide" : "Show"}
                          </button>
                        </div>
                      ) : dateDisplay ? (
                        <span className="date-cell" title={raw}>
                          {dateDisplay}
                        </span>
                      ) : (
                        display
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="table-footer">
        <label className="rows-per-page-control">
          Rows per page
          <select value={pageSize} onChange={(e) => { setPageSize(e.target.value); setPage(1); }}>
            <option value="10">10</option>
            <option value="25">25</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
        </label>

        <div className="pagination">
          <button type="button" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={currentPage <= 1}>
            Previous
          </button>
          <span>Page {currentPage} of {totalPages}</span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage >= totalPages}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
