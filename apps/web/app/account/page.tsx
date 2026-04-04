import { updateAccountAction } from "../actions/auth";
import { SessionUser } from "../../lib/auth";
import { fetchApi } from "../../lib/api";

type SearchParams = { [key: string]: string | string[] | undefined };

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

export default async function AccountPage({ searchParams }: { searchParams?: SearchParams }) {
  const error = first(searchParams?.error);
  const success = first(searchParams?.success);
  const me = await fetchApi<SessionUser>("/auth/me");

  return (
    <main>
      <section className="section-card">
        <p className="muted">Update your username or password. Current password is required for any change.</p>
      </section>

      <section className="section-stack split-card">
        <article className="metric-box">
          <p className="metric-label">Current username</p>
          <p className="metric-value account-name">{me.data?.username ?? "unknown"}</p>
          <p className="muted">Role: {me.data?.role ?? "unknown"}</p>
        </article>

        <article className="metric-box">
          {error ? <div className="error-box">{error}</div> : null}
          {success ? <div className="success-box">{success}</div> : null}

          <form action={updateAccountAction} className="auth-form">
            <label>
              New username
              <input name="username" defaultValue={me.data?.username ?? ""} />
            </label>

            <label>
              New password
              <input name="new_password" type="password" placeholder="Leave blank to keep current password" />
            </label>

            <label>
              Current password
              <input name="current_password" type="password" required />
            </label>

            <button type="submit">Save account changes</button>
          </form>
        </article>
      </section>
    </main>
  );
}
