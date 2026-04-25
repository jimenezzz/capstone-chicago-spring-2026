import { redirect } from "next/navigation";

import { createUserAction, updateVolatilityThresholdAction } from "../actions/auth";
import DeleteUserForm from "../components/DeleteUserForm";
import { SessionUser } from "../../lib/auth";
import { fetchApi } from "../../lib/api";

type SearchParams = { [key: string]: string | string[] | undefined };
type VolatilityRiskSettings = {
  threshold_pct: string | number;
  moderate_risk_months: number;
  high_risk_months: number;
};

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

export default async function AdminPage({ searchParams }: { searchParams?: SearchParams }) {
  const userError = first(searchParams?.user_error) ?? first(searchParams?.error);
  const userSuccess = first(searchParams?.user_success) ?? first(searchParams?.success);
  const settingsError = first(searchParams?.settings_error);
  const settingsSuccess = first(searchParams?.settings_success);
  const me = await fetchApi<SessionUser>("/auth/me");

  if (me.data?.role !== "admin") {
    redirect("/");
  }

  const users = await fetchApi<SessionUser[]>("/admin/users");
  const volatilitySettings = await fetchApi<VolatilityRiskSettings>("/admin/settings/volatility-threshold");

  return (
    <main>
      <section className="section-card">
        <p className="muted">Manage user access and configure the analytics defaults used across the hub.</p>
      </section>

      <section className="admin-grid">
        <article className="section-card">
          <h3>Create user</h3>
          {userError ? <div className="error-box">{userError}</div> : null}
          {userSuccess ? <div className="success-box">{userSuccess}</div> : null}

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

      <section className="section-card admin-setting-card">
        <h3>NADAC volatility threshold</h3>
        <p className="muted">
          Controls the percent-change cutoff and month counts used for Risk &amp; Stability labels on NDC Analysis.
        </p>
        {settingsError ? <div className="error-box">{settingsError}</div> : null}
        {settingsSuccess ? <div className="success-box">{settingsSuccess}</div> : null}

        <form action={updateVolatilityThresholdAction} className="auth-form admin-setting-form">
          <div className="admin-setting-fields">
            <label>
              Threshold percent
              <input
                name="threshold_pct"
                type="number"
                min="0"
                max="1000"
                step="0.1"
                defaultValue={String(volatilitySettings.data?.threshold_pct ?? 5)}
                required
              />
            </label>
            <label>
              Moderate Risk starts at months
              <input
                name="moderate_risk_months"
                type="number"
                min="1"
                max="120"
                step="1"
                defaultValue={String(volatilitySettings.data?.moderate_risk_months ?? 1)}
                required
              />
            </label>
            <label>
              High Risk starts at months
              <input
                name="high_risk_months"
                type="number"
                min="2"
                max="120"
                step="1"
                defaultValue={String(volatilitySettings.data?.high_risk_months ?? 3)}
                required
              />
            </label>
          </div>
          <button type="submit">Update threshold</button>
        </form>
      </section>
    </main>
  );
}
