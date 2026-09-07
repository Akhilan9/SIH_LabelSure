import React, { useState } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  HelpCircle, 
  MinusCircle, 
  ExternalLink, 
  ZoomIn, 
  ZoomOut, 
  Eye, 
  Edit3,
  ShieldAlert,
  FileCheck
} from 'lucide-react';
import { Finding, InspectionImage, Declaration } from '../types';

interface RuleLensViewerProps {
  image: InspectionImage;
  findings: Finding[];
  declarations: Declaration[];
  onOverrideFinding: (findingId: string, status: string, comment: string) => Promise<void>;
  onClose: () => void;
}

export const RuleLensViewer: React.FC<RuleLensViewerProps> = ({
  image,
  findings,
  declarations,
  onOverrideFinding,
  onClose
}) => {
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(findings[0] || null);
  const [zoomLevel, setZoomLevel] = useState<number>(1.0);
  const [overrideStatus, setOverrideStatus] = useState<string>('');
  const [overrideComment, setOverrideComment] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const handleApplyOverride = async () => {
    if (!selectedFinding || !overrideStatus) return;
    setIsSubmitting(true);
    try {
      await onOverrideFinding(selectedFinding.id, overrideStatus, overrideComment);
      // Update local state
      setSelectedFinding({
        ...selectedFinding,
        inspector_status: overrideStatus as any,
        final_status: overrideStatus as any,
        inspector_comment: overrideComment
      });
      setOverrideStatus('');
      setOverrideComment('');
    } catch (err: any) {
      alert(`Error applying override: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

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
    <div className="modal-overlay" onClick={onClose}>
      <div 
        className="modal-content" 
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: 1100, width: '95%', height: '88vh', display: 'flex', flexDirection: 'column' }}
      >
        {/* Modal Header */}
        <div style={{
          padding: '16px 24px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: '#0f172a',
          color: 'white',
          borderTopLeftRadius: 'var(--radius-lg)',
          borderTopRightRadius: 'var(--radius-lg)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              background: 'rgba(37, 99, 235, 0.2)',
              border: '1px solid #3b82f6',
              padding: 6,
              borderRadius: 8
            }}>
              <Eye size={18} color="#60a5fa" />
            </div>
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 700 }}>RuleLens™ Visual Compliance Inspector</h3>
              <p style={{ fontSize: 11, color: '#94a3b8' }}>
                Image View: {image.view_type} | Resolution: {image.width}x{image.height} px | Hash: {image.sha256_hash.slice(0, 12)}...
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', background: '#1e293b', borderRadius: 6, padding: 2 }}>
              <button 
                onClick={() => setZoomLevel(prev => Math.max(0.75, prev - 0.2))}
                style={{ background: 'transparent', border: 'none', color: 'white', padding: 6, cursor: 'pointer' }}
                title="Zoom Out"
              >
                <ZoomOut size={16} />
              </button>
              <span style={{ fontSize: 12, padding: '0 8px', color: '#cbd5e1' }}>{Math.round(zoomLevel * 100)}%</span>
              <button 
                onClick={() => setZoomLevel(prev => Math.min(2.5, prev + 0.2))}
                style={{ background: 'transparent', border: 'none', color: 'white', padding: 6, cursor: 'pointer' }}
                title="Zoom In"
              >
                <ZoomIn size={16} />
              </button>
            </div>

            <button 
              onClick={onClose}
              style={{ background: '#334155', border: 'none', color: 'white', borderRadius: 6, padding: '6px 12px', cursor: 'pointer', fontSize: 13 }}
            >
              Close
            </button>
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
            overflow: 'auto'
          }}>
            <div 
              className="rulelens-canvas-wrapper"
              style={{
                transform: `scale(${zoomLevel})`,
                transformOrigin: 'center center',
                transition: 'transform 0.15s ease-out'
              }}
            >
              <img 
                src={image.processed_path || image.storage_path} 
                alt="Package Label Evidence" 
                style={{ maxWidth: '100%', maxHeight: '65vh', display: 'block' }}
              />

              {/* Render Bounding Boxes for Findings */}
              {findings.map((f) => {
                const isSelected = selectedFinding?.id === f.id;
                return f.evidence_references?.map((ev, idx) => {
                  const bbox = ev.bbox || [0, 0, 0, 0]; // [x1, y1, x2, y2]
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
            gap: 20
          }}>
            {/* Finding Selector Chips */}
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
                Select Requirement Card
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {findings.map((f) => (
                  <button
                    key={f.id}
                    onClick={() => setSelectedFinding(f)}
                    style={{
                      padding: '4px 8px',
                      borderRadius: 6,
                      fontSize: 11,
                      fontWeight: 600,
                      cursor: 'pointer',
                      border: selectedFinding?.id === f.id ? '2px solid #2563eb' : '1px solid var(--border)',
                      background: selectedFinding?.id === f.id ? '#eff6ff' : '#f8fafc',
                      color: selectedFinding?.id === f.id ? '#1e40af' : 'var(--text-main)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4
                    }}
                  >
                    <span>{f.clause_reference}</span>
                    <span style={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      background: f.final_status === 'PASS' ? '#10b981' : f.final_status === 'FAIL' ? '#ef4444' : '#f59e0b'
                    }} />
                  </button>
                ))}
              </div>
            </div>

            {selectedFinding ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {/* Header */}
                <div style={{
                  background: '#f8fafc',
                  padding: 16,
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
                    <span style={{ fontSize: 12, fontWeight: 700, color: '#2563eb' }}>{selectedFinding.clause_reference}</span>
                    {getStatusBadge(selectedFinding.final_status)}
                  </div>
                  <h4 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-main)' }}>{selectedFinding.requirement_title}</h4>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                    Severity: <b>{selectedFinding.severity}</b> | Rule Version: <b>{selectedFinding.rule_version}</b> | Confidence: <b>{Math.round(selectedFinding.confidence * 100)}%</b>
                  </div>
                </div>

                {/* Statutory Explanation */}
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 4 }}>
                    Statutory Explanation
                  </div>
                  <p style={{ fontSize: 13, color: 'var(--text-main)', lineHeight: 1.5, background: '#fff', padding: 10, border: '1px solid var(--border)', borderRadius: 6 }}>
                    {selectedFinding.explanation}
                  </p>
                </div>

                {/* Evidence Comparison Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div style={{ background: '#f8fafc', padding: 12, borderRadius: 6, border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Observed Evidence</div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#0f172a', marginTop: 4 }}>
                      {selectedFinding.observed_value || '[Not Detected]'}
                    </div>
                  </div>
                  <div style={{ background: '#f8fafc', padding: 12, borderRadius: 6, border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Statutory Expectation</div>
                    <div style={{ fontSize: 13, color: '#334155', marginTop: 4 }}>
                      {selectedFinding.expected_condition}
                    </div>
                  </div>
                </div>

                {/* Uncertainty Reason if applicable */}
                {selectedFinding.uncertainty_reason && (
                  <div style={{ background: '#fffbeb', border: '1px solid #fcd34d', padding: 12, borderRadius: 6, display: 'flex', gap: 8 }}>
                    <ShieldAlert size={16} color="#b45309" style={{ flexShrink: 0, marginTop: 2 }} />
                    <div style={{ fontSize: 12, color: '#92400e' }}>
                      <b>Uncertainty Diagnostic:</b> {selectedFinding.uncertainty_reason}
                    </div>
                  </div>
                )}

                {/* Inspector Human Review & Override Panel */}
                <div style={{
                  marginTop: 10,
                  padding: 16,
                  background: '#f8fafc',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid #cbd5e1'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <Edit3 size={15} color="#2563eb" />
                    <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-main)' }}>Inspector Adjudication & Override</span>
                  </div>

                  {selectedFinding.inspector_status && (
                    <div style={{ fontSize: 12, color: '#475569', marginBottom: 12, background: 'white', padding: 8, borderRadius: 6, border: '1px solid var(--border)' }}>
                      <b>Previous Human Decision:</b> {selectedFinding.inspector_status}
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
                          fontWeight: 600,
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
                    placeholder="Enter statutory justification for override (e.g. verified with manual physical micrometer or physical batch documents)..."
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
                    disabled={!overrideStatus || isSubmitting}
                    className="btn btn-primary"
                    style={{ width: '100%', fontSize: 13, padding: '8px 0', opacity: (!overrideStatus || isSubmitting) ? 0.6 : 1 }}
                  >
                    {isSubmitting ? 'Logging to Audit Ledger...' : 'Commit Inspector Adjudication'}
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                Select a requirement card to inspect evidence and apply statutory review.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
