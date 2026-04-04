import { loginAction } from "../actions/auth";

type SearchParams = { [key: string]: string | string[] | undefined };

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

export default function LoginPage({ searchParams }: { searchParams?: SearchParams }) {
  const error = first(searchParams?.error);
  const next = first(searchParams?.next) ?? "/";

  return (
    <main className="login-shell">
      <section className="login-panel">
        <p className="eyebrow">Secure access</p>
        <h1>Sign in to PharmaHub</h1>
        <p className="muted">
          Use the seeded dev accounts for now: <strong>admin/admin</strong> or <strong>viewer/viewer</strong>.
        </p>
        {error ? <div className="error-box">{error}</div> : null}

        <form action={loginAction} className="auth-form">
          <input type="hidden" name="next" value={next} />

          <label>
            Username
            <input name="username" placeholder="admin" required />
          </label>

          <label>
            Password
            <input name="password" type="password" placeholder="admin" required />
          </label>

          <button type="submit">Log in</button>
        </form>
      </section>
    </main>
  );
}
