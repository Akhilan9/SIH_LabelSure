import React from 'react';
import { Search, Bell, CheckCircle2, AlertCircle } from 'lucide-react';
import { User } from '../types';

interface TopNavbarProps {
  pageTitle: string;
  user: User | null;
  searchQuery?: string;
  onSearchChange?: (q: string) => void;
}

export const TopNavbar: React.FC<TopNavbarProps> = ({
  pageTitle,
  user,
  searchQuery = '',
  onSearchChange
}) => {
  return (
    <header className="top-navbar">
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-main)' }}>{pageTitle}</h1>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
        {onSearchChange && (
          <div style={{ position: 'relative', width: 280 }}>
            <Search size={16} color="#94a3b8" style={{ position: 'absolute', left: 12, top: 10 }} />
            <input 
              type="text"
              placeholder="Search commodity, brand, ID..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px 8px 36px',
                borderRadius: 8,
                border: '1px solid var(--border)',
                fontSize: 13,
                outline: 'none',
                background: '#f8fafc'
              }}
            />
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: '#f1f5f9', padding: '6px 12px', borderRadius: 20 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981' }}></span>
          <span style={{ fontSize: 12, fontWeight: 600, color: '#334155' }}>LMPC 2026 Engine Active</span>
        </div>
      </div>
    </header>
  );
};
