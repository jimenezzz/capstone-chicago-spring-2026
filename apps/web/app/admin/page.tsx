import { redirect } from "next/navigation";

import { createUserAction } from "../actions/auth";
import DeleteUserForm from "../components/DeleteUserForm";
import { SessionUser } from "../../lib/auth";
import { fetchApi } from "../../lib/api";

type SearchParams = { [key: string]: string | string[] | undefined };

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

export default async function AdminPage({ searchParams }: { searchParams?: SearchParams }) {
  const error = first(searchParams?.error);
  const success = first(searchParams?.success);
  const me = await fetchApi<SessionUser>("/auth/me");

  if (me.data?.role !== "admin") {
    redirect("/");
  }

  const users = await fetchApi<SessionUser[]>("/admin/users");

  return (
    <main>
      <section className="section-card">
        <p className="muted">Manage users today. The panel is structured so ingestion controls can be added here later.</p>
      </section>

      <section className="admin-grid">
        <article className="section-card">
          <h3>Create user</h3>
          {error ? <div className="error-box">{error}</div> : null}
          {success ? <div className="success-box">{success}</div> : null}

          <form action={createUserAction} className="auth-form">
            <label>
              Username
              <input name="username" placeholder="new-user" required />
            </label>

            <label>
              Password
              <input name="password" type="password" required />
            </label>

            <label>
              Role
              <select name="role" defaultValue="viewer">
                <option value="viewer">Viewer</option>
                <option value="admin">Admin</option>
              </select>
            </label>

            <button type="submit">Create user</button>
          </form>
        </article>

        <article className="section-card">
          <h3>Current users</h3>
          <div className="user-list">
            {(users.data ?? []).map((user) => (
              <div className="user-row" key={user.id}>
                <div>
                  <strong>{user.username}</strong>
                  <p className="muted">{user.is_system_account ? "Seeded dev account" : "Created by admin"}</p>
                </div>
                <div className="user-row-actions">
                  <span className="status-pill ok">{user.role}</span>
                  {user.id !== me.data?.id ? (
                    <DeleteUserForm userId={user.id} username={user.username} />
                  ) : (
                    <span className="user-row-note">Current user</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="section-card" id="future-tools">
        <h3>Future admin tools</h3>
        <p className="muted">
          This space is reserved for ingestion pipeline controls so they live beside user administration instead of
          becoming a separate management surface later.
        </p>
      </section>
    </main>
  );
}
