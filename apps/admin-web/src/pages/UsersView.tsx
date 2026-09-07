import React, { useState, useEffect } from 'react';
import { 
  Users, 
  UserPlus, 
  ShieldCheck, 
  Search, 
  CheckCircle2, 
  XCircle, 
  Lock, 
  Mail, 
  BadgeCheck, 
  AlertTriangle,
  RefreshCw,
  X
} from 'lucide-react';
import { api } from '../api/client';
import { User, UserCreatePayload } from '../types';

interface UsersViewProps {
  currentUser: User | null;
}

export const UsersView: React.FC<UsersViewProps> = ({ currentUser }) => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [roleFilter, setRoleFilter] = useState<string>('ALL');

  // Register Modal State
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [form, setForm] = useState<UserCreatePayload>({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'INSPECTOR',
    badge_number: ''
  });
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  const fetchUsers = () => {
    setLoading(true);
    setError(null);
    api.listUsers()
      .then(setUsers)
      .catch((err: any) => setError(err.message || 'Failed to fetch registered officers'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!form.username.trim() || !form.email.trim() || !form.password.trim() || !form.full_name.trim()) {
      setFormError('Please complete all required fields.');
      return;
    }

    if (form.password.length < 8) {
      setFormError('Password must be at least 8 characters long.');
      return;
    }

    setSubmitting(true);
    try {
      await api.registerUser(form);
      setModalOpen(false);
      setForm({
        username: '',
        email: '',
        password: '',
        full_name: '',
        role: 'INSPECTOR',
        badge_number: ''
      });
      fetchUsers();
    } catch (err: any) {
      setFormError(err.message || 'Registration failed');
    } finally {
      setSubmitting(false);
    }
  };

  const filteredUsers = users.filter((u) => {
    const matchQuery = 
      u.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (u.badge_number && u.badge_number.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchRole = roleFilter === 'ALL' || u.role === roleFilter;
    return matchQuery && matchRole;
  });

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'ADMIN':
        return <span className="badge" style={{ background: '#ede9fe', color: '#6d28d9', border: '1px solid #ddd6fe', fontWeight: 700 }}>ADMIN</span>;
      case 'SUPERVISOR':
        return <span className="badge" style={{ background: '#dcfce7', color: '#15803d', border: '1px solid #86efac', fontWeight: 700 }}>SUPERVISOR</span>;
      case 'INSPECTOR':
        return <span className="badge" style={{ background: '#e0e7ff', color: '#3730a3', border: '1px solid #c7d2fe', fontWeight: 700 }}>INSPECTOR</span>;
      case 'VIEWER':
        return <span className="badge badge-na" style={{ fontWeight: 700 }}>VIEWER</span>;
      default:
        return <span className="badge badge-na">{role}</span>;
    }
  };

  return (
    <div className="page-body">
      {/* Top Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        color: 'white',
        borderRadius: 'var(--radius-lg)',
        padding: '24px 28px',
        marginBottom: 24,
        boxShadow: 'var(--shadow-md)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 16
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
            <span style={{
              background: 'rgba(37, 99, 235, 0.25)',
              padding: '4px 10px',
              borderRadius: 6,
              fontSize: 12,
              fontWeight: 700,
              color: '#93c5fd',
              letterSpacing: '0.04em'
            }}>
              ROLE-BASED ACCESS CONTROL (RBAC)
            </span>
            <span style={{ fontSize: 12, color: '#94a3b8' }}>
              Government Officer Registry
            </span>
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: '#f8fafc' }}>
            Legal Metrology Officer & Personnel Directory
          </h2>
          <p style={{ fontSize: 13, color: '#94a3b8', maxWidth: 700, marginTop: 4 }}>
            Authorized personnel registry with cryptographic role credentials for field inspection, supervisory review, and administrative control.
          </p>
        </div>

        {currentUser?.role === 'ADMIN' && (
          <button 
            onClick={() => setModalOpen(true)}
            className="btn btn-primary"
            style={{ gap: 8, padding: '10px 18px', background: '#2563eb' }}
          >
            <UserPlus size={16} /> Register New Officer
          </button>
        )}
      </div>

      {/* Search & Filter Bar */}
      <div style={{
        background: 'var(--bg-card)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border)',
        padding: '14px 18px',
        marginBottom: 24,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 16
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, flex: 1, minWidth: 280 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
            <Search size={16} color="var(--text-muted)" />
            <input 
              type="text"
              placeholder="Search by officer name, username, email, badge..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                border: 'none',
                outline: 'none',
                width: '100%',
                fontSize: 13,
                background: 'transparent'
              }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Role:</span>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--border)', fontSize: 13 }}
            >
              <option value="ALL">All Roles</option>
              <option value="ADMIN">ADMIN</option>
              <option value="SUPERVISOR">SUPERVISOR</option>
              <option value="INSPECTOR">INSPECTOR</option>
              <option value="VIEWER">VIEWER</option>
            </select>
          </div>
        </div>

        <button 
          onClick={fetchUsers}
          className="btn btn-secondary"
          style={{ gap: 6, fontSize: 12 }}
        >
          <RefreshCw size={13} /> Refresh
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div style={{
          background: '#fef2f2',
          border: '1px solid #fca5a5',
          borderRadius: 'var(--radius-md)',
          padding: 16,
          color: '#b91c1c',
          marginBottom: 20,
          display: 'flex',
          alignItems: 'center',
          gap: 12
        }}>
          <AlertTriangle size={18} />
          <div>{error}</div>
        </div>
      )}

      {/* Users Table */}
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Officer Name</th>
              <th>Username & Email</th>
              <th>Role</th>
              <th>Badge ID</th>
              <th>Account Status</th>
              <th>Security Level</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: 48, color: 'var(--text-muted)' }}>
                  <RefreshCw size={24} className="spin" style={{ animation: 'spin 1s linear infinite', marginBottom: 8 }} />
                  <div>Loading personnel directory...</div>
                </td>
              </tr>
            ) : filteredUsers.length > 0 ? (
              filteredUsers.map((u) => (
                <tr key={u.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{
                        width: 34,
                        height: 34,
                        borderRadius: '50%',
                        background: '#eff6ff',
                        color: '#2563eb',
                        fontWeight: 700,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 13
                      }}>
                        {u.full_name.charAt(0)}
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 14 }}>{u.full_name}</div>
                        {u.id === currentUser?.id && (
                          <span style={{ fontSize: 11, color: '#2563eb', fontWeight: 600 }}>Active Session</span>
                        )}
                      </div>
                    </div>
                  </td>

                  <td>
                    <div style={{ fontSize: 13, fontWeight: 500 }}>{u.username}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{u.email}</div>
                  </td>

                  <td>{getRoleBadge(u.role)}</td>

                  <td style={{ fontSize: 13, fontFamily: 'monospace', fontWeight: 600 }}>
                    {u.badge_number || <span style={{ color: 'var(--text-muted)' }}>—</span>}
                  </td>

                  <td>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#15803d', fontWeight: 600 }}>
                      <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#22c55e' }} />
                      Active
                    </span>
                  </td>

                  <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    {u.role === 'ADMIN' ? 'Full Authority' : u.role === 'SUPERVISOR' ? 'Audit & Signoff' : u.role === 'INSPECTOR' ? 'Field Adjudication' : 'Observer'}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: 48, color: 'var(--text-muted)' }}>
                  <Users size={36} style={{ opacity: 0.3, marginBottom: 8 }} />
                  <div>No officers matched the active search filters.</div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Register New Officer Modal */}
      {modalOpen && (
        <div className="modal-overlay" onClick={() => setModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 520 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <UserPlus size={20} color="#2563eb" />
                <h3 style={{ fontSize: 18, fontWeight: 700 }}>Register Legal Metrology Officer</h3>
              </div>
              <button onClick={() => setModalOpen(false)} style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            {formError && (
              <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', padding: 10, borderRadius: 6, color: '#b91c1c', fontSize: 12, marginBottom: 14 }}>
                {formError}
              </div>
            )}

            <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Full Legal Name</label>
                <input 
                  type="text"
                  required
                  placeholder="e.g. Inspector Ramesh Kumar"
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', marginTop: 4 }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Username</label>
                  <input 
                    type="text"
                    required
                    placeholder="e.g. ramesh_k"
                    value={form.username}
                    onChange={(e) => setForm({ ...form, username: e.target.value })}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', marginTop: 4 }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Badge ID / Number</label>
                  <input 
                    type="text"
                    placeholder="e.g. DL-LM-8921"
                    value={form.badge_number}
                    onChange={(e) => setForm({ ...form, badge_number: e.target.value })}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', marginTop: 4 }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Official Government Email</label>
                <input 
                  type="email"
                  required
                  placeholder="officer@labelsure.gov.in"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', marginTop: 4 }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Initial Password</label>
                  <input 
                    type="password"
                    required
                    placeholder="Minimum 8 characters"
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', marginTop: 4 }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>RBAC Officer Role</label>
                  <select
                    value={form.role}
                    onChange={(e) => setForm({ ...form, role: e.target.value as any })}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', marginTop: 4 }}
                  >
                    <option value="INSPECTOR">INSPECTOR (Field Officer)</option>
                    <option value="SUPERVISOR">SUPERVISOR (Assistant Controller)</option>
                    <option value="VIEWER">VIEWER (Read-Only Observer)</option>
                    <option value="ADMIN">ADMIN (Full Authority)</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 16 }}>
                <button 
                  type="button" 
                  onClick={() => setModalOpen(false)}
                  className="btn btn-secondary"
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={submitting}
                >
                  {submitting ? 'Registering...' : 'Register Officer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
