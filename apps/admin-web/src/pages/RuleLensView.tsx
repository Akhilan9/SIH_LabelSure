import React, { useState, useEffect } from 'react';
import { 
  Eye, 
  Search, 
  CheckCircle2, 
  XCircle, 
  HelpCircle, 
  MinusCircle, 
  ZoomIn, 
  ZoomOut, 
  Edit3, 
  ShieldAlert, 
  ShieldCheck, 
  Layers, 
  ExternalLink,
  RefreshCw,
  AlertTriangle
} from 'lucide-react';
import { api } from '../api/client';
import { InspectionSummary, Finding, InspectionImage, Declaration } from '../types';

interface RuleLensViewProps {
  initialInspectionId?: string | null;
  onOpenInspectionDetail?: (id: string) => void;
}

export const RuleLensView: React.FC<RuleLensViewProps> = ({ 
  initialInspectionId,
  onOpenInspectionDetail 
}) => {
  const [inspections, setInspections] = useState<InspectionSummary[]>([]);
  const [selectedInspectionId, setSelectedInspectionId] = useState<string>(initialInspectionId || '');
  const [ruleLensData, setRuleLensData] = useState<any>(null);
  const [loadingList, setLoadingList] = useState<boolean>(true);
  const [loadingData, setLoadingData] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Active finding & visual state
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [zoomLevel, setZoomLevel] = useState<number>(1.0);
  const [overrideStatus, setOverrideStatus] = useState<string>('');
  const [overrideComment, setOverrideComment] = useState<string>('');
  const [submittingOverride, setSubmittingOverride] = useState<boolean>(false);

  // Fetch list of inspections on mount
  useEffect(() => {
    setLoadingList(true);
    api.listInspections()
      .then((list) => {
        setInspections(list);
        if (!selectedInspectionId && list.length > 0) {
          setSelectedInspectionId(list[0].id);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoadingList(false));
  }, []);

  // Fetch RuleLens data whenever selected inspection changes
  const fetchRuleLensData = () => {
    if (!selectedInspectionId) return;
    setLoadingData(true);
    setError(null);
    api.getRuleLens(selectedInspectionId)
      .then((data) => {
        setRuleLensData(data);
        const findings: Finding[] = data.findings || [];
        if (findings.length > 0) {
          setSelectedFinding(findings[0]);
        } else {
          setSelectedFinding(null);
        }
      })
      .catch((err: any) => setError(err.message || 'Failed to load RuleLens data'))
      .finally(() => setLoadingData(false));
  };

  useEffect(() => {
    fetchRuleLensData();
  }, [selectedInspectionId]);

  const handleApplyOverride = async () => {
    if (!selectedFinding || !overrideStatus) return;
    setSubmittingOverride(true);
    try {
      await api.overrideFinding(selectedFinding.id, overrideStatus, overrideComment);
      fetchRuleLensData();
      setOverrideStatus('');
      setOverrideComment('');
    } catch (err: any) {
      alert(`Error applying override: ${err.message}`);
    } finally {
      setSubmittingOverride(false);
    }
  };

  const findings: Finding[] = ruleLensData?.findings || [];
  const primaryImage = ruleLensData?.images?.[0] || null;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PASS':
        return <span className="badge badge-pass"><CheckCircle2 size={12} /> PASS</span>;
      case 'FAIL':
        return <span className="badge badge-fail"><XCircle size={12} /> FAIL</span>;
      case 'UNCERTAIN':
        return <span className="badge badge-uncertain"><HelpCircle size={12} /> UNCERTAIN</span>;
      default:
        return <span className="badge badge-na"><MinusCircle size={12} /> N/A</span>;
    }
  };

  return (
    <div className="page-body">
      {/* Top Header */}
      <div style={{
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        color: 'white',
        borderRadius: 'var(--radius-lg)',
        padding: '24px 28px',
        marginBottom: 20,
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
              RULELENS™ TRACEABILITY SUITE
            </span>
            <span style={{ fontSize: 12, color: '#94a3b8' }}>
              Statutory Explainability Engine
            </span>
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: '#f8fafc' }}>
            Visual Grounding & Statutory Requirement Audit
          </h2>
          <p style={{ fontSize: 13, color: '#94a3b8', maxWidth: 700, marginTop: 4 }}>
            Direct visual correlation connecting packaging OCR bounding boxes to Legal Metrology clauses, expected statutory conditions, and human inspector review.
          </p>
        </div>

        {/* Case Selector Dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 11, color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>Active Case</div>
            <select
              value={selectedInspectionId}
              onChange={(e) => setSelectedInspectionId(e.target.value)}
              disabled={loadingList}
              style={{
                background: '#1e293b',
                color: 'white',
                border: '1px solid #475569',
                padding: '8px 14px',
                borderRadius: 8,
                fontSize: 13,
                fontWeight: 600,
                marginTop: 4,
                cursor: 'pointer'
              }}
            >
              {inspections.map((insp) => (
                <option key={insp.id} value={insp.id}>
                  {insp.inspection_number} — {insp.commodity_name} ({insp.compliance_status})
                </option>
              ))}
            </select>
          </div>

          <button 
            onClick={fetchRuleLensData}
            className="btn btn-secondary"
            style={{ background: '#334155', color: 'white', borderColor: '#475569', marginTop: 16 }}
            title="Reload case data"
          >
            <RefreshCw size={15} />
          </button>
        </div>
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

      {/* Main Split View */}
      {loadingData ? (
        <div style={{ textAlign: 'center', padding: 80, color: 'var(--text-muted)' }}>
          <RefreshCw size={32} className="spin" style={{ animation: 'spin 1s linear infinite', marginBottom: 16 }} />
          <p style={{ fontSize: 14 }}>Extracting statutory bounding boxes and rule mappings...</p>
        </div>
      ) : ruleLensData && findings.length > 0 ? (
        <div style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          height: '75vh',
          boxShadow: 'var(--shadow-md)'
        }}>
          {/* Sub-header Bar */}
          <div style={{
            padding: '12px 20px',
            borderBottom: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: '#f8fafc'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-main)' }}>
                {ruleLensData.commodity_name}
              </span>
              <span className="badge badge-na">Rule Baseline: {ruleLensData.rule_version}</span>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                {findings.length} Evaluated Rules
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', background: 'white', border: '1px solid var(--border)', borderRadius: 6, padding: '2px 4px' }}>
                <button 
                  onClick={() => setZoomLevel(prev => Math.max(0.6, prev - 0.2))}
                  style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: 4 }}
                  title="Zoom Out"
                >
                  <ZoomOut size={15} />
                </button>
                <span style={{ fontSize: 12, padding: '0 8px', fontWeight: 600 }}>{Math.round(zoomLevel * 100)}%</span>
                <button 
                  onClick={() => setZoomLevel(prev => Math.min(3.0, prev + 0.2))}
                  style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: 4 }}
                  title="Zoom In"
                >
                  <ZoomIn size={15} />
                </button>
              </div>

              {onOpenInspectionDetail && (
                <button 
                  onClick={() => onOpenInspectionDetail(selectedInspectionId)}
                  className="btn btn-secondary"
                  style={{ fontSize: 12, padding: '5px 10px', gap: 4 }}
                >
                  <ExternalLink size={13} /> Full Dossier
                </button>
              )}
            </div>
          </div>

          {/* Split Body */}
          <div style={{ display: 'flex', flexGrow: 1, minHeight: 0 }}>
            {/* Left Canvas Panel */}
            <div style={{
              flex: '1 1 55%',
              background: '#020617',
              padding: 24,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              overflow: 'auto',
              position: 'relative'
            }}>
              {primaryImage ? (
                <div 
                  className="rulelens-canvas-wrapper"
                  style={{
                    transform: `scale(${zoomLevel})`,
                    transformOrigin: 'center center',
                    transition: 'transform 0.15s ease-out'
                  }}
                >
                  <img 
                    src={primaryImage.processed_path || primaryImage.storage_path} 
                    alt="Packaging Evidence" 
                    style={{ maxWidth: '100%', maxHeight: '60vh', display: 'block' }}
                  />

                  {/* Render Bounding Boxes */}
                  {findings.map((f) => {
                    const isSelected = selectedFinding?.id === f.id;
                    return f.evidence_references?.map((ev, idx) => {
                      const bbox = ev.bbox || [0, 0, 0, 0];
                      const left = `${bbox[0] * 100}%`;
                      const top = `${bbox[1] * 100}%`;
                      const width = `${(bbox[2] - bbox[0]) * 100}%`;
                      const height = `${(bbox[3] - bbox[1]) * 100}%`;

                      let borderColor = '#10b981';
                      if (f.final_status === 'FAIL') borderColor = '#ef4444';
                      if (f.final_status === 'UNCERTAIN') borderColor = '#f59e0b';

                      return (
                        <div
                          key={`${f.id}-${idx}`}
                          className={`rulelens-bbox ${isSelected ? 'active' : ''}`}
                          onClick={() => setSelectedFinding(f)}
                          style={{
                            left,
                            top,
                            width,
                            height,
                            borderColor: isSelected ? '#3b82f6' : borderColor,
                            borderWidth: isSelected ? 3 : 2,
                            backgroundColor: isSelected ? 'rgba(59, 130, 246, 0.35)' : undefined
                          }}
                          title={`${f.requirement_title}: ${f.final_status}`}
                        />
                      );
                    });
                  })}
                </div>
              ) : (
                <div style={{ color: '#94a3b8', textAlign: 'center' }}>
                  No evidence photographs available for this case.
                </div>
              )}
            </div>

            {/* Right Details Panel */}
            <div style={{
              flex: '1 1 45%',
              background: 'var(--bg-card)',
              padding: 24,
              overflowY: 'auto',
              borderLeft: '1px solid var(--border)',
              display: 'flex',
              flexDirection: 'column',
              gap: 16
            }}>
              {/* Finding Selection Chips */}
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
                  Statutory Rules Checklist
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {findings.map((f) => (
                    <button
                      key={f.id}
                      onClick={() => setSelectedFinding(f)}
                      style={{
                        padding: '5px 10px',
                        borderRadius: 6,
                        fontSize: 12,
                        fontWeight: 600,
                        cursor: 'pointer',
                        border: selectedFinding?.id === f.id ? '2px solid #2563eb' : '1px solid var(--border)',
                        background: selectedFinding?.id === f.id ? '#eff6ff' : '#f8fafc',
                        color: selectedFinding?.id === f.id ? '#1e40af' : 'var(--text-main)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6
                      }}
                    >
                      <span>{f.clause_reference}</span>
                      <span style={{
                        width: 7,
                        height: 7,
                        borderRadius: '50%',
                        background: f.final_status === 'PASS' ? '#10b981' : f.final_status === 'FAIL' ? '#ef4444' : '#f59e0b'
                      }} />
                    </button>
                  ))}
                </div>
              </div>

              {selectedFinding && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  {/* Selected Card Header */}
                  <div style={{
                    background: '#f8fafc',
                    padding: 16,
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border)'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
                      <span style={{ fontSize: 13, fontWeight: 700, color: '#2563eb' }}>{selectedFinding.clause_reference}</span>
                      {getStatusBadge(selectedFinding.final_status)}
                    </div>
                    <h4 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-main)' }}>{selectedFinding.requirement_title}</h4>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                      Severity: <b>{selectedFinding.severity}</b> | Rule ID: <b>{selectedFinding.rule_id}</b> | Confidence: <b>{Math.round(selectedFinding.confidence * 100)}%</b>
                    </div>
                  </div>

                  {/* Statutory Grounded Explanation */}
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 4 }}>
                      Statutory Clause & Evidence Explanation
                    </div>
                    <p style={{
                      fontSize: 13,
                      color: 'var(--text-main)',
                      lineHeight: 1.5,
                      background: '#fff',
                      padding: 12,
                      border: '1px solid var(--border)',
                      borderRadius: 6
                    }}>
                      {selectedFinding.explanation}
                    </p>
                  </div>

                  {/* Evidence Comparison Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    <div style={{ background: '#f8fafc', padding: 12, borderRadius: 6, border: '1px solid var(--border)' }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                        Observed OCR Value
                      </div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: '#0f172a', marginTop: 4 }}>
                        {selectedFinding.observed_value || <span style={{ color: '#94a3b8' }}>[Not Detected on Package]</span>}
                      </div>
                    </div>

                    <div style={{ background: '#f8fafc', padding: 12, borderRadius: 6, border: '1px solid var(--border)' }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                        Statutory Mandate
                      </div>
                      <div style={{ fontSize: 13, color: '#334155', marginTop: 4 }}>
                        {selectedFinding.expected_condition}
                      </div>
                    </div>
                  </div>

                  {/* Uncertainty Diagnostic */}
                  {selectedFinding.uncertainty_reason && (
                    <div style={{ background: '#fffbeb', border: '1px solid #fcd34d', padding: 12, borderRadius: 6, display: 'flex', gap: 8 }}>
                      <ShieldAlert size={16} color="#b45309" style={{ flexShrink: 0, marginTop: 2 }} />
                      <div style={{ fontSize: 12, color: '#92400e' }}>
                        <b>Uncertainty Diagnostic:</b> {selectedFinding.uncertainty_reason}
                      </div>
                    </div>
                  )}

                  {/* Human Inspector Override Controls */}
                  <div style={{
                    marginTop: 6,
                    padding: 16,
                    background: '#f8fafc',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid #cbd5e1'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                      <Edit3 size={15} color="#2563eb" />
                      <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-main)' }}>Inspector Finding Adjudication</span>
                    </div>

                    {selectedFinding.inspector_status && (
                      <div style={{ fontSize: 12, color: '#475569', marginBottom: 12, background: 'white', padding: 8, borderRadius: 6, border: '1px solid var(--border)' }}>
                        <b>Current Human Decision:</b> {selectedFinding.inspector_status}
                        {selectedFinding.inspector_comment && ` — "${selectedFinding.inspector_comment}"`}
                      </div>
                    )}

                    <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                      {['PASS', 'FAIL', 'UNCERTAIN', 'NOT_APPLICABLE'].map((st) => (
                        <button
                          key={st}
                          onClick={() => setOverrideStatus(st)}
                          style={{
                            flex: 1,
                            padding: '6px 0',
                            borderRadius: 6,
                            fontSize: 12,
                            fontWeight: 700,
                            cursor: 'pointer',
                            border: overrideStatus === st ? '2px solid #2563eb' : '1px solid var(--border)',
                            background: overrideStatus === st ? '#2563eb' : 'white',
                            color: overrideStatus === st ? 'white' : '#334155'
                          }}
                        >
                          {st}
                        </button>
                      ))}
                    </div>

                    <textarea
                      placeholder="Enter statutory justification for override (e.g., physically verified with calibrated micrometer)..."
                      value={overrideComment}
                      onChange={(e) => setOverrideComment(e.target.value)}
                      style={{
                        width: '100%',
                        minHeight: 65,
                        padding: 8,
                        borderRadius: 6,
                        border: '1px solid var(--border)',
                        fontSize: 12,
                        fontFamily: 'inherit',
                        outline: 'none',
                        marginBottom: 10
                      }}
                    />

                    <button
                      onClick={handleApplyOverride}
                      disabled={!overrideStatus || submittingOverride}
                      className="btn btn-primary"
                      style={{ width: '100%', fontSize: 13, padding: '8px 0', opacity: (!overrideStatus || submittingOverride) ? 0.6 : 1 }}
                    >
                      {submittingOverride ? 'Logging Adjudication to Ledger...' : 'Commit Inspector Adjudication'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-lg)',
          border: '1px dashed var(--border)',
          padding: 60,
          textAlign: 'center',
          color: 'var(--text-muted)'
        }}>
          <Eye size={44} style={{ opacity: 0.3, marginBottom: 16 }} />
          <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-main)', marginBottom: 6 }}>
            No Compliance Findings Available
          </h3>
          <p style={{ fontSize: 13, maxWidth: 450, margin: '0 auto 16px' }}>
            Select an inspection case with completed PP-OCRv4 analysis to view RuleLens bounding boxes and explainability.
          </p>
        </div>
      )}
    </div>
  );
};
