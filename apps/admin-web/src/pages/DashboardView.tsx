import React, { useEffect, useState } from 'react';
import { 
  ClipboardCheck, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  HelpCircle, 
  BookOpen, 
  TrendingUp, 
  ShieldAlert,
  ArrowUpRight
} from 'lucide-react';
import { api } from '../api/client';
import { DashboardSummary, InspectionSummary } from '../types';

interface DashboardViewProps {
  onSelectInspection: (id: string) => void;
  onNewInspection: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  onSelectInspection,
  onNewInspection
}) => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    api.getDashboardSummary()
      .then(setSummary)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Loading compliance analytics...</div>;
  }

  const compliantPct = summary && summary.total_inspections > 0
    ? Math.round((summary.compliant / summary.total_inspections) * 100)
    : 0;

  return (
    <div className="page-body">
      {/* Metric Cards Row */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div>
            <div className="metric-label">Total Inspections</div>
            <div className="metric-value">{summary?.total_inspections || 0}</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>Audited commodities</div>
          </div>
          <div style={{ padding: 12, borderRadius: 12, background: '#eff6ff' }}>
            <ClipboardCheck size={26} color="#2563eb" />
          </div>
        </div>

        <div className="metric-card">
          <div>
            <div className="metric-label">Compliant Packages</div>
            <div className="metric-value" style={{ color: '#15803d' }}>{summary?.compliant || 0}</div>
            <div style={{ fontSize: 12, color: '#15803d', marginTop: 4 }}>{compliantPct}% pass rate</div>
          </div>
          <div style={{ padding: 12, borderRadius: 12, background: '#dcfce7' }}>
            <CheckCircle2 size={26} color="#16a34a" />
          </div>
        </div>

        <div className="metric-card">
          <div>
            <div className="metric-label">Non-Compliant Violations</div>
            <div className="metric-value" style={{ color: '#b91c1c' }}>{summary?.non_compliant || 0}</div>
            <div style={{ fontSize: 12, color: '#b91c1c', marginTop: 4 }}>Statutory breach detected</div>
          </div>
          <div style={{ padding: 12, borderRadius: 12, background: '#fee2e2' }}>
            <XCircle size={26} color="#dc2626" />
          </div>
        </div>

        <div className="metric-card">
          <div>
            <div className="metric-label">Requires Review</div>
            <div className="metric-value" style={{ color: '#b45309' }}>{summary?.requires_review || 0}</div>
            <div style={{ fontSize: 12, color: '#b45309', marginTop: 4 }}>Uncertain / blur evidence</div>
          </div>
          <div style={{ padding: 12, borderRadius: 12, background: '#fef3c7' }}>
            <HelpCircle size={26} color="#d97706" />
          </div>
        </div>

        <div className="metric-card">
          <div>
            <div className="metric-label">Active Legal Rules</div>
            <div className="metric-value">{summary?.active_rules_count || 17}</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>LMPC 2011–2026 corpus</div>
          </div>
          <div style={{ padding: 12, borderRadius: 12, background: '#f1f5f9' }}>
            <BookOpen size={26} color="#475569" />
          </div>
        </div>
      </div>

      {/* Analytics Breakdown Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 32 }}>
        {/* Top Violation Categories */}
        <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700 }}>Top Statutory Violation Categories</h3>
            <ShieldAlert size={18} color="#ef4444" />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {summary?.violation_categories && Object.keys(summary.violation_categories).length > 0 ? (
              Object.entries(summary.violation_categories).map(([cat, count]) => (
                <div key={cat} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 13, color: 'var(--text-main)', fontWeight: 500 }}>{cat}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 120, height: 8, background: '#f1f5f9', borderRadius: 4, overflow: 'hidden' }}>
                      <div style={{
                        width: `${Math.min(100, count * 20)}%`,
                        height: '100%',
                        background: '#ef4444',
                        borderRadius: 4
                      }} />
                    </div>
                    <span style={{ fontSize: 13, fontWeight: 700, width: 20, textAlign: 'right' }}>{count}</span>
                  </div>
                </div>
              ))
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>No violations recorded yet.</div>
            )}
          </div>
        </div>

        {/* Rule Version Distribution */}
        <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700 }}>Regulatory Version Baseline Usage</h3>
            <TrendingUp size={18} color="#2563eb" />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {summary?.rule_version_distribution && Object.entries(summary.rule_version_distribution).map(([ver, count]) => (
              <div key={ver} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 13, color: 'var(--text-main)', fontWeight: 500 }}>{ver}</span>
                <span className="badge badge-na" style={{ fontWeight: 700 }}>{count} cases</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Inspections Table */}
      <div className="table-container">
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <h3 style={{ fontSize: 16, fontWeight: 700 }}>Recent Inspections</h3>
          <button 
            onClick={onNewInspection}
            className="btn btn-secondary"
            style={{ fontSize: 12, padding: '4px 10px' }}
          >
            Create Inspection
          </button>
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>Inspection ID</th>
              <th>Commodity</th>
              <th>Inspector</th>
              <th>Status</th>
              <th>Compliance Verdict</th>
              <th>Date</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {summary?.recent_inspections && summary.recent_inspections.length > 0 ? (
              summary.recent_inspections.map((insp) => (
                <tr key={insp.id}>
                  <td style={{ fontWeight: 600, color: '#2563eb' }}>{insp.inspection_number}</td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{insp.commodity_name}</div>
                    {insp.brand_name && <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{insp.brand_name}</div>}
                  </td>
                  <td>{insp.inspector_name || 'Inspector'}</td>
                  <td>
                    <span className="badge badge-na">{insp.status}</span>
                  </td>
                  <td>
                    {insp.compliance_status === 'COMPLIANT' && <span className="badge badge-pass"><CheckCircle2 size={12} /> COMPLIANT</span>}
                    {insp.compliance_status === 'NON_COMPLIANT' && <span className="badge badge-fail"><XCircle size={12} /> NON-COMPLIANT</span>}
                    {insp.compliance_status === 'REQUIRES_REVIEW' && <span className="badge badge-uncertain"><HelpCircle size={12} /> REQUIRES REVIEW</span>}
                    {insp.compliance_status === 'PENDING' && <span className="badge badge-na">PENDING</span>}
                  </td>
                  <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    {new Date(insp.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    <button 
                      onClick={() => onSelectInspection(insp.id)}
                      className="btn btn-secondary"
                      style={{ padding: '4px 8px', fontSize: 12 }}
                    >
                      Inspect <ArrowUpRight size={14} />
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: 32, color: 'var(--text-muted)' }}>
                  No inspections available. Click "New Inspection" to start auditing packaged commodities.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
