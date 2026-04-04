'use client';
import { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Loader2, Search, Users, CreditCard, FileText, Activity } from 'lucide-react';
import Link from 'next/link';

const getSupabase = () => {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return null;
  return createClient(url, key);
};

const API_BASE = '/api';

const apiFetch = async (url, options = {}) => {
  const supabase = getSupabase();
  const session = supabase ? (await supabase.auth.getSession())?.data?.session : null;
  const token = session?.access_token;
  const headers = { ...options.headers, 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return fetch(`${API_BASE}${url}`, { ...options, headers });
};

export default function AdminPage() {
  const [loading, setLoading] = useState(true);
  const [authorized, setAuthorized] = useState(false);
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [activity, setActivity] = useState([]);
  const [searchEmail, setSearchEmail] = useState('');
  const [searchResult, setSearchResult] = useState(null);
  const [editingCredits, setEditingCredits] = useState({});

  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabase();
      if (!supabase) { window.location.href = '/'; return; }
      const { data: { session } } = await supabase.auth.getSession();
      if (!session || session.user.email !== 'aniketar111@gmail.com') {
        window.location.href = '/';
        return;
      }
      setAuthorized(true);
      await Promise.all([fetchUsers(), fetchStats(), fetchActivity()]);
      setLoading(false);
    };
    checkAuth();
  }, []);

  const fetchUsers = async () => {
    const res = await apiFetch('/admin/users');
    if (res.ok) { const data = await res.json(); setUsers(data.users || []); }
  };

  const fetchStats = async () => {
    const res = await apiFetch('/admin/stats');
    if (res.ok) { const data = await res.json(); setStats(data); }
  };

  const fetchActivity = async () => {
    const res = await apiFetch('/admin/activity');
    if (res.ok) { const data = await res.json(); setActivity(data.activity || []); }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchEmail) return;
    const res = await apiFetch(`/admin/search?email=${encodeURIComponent(searchEmail)}`);
    if (res.ok) { const data = await res.json(); setSearchResult(data); }
  };

  const handleUpdateCredits = async (userId, newCredits) => {
    const res = await apiFetch('/admin/credits', {
      method: 'POST',
      body: JSON.stringify({ userId, newCredits: parseInt(newCredits) }),
    });
    if (res.ok) {
      await fetchUsers();
      setEditingCredits(prev => { const n = { ...prev }; delete n[userId]; return n; });
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>;
  if (!authorized) return null;

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b bg-white">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold">Admin Panel</h1>
          <Link href="/"><Button variant="outline" size="sm">Back to App</Button></Link>
        </div>
      </div>
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card><CardContent className="pt-4"><div className="flex items-center gap-3"><Users className="w-5 h-5 text-primary" /><div><p className="text-sm text-muted-foreground">Total Users</p><p className="text-2xl font-bold">{stats.total_users}</p></div></div></CardContent></Card>
            <Card><CardContent className="pt-4"><div className="flex items-center gap-3"><CreditCard className="w-5 h-5 text-green-500" /><div><p className="text-sm text-muted-foreground">Pro Users</p><p className="text-2xl font-bold">{stats.total_pro_users}</p></div></div></CardContent></Card>
            <Card><CardContent className="pt-4"><div className="flex items-center gap-3"><FileText className="w-5 h-5 text-blue-500" /><div><p className="text-sm text-muted-foreground">Files Today</p><p className="text-2xl font-bold">{stats.files_processed_today}</p></div></div></CardContent></Card>
            <Card><CardContent className="pt-4"><div className="flex items-center gap-3"><Activity className="w-5 h-5 text-orange-500" /><div><p className="text-sm text-muted-foreground">Files This Month</p><p className="text-2xl font-bold">{stats.files_processed_this_month}</p></div></div></CardContent></Card>
          </div>
        )}

        {/* Search */}
        <Card>
          <CardHeader><CardTitle>Search User</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={handleSearch} className="flex gap-2">
              <Input placeholder="Search by email..." value={searchEmail} onChange={e => setSearchEmail(e.target.value)} />
              <Button type="submit"><Search className="w-4 h-4 mr-1" /> Search</Button>
            </form>
            {searchResult && searchResult.user && (
              <div className="mt-4 p-4 border rounded-lg">
                <p className="font-medium">{searchResult.user.email}</p>
                <p className="text-sm text-muted-foreground">Plan: {searchResult.user.plan} | Credits: {searchResult.user.credits}</p>
                {searchResult.uploads?.length > 0 && (
                  <div className="mt-2">
                    <p className="text-sm font-medium">Recent uploads:</p>
                    {searchResult.uploads.map(u => (
                      <p key={u.id} className="text-xs text-muted-foreground">{u.file_name} — {u.status} — {new Date(u.created_at).toLocaleString()}</p>
                    ))}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Users Table */}
        <Card>
          <CardHeader><CardTitle>All Users ({users.length})</CardTitle></CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="border-b"><th className="text-left py-2 px-3">Email</th><th className="text-left py-2 px-3">Plan</th><th className="text-left py-2 px-3">Credits</th><th className="text-left py-2 px-3">Joined</th><th className="text-left py-2 px-3">Actions</th></tr></thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id} className="border-b hover:bg-muted/30">
                      <td className="py-2 px-3">{u.email}</td>
                      <td className="py-2 px-3"><Badge variant={u.plan === 'pro' ? 'default' : 'secondary'}>{u.plan}</Badge></td>
                      <td className="py-2 px-3">
                        {editingCredits[u.id] !== undefined ? (
                          <div className="flex items-center gap-1">
                            <Input type="number" className="w-20 h-7 text-xs" value={editingCredits[u.id]} onChange={e => setEditingCredits(p => ({ ...p, [u.id]: e.target.value }))} />
                            <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => handleUpdateCredits(u.id, editingCredits[u.id])}>Save</Button>
                            <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => setEditingCredits(p => { const n = { ...p }; delete n[u.id]; return n; })}>X</Button>
                          </div>
                        ) : u.credits}
                      </td>
                      <td className="py-2 px-3 text-muted-foreground">{new Date(u.created_at).toLocaleDateString()}</td>
                      <td className="py-2 px-3">
                        <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => setEditingCredits(p => ({ ...p, [u.id]: u.credits }))}>Adjust Credits</Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Activity */}
        <Card>
          <CardHeader><CardTitle>Recent Activity</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {activity.map(a => (
                <div key={a.id} className="flex items-center justify-between text-sm py-2 border-b last:border-0">
                  <div><span className="font-medium">{a.email}</span> <Badge variant="secondary" className="ml-2 text-xs">{a.action}</Badge></div>
                  <span className="text-muted-foreground text-xs">{new Date(a.created_at).toLocaleString()}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
