"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

const links = [
  { href: "/", label: "Dashboard", icon: "/nav-icons/dashboard.png" },
  { href: "/ndc", label: "NDC Analysis", icon: "/nav-icons/ndc-analysis.png" },
  { href: "/cms", label: "CMS Mapping", icon: "/nav-icons/cms-analysis.png" },
  { href: "/samples", label: "Dataset Explorer", icon: "/nav-icons/dataset-explorer.png" },
  { href: "/meta", label: "Data Freshness", icon: "/nav-icons/data-freshness.png" },
  { href: "/health", label: "System Health", icon: "/nav-icons/system-health.png" },
];

const storagePrefix = "pharmahub:last-url:";

export default function SidebarNav({ role }: { role: "admin" | "viewer" }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isOpen, setIsOpen] = useState(false);
  const [savedUrls, setSavedUrls] = useState<Record<string, string>>({});

  const navLinks = useMemo(
    () =>
      role === "admin"
        ? [...links, { href: "/admin", label: "Admin Tools", icon: "/nav-icons/admin-tools.png" }]
        : links,
    [role],
  );

  useEffect(() => {
    const query = searchParams.toString();
    const currentUrl = query ? `${pathname}?${query}` : pathname;
    sessionStorage.setItem(`${storagePrefix}${pathname}`, currentUrl);
    setSavedUrls((current) => ({ ...current, [pathname]: currentUrl }));
  }, [pathname, searchParams]);

  useEffect(() => {
    const nextUrls: Record<string, string> = {};
    for (const item of [...navLinks, { href: "/account", label: "Account", icon: "/nav-icons/account.png" }]) {
      const saved = sessionStorage.getItem(`${storagePrefix}${item.href}`);
      if (saved) {
        nextUrls[item.href] = saved;
      }
    }
    setSavedUrls(nextUrls);
  }, [navLinks]);

  const closeNav = () => setIsOpen(false);

  return (
    <>
      <button
        type="button"
        className="nav-toggle"
        aria-controls="workspace-navigation"
        aria-expanded={isOpen}
        aria-label="Toggle navigation"
        onClick={() => setIsOpen((open) => !open)}
      >
        <span aria-hidden="true" />
      </button>

      <nav id="workspace-navigation" className={isOpen ? "sidebar-nav open" : "sidebar-nav"}>
        <p className="nav-section">Main menu</p>
        <ul className="side-list">
          {navLinks.map((item) => {
            const active = pathname === item.href;
            return (
              <li key={item.href}>
                <Link
                  className={active ? "side-link active" : "side-link"}
                  href={savedUrls[item.href] ?? item.href}
                  onClick={closeNav}
                >
                  <span
                    aria-hidden="true"
                    className={item.href === "/" ? "side-icon dashboard-icon" : "side-icon"}
                    style={{ maskImage: `url(${item.icon})`, WebkitMaskImage: `url(${item.icon})` }}
                  />
                  <span>{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>

        <p className="nav-section">Preferences</p>
        <ul className="side-list">
          <li>
            <Link
              className={pathname === "/account" ? "side-link active" : "side-link"}
              href={savedUrls["/account"] ?? "/account"}
              onClick={closeNav}
            >
              <span
                aria-hidden="true"
                className="side-icon"
                style={{ maskImage: "url(/nav-icons/account.png)", WebkitMaskImage: "url(/nav-icons/account.png)" }}
              />
              <span>Account</span>
            </Link>
          </li>
        </ul>
      </nav>
    </>
  );
}
