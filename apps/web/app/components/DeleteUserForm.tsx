"use client";

import { deleteUserAction } from "../actions/auth";

export default function DeleteUserForm({ userId, username }: { userId: number; username: string }) {
  return (
    <form
      action={deleteUserAction}
      onSubmit={(event) => {
        if (!window.confirm(`Delete user "${username}"? This cannot be undone.`)) {
          event.preventDefault();
        }
      }}
    >
      <input type="hidden" name="user_id" value={userId} />
      <button type="submit" className="btn-danger admin-delete-button" aria-label={`Delete user ${username}`} title="Delete user">
        X
      </button>
    </form>
  );
}
