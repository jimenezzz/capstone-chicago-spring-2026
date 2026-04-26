"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { formatCurrency } from "./NadacPricingDashboard";

type NadacSearchHistoryItem = {
  ndc11: string;
  asOfDate?: string;
  searchedAt: string;
  genericName?: string | null;
  latestPrice?: string | number | null;
  latestEffectiveDate?: string | null;
  resultCount?: number;
};

const STORAGE_KEY = "pharma-hub:nadac-search-history";
const MAX_HISTORY_ITEMS = 10;

function isHistoryItem(value: unknown): value is NadacSearchHistoryItem {
  if (!value || typeof value !== "object") return false;
  const item = value as Partial<NadacSearchHistoryItem>;
  return typeof item.ndc11 === "string" && typeof item.searchedAt === "string";
}

function readHistory() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter(isHistoryItem) : [];
  } catch {
    return [];
  }
}

function historyHref(item: NadacSearchHistoryItem) {
  const params = new URLSearchParams({ ndc11: item.ndc11, mode: "nadac" });
  if (item.asOfDate) {
    params.set("as_of_date", item.asOfDate);
  }
  return `/ndc?${params.toString()}`;
}

function formatSearchTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Recently";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

export function NadacSearchHistoryRecorder({
  ndc11,
  asOfDate,
  genericName,
  latestPrice,
  latestEffectiveDate,
  resultCount,
}: Omit<NadacSearchHistoryItem, "searchedAt">) {
  useEffect(() => {
    if (!ndc11) return;

    const nextItem: NadacSearchHistoryItem = {
      ndc11,
      asOfDate,
      genericName,
      latestPrice,
      latestEffectiveDate,
      resultCount,
      searchedAt: new Date().toISOString(),
    };
    const keyFor = (item: NadacSearchHistoryItem) => `${item.ndc11}:${item.asOfDate ?? ""}`;
    const nextHistory = [
      nextItem,
      ...readHistory().filter((item) => keyFor(item) !== keyFor(nextItem)),
    ].slice(0, MAX_HISTORY_ITEMS);

    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextHistory));
    window.dispatchEvent(new Event("nadac-search-history-updated"));
  }, [asOfDate, genericName, latestEffectiveDate, latestPrice, ndc11, resultCount]);

  return null;
}

export function RecentNadacSearchHistory() {
  const [history, setHistory] = useState<NadacSearchHistoryItem[]>([]);

  function clearHistory() {
    window.localStorage.removeItem(STORAGE_KEY);
    setHistory([]);
    window.dispatchEvent(new Event("nadac-search-history-updated"));
  }

  useEffect(() => {
    const syncHistory = () => setHistory(readHistory().slice(0, MAX_HISTORY_ITEMS));
    syncHistory();

    window.addEventListener("storage", syncHistory);
    window.addEventListener("nadac-search-history-updated", syncHistory);
    return () => {
      window.removeEventListener("storage", syncHistory);
      window.removeEventListener("nadac-search-history-updated", syncHistory);
    };
  }, []);

  return (
    <section className="section-stack">
      <div className="history-section-head">
        <div>
          <h2 className="section-title-soft section-title-compact">Recent NADAC history searches</h2>
          <p className="muted">Latest 10 price history lookups from NDC Analysis.</p>
        </div>
        <div className="history-section-actions">
          {history.length > 0 && (
            <button className="history-clear-button" type="button" onClick={clearHistory} aria-label="Clear NADAC recent searches">
              X
            </button>
          )}
          <Link className="btn-link history-section-action" href="/ndc?mode=nadac">
            Open NADAC history
          </Link>
        </div>
      </div>

      {history.length === 0 ? (
        <p className="empty-state">No NADAC history searches yet.</p>
      ) : (
        <div className="recent-history-list">
          {history.map((item) => (
            <Link className="recent-history-item" href={historyHref(item)} key={`${item.ndc11}-${item.asOfDate ?? ""}`}>
              <span>
                <strong>{item.genericName || item.ndc11}</strong>
                <small>
                  NDC {item.ndc11}
                  {item.asOfDate ? ` · As of ${item.asOfDate}` : ""}
                </small>
              </span>
              <span className="recent-history-meta">
                <strong>{formatCurrency(item.latestPrice)}</strong>
                <small>{item.latestEffectiveDate || `${item.resultCount ?? 0} points`}</small>
              </span>
              <time dateTime={item.searchedAt}>{formatSearchTime(item.searchedAt)}</time>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
