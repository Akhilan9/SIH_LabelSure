import React, { useState, useEffect } from 'react';
import { History, ShieldCheck, FileText } from 'lucide-react';
import { api } from '../api/client';

export const AuditLogsView: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    api.listAuditLogs()
      .then(setLogs)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page-body">
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700 }}>Tamper-Evident System Audit Ledger</h2>
        <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          Immutable ledger of all inspection creations, human inspector overrides, AI analysis executions, and PDF generation events.
        </p>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Timestamp (UTC)</th>
              <th>Action</th>
              <th>Entity Type</th>
              <th>Entity ID</th>
              <th>State Transition Details</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} style={{ textAlign: 'center', padding: 32 }}>Loading audit trail...</td></tr>
            ) : logs.length > 0 ? (
              logs.map((log) => (
                <tr key={log.id}>
                  <td style={{ fontSize: 12, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td>
                    <span className="badge" style={{
                      background: log.action.includes('OVERRIDE') ? '#fee2e2' : log.action.includes('FINALIZE') ? '#dcfce7' : '#eff6ff',
                      color: log.action.includes('OVERRIDE') ? '#b91c1c' : log.action.includes('FINALIZE') ? '#15803d' : '#1d4ed8',
                      fontWeight: 700
                    }}>
                      {log.action}
                    </span>
                  </td>
                  <td style={{ fontSize: 13, fontWeight: 600 }}>{log.entity_type}</td>
                  <td style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                    {log.entity_id.slice(0, 16)}...
                  </td>
                  <td style={{ fontSize: 12 }}>
                    {log.new_state ? (
                      <pre style={{ margin: 0, padding: 4, background: '#f8fafc', borderRadius: 4, maxHeight: 60, overflow: 'auto', fontSize: 11 }}>
                        {JSON.stringify(log.new_state)}
                      </pre>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>No state data</span>
                    )}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: 32, color: 'var(--text-muted)' }}>
                  No audit log entries recorded yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
