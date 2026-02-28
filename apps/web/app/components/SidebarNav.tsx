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

export default function SidebarNav() {
  const pathname = usePathname();

  return (
    <nav>
      <p className="nav-section">Main menu</p>
      <ul className="side-list">
        {links.map((item) => {
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
          <a className="side-link" href="#">Settings</a>
        </li>
        <li>
          <a className="side-link" href="#">Help center</a>
        </li>
      </ul>
    </nav>
  );
}
