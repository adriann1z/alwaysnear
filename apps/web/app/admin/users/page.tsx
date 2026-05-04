"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { AdminShell } from "@/components/admin/AdminShell";
import { Badge, Card } from "@/components/parent/ui";
import { api } from "@/lib/api";
import { RequireAdmin } from "@/lib/auth";

export default function AdminUsersPage() {
  return (
    <RequireAdmin>
      <AdminShell>
        <AdminUsersContent />
      </AdminShell>
    </RequireAdmin>
  );
}

function AdminUsersContent() {
  const [role, setRole] = useState("");
  const users = useQuery({
    queryKey: ["admin-users", role],
    queryFn: () => api.admin.users({ role: role || undefined })
  });

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ink/50">
          Admin users
        </p>
        <h1 className="mt-2 text-5xl font-bold">Accounts</h1>
      </div>

      <Card>
        <label className="space-y-2 text-sm font-semibold">
          Role
          <select
            value={role}
            onChange={(event) => setRole(event.target.value)}
            className="block w-full max-w-sm rounded-3xl border border-ink/10 bg-white px-4 py-3 text-sm outline-none"
          >
            <option value="">All</option>
            <option value="parent">Parent</option>
            <option value="admin">Admin</option>
          </select>
        </label>
      </Card>

      <Card>
        {users.isLoading && <p className="text-sm text-ink/60">Loading users...</p>}
        {users.isError && <p className="text-sm text-emergency">Users could not be loaded.</p>}
        {users.data && users.data.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[620px] border-separate border-spacing-y-3 text-left text-sm">
              <thead className="text-xs uppercase tracking-[0.14em] text-ink/45">
                <tr>
                  <th className="px-4">Email</th>
                  <th className="px-4">Role</th>
                  <th className="px-4">Created</th>
                  <th className="px-4">Active</th>
                </tr>
              </thead>
              <tbody>
                {users.data.map((user) => (
                  <tr key={user.id} className="bg-white">
                    <td className="rounded-l-3xl px-4 py-4 font-semibold">{user.email}</td>
                    <td className="px-4 py-4">
                      <Badge tone={user.role === "admin" ? "lavender" : "neutral"}>{user.role}</Badge>
                    </td>
                    <td className="px-4 py-4 text-ink/70">{new Date(user.created_at).toLocaleString()}</td>
                    <td className="rounded-r-3xl px-4 py-4">{user.is_active ? "Yes" : "No"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {users.data?.length === 0 && <p className="text-sm text-ink/60">No users match this filter.</p>}
      </Card>
    </div>
  );
}
