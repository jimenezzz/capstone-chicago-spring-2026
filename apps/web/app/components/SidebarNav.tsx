"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Dashboard", icon: "/nav-icons/dashboard.png" },
  { href: "/ndc", label: "NDC Analysis", icon: "/nav-icons/ndc-analysis.png" },
  { href: "/cms", label: "CMS Analysis", icon: "/nav-icons/cms-analysis.png" },
  { href: "/samples", label: "Dataset Explorer", icon: "/nav-icons/dataset-explorer.png" },
  { href: "/meta", label: "Data Freshness", icon: "/nav-icons/data-freshness.png" },
  { href: "/health", label: "System Health", icon: "/nav-icons/system-health.png" },
];

export default function SidebarNav({ role }: { role: "admin" | "viewer" }) {
  const pathname = usePathname();
  const navLinks =
    role === "admin"
      ? [...links, { href: "/admin", label: "Admin Tools", icon: "/nav-icons/admin-tools.png" }]
      : links;

  return (
    <nav>
      <p className="nav-section">Main menu</p>
      <ul className="side-list">
        {navLinks.map((item) => {
          const active = pathname === item.href;
          return (
            <li key={item.href}>
              <Link className={active ? "side-link active" : "side-link"} href={item.href}>
                <span
                  aria-hidden="true"
                  className="side-icon"
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
          <Link className={pathname === "/account" ? "side-link active" : "side-link"} href="/account">
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
  );
}
