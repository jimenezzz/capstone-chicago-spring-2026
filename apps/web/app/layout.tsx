import "./globals.css";
import SidebarNav from "./components/SidebarNav";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div className="workspace-shell">
          <aside className="sidebar">
            <div className="brand">PharmaHub</div>
            <SidebarNav />
          </aside>

          <div className="workspace-main">
            <div className="page-body">{children}</div>
          </div>
        </div>
      </body>
    </html>
  );
}
