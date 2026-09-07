import React, { useState } from 'react';
import { ShieldCheck, Lock, User, ArrowRight, AlertCircle } from 'lucide-react';
import { api } from '../api/client';
import { User as UserType } from '../types';

interface LoginViewProps {
  onLoginSuccess: (user: UserType) => void;
}

export const LoginView: React.FC<LoginViewProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState<string>('admin');
  const [password, setPassword] = useState<string>('Admin@LabelSure2026');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await api.login(username, password);
      onLoginSuccess(user);
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'radial-gradient(circle at top, #1e293b, #0f172a)',
      padding: 20
    }}>
      <div style={{
        background: 'white',
        borderRadius: 'var(--radius-lg)',
        padding: 36,
        maxWidth: 440,
        width: '100%',
        boxShadow: 'var(--shadow-xl)',
        border: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{
            width: 52,
            height: 52,
            borderRadius: 14,
            background: 'linear-gradient(135deg, #2563eb, #10b981)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: 12,
            boxShadow: '0 8px 16px rgba(37, 99, 235, 0.3)'
          }}>
            <ShieldCheck size={30} color="white" />
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 800, color: '#0f172a' }}>APEX LabelSure</h2>
          <p style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>
            Department of Consumer Affairs, Government of India
          </p>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#2563eb', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: 2 }}>
            Legal Metrology Packaged Commodities
          </div>
        </div>

        {error && (
          <div style={{
            background: '#fef2f2',
            border: '1px solid #fecaca',
            color: '#b91c1c',
            padding: 10,
            borderRadius: 8,
            fontSize: 13,
            marginBottom: 18,
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#334155', marginBottom: 6 }}>
              Inspector / Officer ID
            </label>
            <div style={{ position: 'relative' }}>
              <User size={16} color="#94a3b8" style={{ position: 'absolute', left: 12, top: 12 }} />
              <input 
                type="text" 
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username or badge number"
                style={{
                  width: '100%',
                  padding: '10px 12px 10px 38px',
                  borderRadius: 8,
                  border: '1px solid #cbd5e1',
                  fontSize: 14,
                  outline: 'none'
                }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#334155', marginBottom: 6 }}>
              Security Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} color="#94a3b8" style={{ position: 'absolute', left: 12, top: 12 }} />
              <input 
                type="password" 
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                style={{
                  width: '100%',
                  padding: '10px 12px 10px 38px',
                  borderRadius: 8,
                  border: '1px solid #cbd5e1',
                  fontSize: 14,
                  outline: 'none'
                }}
              />
            </div>
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="btn btn-primary"
            style={{ width: '100%', padding: '12px 0', fontSize: 14, fontWeight: 600, marginTop: 6 }}
          >
            {loading ? 'Authenticating...' : 'Sign In to Inspection Portal'}
            <ArrowRight size={16} />
          </button>
        </form>

        {/* Quick Demo Accounts */}
        <div style={{ marginTop: 24, paddingTop: 18, borderTop: '1px solid #e2e8f0', textAlign: 'center' }}>
          <div style={{ fontSize: 11, color: '#64748b', fontWeight: 600, textTransform: 'uppercase', marginBottom: 8 }}>
            Quick Demo Roster Credentials
          </div>
          <div style={{ display: 'flex', gap: 6, justifyContent: 'center' }}>
            <button
              type="button"
              onClick={() => handleQuickLogin('admin', 'Admin@LabelSure2026')}
              style={{ padding: '4px 8px', borderRadius: 4, border: '1px solid #cbd5e1', background: '#f8fafc', fontSize: 11, cursor: 'pointer' }}
            >
              Chief Officer (Admin)
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin('inspector1', 'Inspector@2026')}
              style={{ padding: '4px 8px', borderRadius: 4, border: '1px solid #cbd5e1', background: '#f8fafc', fontSize: 11, cursor: 'pointer' }}
            >
              Field Inspector
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin('supervisor1', 'Supervisor@2026')}
              style={{ padding: '4px 8px', borderRadius: 4, border: '1px solid #cbd5e1', background: '#f8fafc', fontSize: 11, cursor: 'pointer' }}
            >
              Supervisor
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
