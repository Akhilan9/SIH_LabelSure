import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Search, 
  Download, 
  CheckCircle2, 
  XCircle, 
  HelpCircle, 
  ShieldCheck, 
  ExternalLink, 
  RefreshCw, 
  AlertTriangle,
  FileCheck,
  Calendar,
  Hash
} from 'lucide-react';
import { api } from '../api/client';
import { ReportRecord } from '../types';

interface ReportsViewProps {
  onOpenInspection?: (inspectionId: string) => void;
}

export const ReportsView: React.FC<ReportsViewProps> = ({ onOpenInspection }) => {
  const [reports, setReports] = useState<ReportRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');

  const fetchReports = () => {
    setLoading(true);
    setError(null);
    api.listReports(searchQuery)
      .then(setReports)
      .catch((err: any) => setError(err.message || 'Failed to load official reports'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      fetchReports();
    }, 300);
    return () => clearTimeout(delayDebounce);
  }, [searchQuery]);

  const getVerdictBadge = (verdict: string) => {
    switch (verdict) {
      case 'COMPLIANT':
        return <span className="badge badge-pass"><CheckCircle2 size={12} /> COMPLIANT</span>;
      case 'NON_COMPLIANT':
        return <span className="badge badge-fail"><XCircle size={12} /> NON-COMPLIANT</span>;
      case 'REQUIRES_REVIEW':
        return <span className="badge badge-uncertain"><HelpCircle size={12} /> REQUIRES REVIEW</span>;
      default:
        return <span className="badge badge-na">PENDING</span>;
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
              LEGAL METROLOGY CERTIFICATE REGISTRY
            </span>
            <span style={{ fontSize: 12, color: '#94a3b8' }}>
              Statutory Government PDF Reports
            </span>
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: '#f8fafc' }}>
            Official Compliance Inspection Reports & Certificates
          </h2>
          <p style={{ fontSize: 13, color: '#94a3b8', maxWidth: 700, marginTop: 4 }}>
            Tamper-evident statutory certificates generated in compliance with the Legal Metrology (Packaged Commodities) Rules. Authenticated with cryptographic SHA-256 hashes and officer credentials.
          </p>
        </div>

        <button 
          onClick={fetchReports}
          className="btn btn-secondary"
          style={{ background: '#334155', color: 'white', borderColor: '#475569', gap: 8 }}
        >
          <RefreshCw size={15} /> Refresh Registry
        </button>
      </div>

      {/* Search & Actions Bar */}
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
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 280 }}>
          <Search size={16} color="var(--text-muted)" />
          <input 
            type="text"
            placeholder="Search by certificate number, inspector name, or verdict..."
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

        <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          Total Certificates: <b>{reports.length}</b>
        </div>
      </div>

      {/* Error State */}
      {error && !loading && (
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
          <div><b>Error:</b> {error}</div>
        </div>
      )}

      {/* Table of Reports */}
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Certificate Number</th>
              <th>Compliance Verdict</th>
              <th>Inspecting Officer</th>
              <th>Rules Evaluated</th>
              <th>Verification SHA-256</th>
              <th>Issued Timestamp</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: 48, color: 'var(--text-muted)' }}>
                  <RefreshCw size={24} className="spin" style={{ animation: 'spin 1s linear infinite', marginBottom: 8 }} />
                  <div>Loading statutory report registry...</div>
                </td>
              </tr>
            ) : reports.length > 0 ? (
              reports.map((rep) => (
                <tr key={rep.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <FileCheck size={16} color="#2563eb" />
                      <span style={{ fontWeight: 700, fontFamily: 'monospace', color: '#1e40af' }}>
                        {rep.certificate_number}
                      </span>
                    </div>
                  </td>

                  <td>{getVerdictBadge(rep.compliance_verdict)}</td>

                  <td style={{ fontSize: 13, fontWeight: 600 }}>{rep.generated_by}</td>

                  <td style={{ fontSize: 12 }}>
                    <div style={{ display: 'flex', gap: 4 }}>
                      <span className="badge badge-pass" title="Passed Rules">{rep.summary?.passed || 0}P</span>
                      <span className="badge badge-fail" title="Failed Rules">{rep.summary?.failed || 0}F</span>
                      <span className="badge badge-uncertain" title="Uncertain Rules">{rep.summary?.uncertain || 0}U</span>
                    </div>
                  </td>

                  <td style={{ fontSize: 11, fontFamily: 'monospace', color: 'var(--text-muted)' }} title={rep.pdf_sha256}>
                    {rep.pdf_sha256.slice(0, 12)}...{rep.pdf_sha256.slice(-4)}
                  </td>

                  <td style={{ fontSize: 12, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                    {new Date(rep.generated_at).toLocaleString()}
                  </td>

                  <td>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <a 
                        href={rep.pdf_url}
                        target="_blank"
                        rel="noreferrer"
                        className="btn btn-primary"
                        style={{ padding: '4px 10px', fontSize: 12, gap: 4, textDecoration: 'none' }}
                      >
                        <Download size={13} /> PDF
                      </a>

                      {onOpenInspection && (
                        <button 
                          onClick={() => onOpenInspection(rep.inspection_id)}
                          className="btn btn-secondary"
                          style={{ padding: '4px 8px', fontSize: 12 }}
                          title="Open Case Dossier"
                        >
                          <ExternalLink size={13} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: 48, color: 'var(--text-muted)' }}>
                  <FileText size={36} style={{ opacity: 0.3, marginBottom: 8 }} />
                  <div>No statutory inspection certificates generated yet.</div>
                  <div style={{ fontSize: 12, marginTop: 4 }}>Generate certificates from inspection case dossiers.</div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
