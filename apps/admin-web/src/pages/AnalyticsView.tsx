import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  HelpCircle, 
  Layers, 
  RefreshCw,
  PieChart,
  Scale,
  Users
} from 'lucide-react';
import { api } from '../api/client';
import { AnalyticsData } from '../types';

export const AnalyticsView: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = () => {
    setLoading(true);
    setError(null);
    api.getAnalytics()
      .then(setData)
      .catch((err: any) => setError(err.message || 'Failed to fetch analytics data'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

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
              INTELLIGENCE & AUDIT METRICS
            </span>
            <span style={{ fontSize: 12, color: '#94a3b8' }}>
              Enforcement Risk Trends
            </span>
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: '#f8fafc' }}>
            Packaged Commodity Compliance Intelligence
          </h2>
          <p style={{ fontSize: 13, color: '#94a3b8', maxWidth: 700, marginTop: 4 }}>
            Aggregated statutory audit metrics across Legal Metrology rules, non-compliance frequency distributions, and human inspector adjudications.
          </p>
        </div>

        <button 
          onClick={fetchAnalytics}
          className="btn btn-secondary"
          style={{ background: '#334155', color: 'white', borderColor: '#475569', gap: 8 }}
        >
          <RefreshCw size={15} /> Refresh Analytics
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

      {loading ? (
        <div style={{ textAlign: 'center', padding: 80, color: 'var(--text-muted)' }}>
          <RefreshCw size={32} className="spin" style={{ animation: 'spin 1s linear infinite', marginBottom: 16 }} />
          <p style={{ fontSize: 14 }}>Aggregating Legal Metrology compliance metrics...</p>
        </div>
      ) : data ? (
        <div>
          {/* KPI Cards Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: 16,
            marginBottom: 24
          }}>
            <div style={{
              background: 'var(--bg-card)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border)',
              padding: 20,
              boxShadow: 'var(--shadow-sm)'
            }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Total Inspections
              </div>
              <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--text-main)', marginTop: 6 }}>
                {data.total_inspections}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                Across physical packaging & e-comm
              </div>
            </div>

            <div style={{
              background: 'var(--bg-card)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border)',
              padding: 20,
              boxShadow: 'var(--shadow-sm)'
            }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Compliance Rate
              </div>
              <div style={{ fontSize: 28, fontWeight: 800, color: data.compliance_rate >= 70 ? '#15803d' : '#b91c1c', marginTop: 6 }}>
                {data.compliance_rate}%
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                {data.compliant_count} Compliant of {data.total_inspections} total
              </div>
            </div>

            <div style={{
              background: 'var(--bg-card)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border)',
              padding: 20,
              boxShadow: 'var(--shadow-sm)'
            }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Rules Evaluated
              </div>
              <div style={{ fontSize: 28, fontWeight: 800, color: '#2563eb', marginTop: 6 }}>
                {data.total_rules_evaluated}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                {data.passed_findings} Pass | {data.failed_findings} Fail | {data.uncertain_findings} Uncertain
              </div>
            </div>

            <div style={{
              background: 'var(--bg-card)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border)',
              padding: 20,
              boxShadow: 'var(--shadow-sm)'
            }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Inspector Overrides
              </div>
              <div style={{ fontSize: 28, fontWeight: 800, color: '#6366f1', marginTop: 6 }}>
                {data.overridden_findings}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                Human-in-the-loop statutory adjudications
              </div>
            </div>
          </div>

          {/* Charts Row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: 20, marginBottom: 24 }}>
            {/* Top Statutory Violations Card */}
            <div style={{
              background: 'var(--bg-card)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border)',
              padding: 24,
              boxShadow: 'var(--shadow-sm)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                <BarChart3 size={18} color="#2563eb" />
                <h3 style={{ fontSize: 16, fontWeight: 700 }}>Top Statutory Violations by Clause</h3>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {data.top_violations.map((v, i) => {
                  const maxCount = Math.max(...data.top_violations.map(t => t.count), 1);
                  const pct = Math.round((v.count / maxCount) * 100);
                  return (
                    <div key={i}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                        <span style={{ fontWeight: 600 }}>{v.clause}: {v.title}</span>
                        <span style={{ fontWeight: 700, color: '#dc2626' }}>{v.count} violations</span>
                      </div>
                      <div style={{ height: 8, background: '#f1f5f9', borderRadius: 4, overflow: 'hidden' }}>
                        <div 
                          style={{ 
                            width: `${pct}%`, 
                            height: '100%', 
                            background: i === 0 ? '#ef4444' : i === 1 ? '#f97316' : '#f59e0b',
                            borderRadius: 4
                          }} 
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Commodity Risk Breakdown Card */}
            <div style={{
              background: 'var(--bg-card)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border)',
              padding: 24,
              boxShadow: 'var(--shadow-sm)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                <PieChart size={18} color="#10b981" />
                <h3 style={{ fontSize: 16, fontWeight: 700 }}>Inspections by Commodity Category</h3>
              </div>

              {data.commodity_distribution.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {data.commodity_distribution.map((c, i) => {
                    const pct = Math.round((c.count / (data.total_inspections || 1)) * 100);
                    return (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: '#f8fafc', borderRadius: 8 }}>
                        <span style={{ fontSize: 13, fontWeight: 600 }}>{c.name}</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{c.count} packages</span>
                          <span className="badge badge-pass">{pct}%</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 32 }}>
                  No commodity data recorded yet.
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
