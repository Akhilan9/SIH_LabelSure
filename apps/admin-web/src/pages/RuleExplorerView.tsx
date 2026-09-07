import React, { useState, useEffect } from 'react';
import { BookOpen, ExternalLink, ShieldCheck, Filter } from 'lucide-react';
import { api } from '../api/client';
import { Rule } from '../types';

export const RuleExplorerView: React.FC = () => {
  const [rules, setRules] = useState<Rule[]>([]);
  const [versionFilter, setVersionFilter] = useState<string>('LMPC-2026-RULES');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    setLoading(true);
    api.listRules(versionFilter || undefined)
      .then(setRules)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [versionFilter]);

  return (
    <div className="page-body">
      {/* Control Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 700 }}>Department of Consumer Affairs Rule Corpus</h2>
          <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
            Statutory Legal Metrology (Packaged Commodities) rules and official gazette amendments.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)' }}>Regulatory Version:</span>
          <select
            value={versionFilter}
            onChange={(e) => setVersionFilter(e.target.value)}
            style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13, background: 'white' }}
          >
            <option value="LMPC-2026-RULES">LMPC 2026 Modernized Rules</option>
            <option value="LMPC-2021-AMENDMENT">LMPC 2021 USP Amendment</option>
            <option value="LMPC-2017-AMENDMENT">LMPC 2017 E-Commerce Amendment</option>
            <option value="LMPC-2011-BASE">LMPC 2011 Base Rules</option>
          </select>
        </div>
      </div>

      {/* Rules Grid */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>Loading regulatory rules...</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 20 }}>
          {rules.map((rule) => (
            <div key={`${rule.rule_id}-${rule.rule_version}`} style={{
              background: 'var(--bg-card)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border)',
              padding: 20,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: '#2563eb' }}>{rule.clause_reference}</span>
                  <span className={`badge ${rule.severity === 'CRITICAL' ? 'badge-fail' : 'badge-na'}`}>
                    {rule.severity}
                  </span>
                </div>

                <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-main)', marginBottom: 8 }}>
                  {rule.requirement}
                </h3>

                <p style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: 12 }}>
                  {rule.notes || rule.source_document}
                </p>

                <div style={{ background: '#f8fafc', padding: 10, borderRadius: 6, fontSize: 12, marginBottom: 12 }}>
                  <div>Operator: <b>{rule.validation_logic?.operator}</b></div>
                  <div>Target Field: <b>{rule.validation_logic?.field || 'Composite'}</b></div>
                  <div>Effective Date: <b>{rule.effective_from}</b></div>
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--border)', paddingTop: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{rule.rule_version}</span>
                <a 
                  href={rule.source_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  style={{ fontSize: 12, color: '#2563eb', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4, fontWeight: 600 }}
                >
                  Statutory Source <ExternalLink size={12} />
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
