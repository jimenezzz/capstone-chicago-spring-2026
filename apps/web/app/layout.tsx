import "./globals.css";
import { headers } from "next/headers";
import { redirect } from "next/navigation";

import SidebarNav from "./components/SidebarNav";
import WorkspaceHeader from "./components/WorkspaceHeader";
import { SessionUser } from "../lib/auth";
import { fetchApi } from "../lib/api";

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = (await headers()).get("x-pathname") ?? "/";
  const isLoginRoute = pathname.startsWith("/login");

  if (isLoginRoute) {
    return (
      <html lang="en">
        <body>{children}</body>
      </html>
    );
  }

  const session = await fetchApi<SessionUser>("/auth/me");
  if (!session.ok || !session.data) {
    redirect(`/login?next=${encodeURIComponent(pathname)}&error=Session expired`);
  }

  return (
    <html lang="en">
      <body>
        <div className="workspace-shell">
          <aside className="sidebar">
            <div className="brand">PharmaHub</div>
            <SidebarNav role={session.data.role} />
          </aside>

          <div className="workspace-main">
            <WorkspaceHeader />
            <div className="page-body">{children}</div>
          </div>
        </div>
      </body>
    </html>
  );
}
