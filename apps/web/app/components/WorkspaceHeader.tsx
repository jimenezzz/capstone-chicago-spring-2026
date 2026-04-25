"use client";

import { usePathname } from "next/navigation";

import UserMenu from "./UserMenu";

function pageTitleFor(pathname: string) {
  switch (pathname) {
    case "/":
      return "Dashboard";
    case "/ndc":
      return "NDC Analysis";
    case "/cms":
      return "CMS Mapping";
    case "/samples":
      return "Dataset Explorer";
    case "/meta":
      return "Data Freshness";
    case "/health":
      return "System Health";
    case "/account":
      return "Account";
    case "/admin":
      return "Admin Tools";
    default:
      return "PharmaHub";
  }
}

export default function WorkspaceHeader() {
  const pathname = usePathname();

  return (
    <div className="workspace-actions">
      <h1 className="workspace-page-title">{pageTitleFor(pathname)}</h1>
      <UserMenu />
    </div>
  );
}
