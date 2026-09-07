import React from 'react';
import { 
  LayoutDashboard, 
  ClipboardCheck, 
  BookOpen, 
  FileText, 
  History, 
  LogOut, 
  ShieldCheck,
  PlusCircle,
  Camera,
  Eye,
  BarChart3,
  Users
} from 'lucide-react';
import { User } from '../types';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  user: User | null;
  onLogout: () => void;
  onNewInspection: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  setCurrentTab,
  user,
  onLogout,
  onNewInspection
}) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div style={{
          width: 38,
          height: 38,
          borderRadius: 8,
          background: 'linear-gradient(135deg, #2563eb, #10b981)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 10px rgba(37, 99, 235, 0.4)'
        }}>
          <ShieldCheck size={22} color="white" />
        </div>
        <div>
          <div className="brand-font" style={{ fontSize: 16, fontWeight: 700, letterSpacing: '0.02em' }}>APEX LabelSure</div>
          <div style={{ fontSize: 10, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Legal Metrology</div>
        </div>
      </div>

      <div style={{ padding: '16px 12px 0' }}>
        <button 
          onClick={onNewInspection}
          className="btn btn-primary"
          style={{ width: '100%', justifyContent: 'center', gap: 8, padding: '10px 0', borderRadius: 8 }}
        >
          <PlusCircle size={16} />
          New Inspection
        </button>
      </div>

      <nav className="sidebar-nav">
        <button 
          className={`nav-item ${currentTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setCurrentTab('dashboard')}
        >
          <LayoutDashboard size={18} />
          Dashboard
        </button>

        <button 
          className={`nav-item ${currentTab === 'inspections' || currentTab === 'inspection-detail' ? 'active' : ''}`}
          onClick={() => setCurrentTab('inspections')}
        >
          <ClipboardCheck size={18} />
          Inspections
        </button>

        <button 
          className={`nav-item ${currentTab === 'evidence' ? 'active' : ''}`}
          onClick={() => setCurrentTab('evidence')}
        >
          <Camera size={18} />
          Evidence Viewer
        </button>

        <button 
          className={`nav-item ${currentTab === 'rulelens' ? 'active' : ''}`}
          onClick={() => setCurrentTab('rulelens')}
        >
          <Eye size={18} />
          RuleLens
        </button>

        <button 
          className={`nav-item ${currentTab === 'rules' ? 'active' : ''}`}
          onClick={() => setCurrentTab('rules')}
        >
          <BookOpen size={18} />
          Rule Explorer
        </button>

        <button 
          className={`nav-item ${currentTab === 'reports' ? 'active' : ''}`}
          onClick={() => setCurrentTab('reports')}
        >
          <FileText size={18} />
          Reports
        </button>

        <button 
          className={`nav-item ${currentTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setCurrentTab('analytics')}
        >
          <BarChart3 size={18} />
          Analytics
        </button>

        {(user?.role === 'ADMIN' || user?.role === 'SUPERVISOR') && (
          <button 
            className={`nav-item ${currentTab === 'users' ? 'active' : ''}`}
            onClick={() => setCurrentTab('users')}
          >
            <Users size={18} />
            Users
          </button>
        )}

        <button 
          className={`nav-item ${currentTab === 'audit' ? 'active' : ''}`}
          onClick={() => setCurrentTab('audit')}
        >
          <History size={18} />
          Audit Logs
        </button>
      </nav>

      <div className="sidebar-footer">
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'white' }}>{user?.full_name || 'Inspector'}</span>
          <span style={{ fontSize: 11, color: '#94a3b8' }}>{user?.role} {user?.badge_number ? `(${user.badge_number})` : ''}</span>
        </div>
        <button 
          onClick={onLogout}
          style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: 4 }}
          title="Logout"
        >
          <LogOut size={18} />
        </button>
      </div>
    </aside>
  );
};
