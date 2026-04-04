"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/ndc", label: "NDC Analysis" },
  { href: "/cms", label: "CMS Analysis" },
  { href: "/samples", label: "Dataset Explorer" },
  { href: "/meta", label: "Data Freshness" },
  { href: "/health", label: "System Health" },
];

export default function SidebarNav({ role }: { role: "admin" | "viewer" }) {
  const pathname = usePathname();
  const navLinks = role === "admin" ? [...links, { href: "/admin", label: "Admin Tools" }] : links;

  return (
    <nav>
      <p className="nav-section">Main menu</p>
      <ul className="side-list">
        {navLinks.map((item) => {
          const active = pathname === item.href;
          return (
            <li key={item.href}>
              <Link className={active ? "side-link active" : "side-link"} href={item.href}>
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>

      <p className="nav-section">Preferences</p>
      <ul className="side-list">
        <li>
          <Link className={pathname === "/account" ? "side-link active" : "side-link"} href="/account">
            Account
          </Link>
        </li>
      </ul>
    </nav>
  );
}
