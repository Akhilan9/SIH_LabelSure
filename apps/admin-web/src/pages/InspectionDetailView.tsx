import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  Play, 
  FileDown, 
  Upload, 
  CheckCircle2, 
  XCircle, 
  HelpCircle, 
  MinusCircle, 
  Eye, 
  Edit, 
  ShieldCheck, 
  AlertTriangle,
  FileCheck,
  Camera,
  Layers,
  Sparkles,
  Plus,
  RefreshCw,
  X,
  Save,
  Sliders
} from 'lucide-react';
import { api } from '../api/client';
import { RuleLensViewer } from '../components/RuleLensViewer';
import { InspectionImage, Declaration, Finding } from '../types';

interface InspectionDetailViewProps {
  inspectionId: string;
  onBack: () => void;
}

export const InspectionDetailView: React.FC<InspectionDetailViewProps> = ({
  inspectionId,
  onBack
}) => {
  const [inspection, setInspection] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'findings' | 'declarations' | 'images'>('findings');
  const [loading, setLoading] = useState<boolean>(true);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [generatingReport, setGeneratingReport] = useState<boolean>(false);

  // Upload State
  const [uploadViewType, setUploadViewType] = useState<string>('FRONT');
  const [isUploading, setIsUploading] = useState<boolean>(false);

  // RuleLens Viewer State
  const [ruleLensImage, setRuleLensImage] = useState<InspectionImage | null>(null);

  // Context Modal State
  const [showContextModal, setShowContextModal] = useState<boolean>(false);
  const [contextForm, setContextForm] = useState<any>({
    commodity_category: 'FOOD',
    is_food: true,
    is_imported: false,
    origin_country: 'India',
    package_type: 'STANDARD',
    declared_net_quantity: '',
    declared_unit: 'g',
    is_ecommerce: false
  });
  const [savingContext, setSavingContext] = useState<boolean>(false);

  // Declarations Edit / Add Modal State
  const [declModalOpen, setDeclModalOpen] = useState<boolean>(false);
  const [editingDeclId, setEditingDeclId] = useState<string | null>(null);
  const [declForm, setDeclForm] = useState<{ category: string; raw_text: string; unit: string }>({
    category: 'COMMON_GENERIC_NAME',
    raw_text: '',
    unit: ''
  });
  const [savingDecl, setSavingDecl] = useState<boolean>(false);

  // Quick Adjudication Modal State
  const [quickFinding, setQuickFinding] = useState<Finding | null>(null);
  const [quickStatus, setQuickStatus] = useState<string>('PASS');
  const [quickComment, setQuickComment] = useState<string>('');
  const [savingQuickOverride, setSavingQuickOverride] = useState<boolean>(false);

  const fetchDetails = () => {
    setLoading(true);
    api.getInspection(inspectionId)
      .then(setInspection)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchDetails();
  }, [inspectionId]);

  const handleRunAnalysis = async () => {
    if (!inspection || inspection.images?.length === 0) {
      alert('Please upload at least one package photograph before running analysis.');
      return;
    }
    setAnalyzing(true);
    try {
      await api.triggerAnalysis(inspectionId);
      fetchDetails();
    } catch (err: any) {
      alert(`Analysis failed: ${err.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    try {
      await api.uploadImage(inspectionId, file, uploadViewType);
      fetchDetails();
    } catch (err: any) {
      alert(`Upload error: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleGenerateReport = async () => {
    setGeneratingReport(true);
    try {
      const rep = await api.generateReport(inspectionId);
      window.open(rep.pdf_url, '_blank');
      fetchDetails();
    } catch (err: any) {
      alert(`Report error: ${err.message}`);
    } finally {
      setGeneratingReport(false);
    }
  };

  const handleOverrideFinding = async (findingId: string, status: string, comment: string) => {
    await api.overrideFinding(findingId, status, comment);
    fetchDetails();
  };

  const handleFinalize = async () => {
    if (!confirm('Are you sure you want to finalize this inspection case? This action will freeze findings into the compliance certificate.')) {
      return;
    }
    try {
      await api.finalizeInspection(inspectionId);
      fetchDetails();
    } catch (err: any) {
      alert(`Finalization error: ${err.message}`);
    }
  };

  // Product Context Handlers
  const handleOpenContextModal = async () => {
    try {
      const ctx = await api.getInspectionContext(inspectionId);
      setContextForm({
        commodity_category: ctx.commodity_category || 'FOOD',
        is_food: ctx.is_food ?? true,
        is_imported: ctx.is_imported ?? false,
        origin_country: ctx.origin_country || 'India',
        package_type: ctx.package_type || 'STANDARD',
        declared_net_quantity: ctx.declared_net_quantity !== null ? String(ctx.declared_net_quantity) : '',
        declared_unit: ctx.declared_unit || 'g',
        is_ecommerce: ctx.is_ecommerce ?? false
      });
      setShowContextModal(true);
    } catch (err: any) {
      // If context endpoint 404s, use defaults from inspection
      setContextForm({
        commodity_category: 'FOOD',
        is_food: true,
        is_imported: false,
        origin_country: 'India',
        package_type: 'STANDARD',
        declared_net_quantity: '',
        declared_unit: 'g',
        is_ecommerce: false
      });
      setShowContextModal(true);
    }
  };

  const handleSaveContext = async () => {
    setSavingContext(true);
    try {
      await api.updateInspectionContext(inspectionId, {
        commodity_category: contextForm.commodity_category,
        is_food: contextForm.is_food,
        is_imported: contextForm.is_imported,
        origin_country: contextForm.origin_country,
        package_type: contextForm.package_type,
        declared_net_quantity: contextForm.declared_net_quantity ? parseFloat(contextForm.declared_net_quantity) : null,
        declared_unit: contextForm.declared_unit,
        is_ecommerce: contextForm.is_ecommerce
      });
      setShowContextModal(false);
      fetchDetails();
    } catch (err: any) {
      alert(`Failed to save product context: ${err.message}`);
    } finally {
      setSavingContext(false);
    }
  };

  // Declaration Handlers
  const handleOpenEditDecl = (d: Declaration) => {
    setEditingDeclId(d.id);
    setDeclForm({
      category: d.category,
      raw_text: d.raw_text,
      unit: d.unit || ''
    });
    setDeclModalOpen(true);
  };

  const handleOpenAddDecl = () => {
    setEditingDeclId(null);
    setDeclForm({
      category: 'COMMON_GENERIC_NAME',
      raw_text: '',
      unit: ''
    });
    setDeclModalOpen(true);
  };

  const handleSaveDecl = async () => {
    if (!declForm.raw_text.trim()) {
      alert('Declaration text cannot be empty.');
      return;
    }
    setSavingDecl(true);
    try {
      if (editingDeclId) {
        await api.updateDeclaration(editingDeclId, {
          category: declForm.category,
          raw_text: declForm.raw_text,
          unit: declForm.unit || undefined
        });
      } else {
        await api.createDeclaration(inspectionId, {
          category: declForm.category,
          raw_text: declForm.raw_text,
          unit: declForm.unit || undefined,
          source_image_id: images[0]?.id || null
        });
      }
      setDeclModalOpen(false);
      fetchDetails();
    } catch (err: any) {
      alert(`Failed to save declaration: ${err.message}`);
    } finally {
      setSavingDecl(false);
    }
  };

  // Quick Adjudication Handlers
  const handleOpenQuickOverride = (finding: Finding, status: string) => {
    setQuickFinding(finding);
    setQuickStatus(status);
    setQuickComment(finding.inspector_comment || '');
  };

  const handleSaveQuickOverride = async () => {
    if (!quickFinding) return;
    setSavingQuickOverride(true);
    try {
      await api.overrideFinding(quickFinding.id, quickStatus, quickComment);
      setQuickFinding(null);
      fetchDetails();
    } catch (err: any) {
      alert(`Failed to record adjudication: ${err.message}`);
    } finally {
      setSavingQuickOverride(false);
    }
  };

  if (loading && !inspection) {
    return <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Loading inspection case...</div>;
  }

  const findings: Finding[] = inspection?.findings || [];
  const declarations: Declaration[] = inspection?.declarations || [];
  const images: InspectionImage[] = inspection?.images || [];

  return (
    <div className="page-body">
      {/* Top Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <button 
          onClick={onBack}
          className="btn btn-secondary"
          style={{ gap: 6, padding: '6px 12px' }}
        >
          <ArrowLeft size={16} /> Back to Inspections
        </button>

        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button 
            onClick={handleRunAnalysis}
            disabled={analyzing || images.length === 0}
            className="btn btn-primary"
            style={{ gap: 8, background: '#1d4ed8' }}
          >
            <Sparkles size={16} />
            {analyzing ? 'Analyzing with PP-OCRv4 & Rule Engine...' : 'Run Compliance Analysis'}
          </button>

          <button 
            onClick={handleGenerateReport}
            disabled={generatingReport || findings.length === 0}
            className="btn btn-secondary"
            style={{ gap: 8 }}
          >
            <FileDown size={16} />
            {generatingReport ? 'Generating Certificate...' : 'Download Official PDF Report'}
          </button>

          {inspection?.status !== 'FINALIZED' && (
            <button 
              onClick={handleFinalize}
              disabled={findings.length === 0}
              className="btn btn-secondary"
              style={{ gap: 8, color: '#15803d', borderColor: '#86efac', background: '#f0fdf4' }}
            >
              <FileCheck size={16} /> Finalize Inspection
            </button>
          )}
        </div>
      </div>

      {/* Case Header Card */}
      <div style={{
        background: 'var(--bg-card)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border)',
        padding: 24,
        marginBottom: 24,
        boxShadow: 'var(--shadow-sm)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <h2 style={{ fontSize: 22, fontWeight: 700 }}>{inspection?.inspection_number}</h2>
              <span className="badge badge-na">{inspection?.status}</span>
            </div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#1e293b', marginTop: 4 }}>
              {inspection?.commodity_name} {inspection?.brand_name && `(${inspection.brand_name})`}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
              Inspecting Officer: <b>{inspection?.inspector_name}</b> | Rule Baseline: <b>{inspection?.rule_version}</b> | Date: <b>{new Date(inspection?.created_at).toLocaleDateString()}</b>
            </div>

            <div style={{ marginTop: 12 }}>
              <button 
                onClick={handleOpenContextModal}
                className="btn btn-secondary"
                style={{ fontSize: 12, padding: '5px 12px', gap: 6, borderColor: '#cbd5e1' }}
              >
                <Sliders size={14} /> Edit Product Context
              </button>
            </div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>
              Compliance Verdict
            </div>
            <div>
              {inspection?.compliance_status === 'COMPLIANT' && (
                <span className="badge badge-pass" style={{ fontSize: 14, padding: '6px 14px' }}>
                  <CheckCircle2 size={16} /> COMPLIANT
                </span>
              )}
              {inspection?.compliance_status === 'NON_COMPLIANT' && (
                <span className="badge badge-fail" style={{ fontSize: 14, padding: '6px 14px' }}>
                  <XCircle size={16} /> NON-COMPLIANT
                </span>
              )}
              {inspection?.compliance_status === 'REQUIRES_REVIEW' && (
                <span className="badge badge-uncertain" style={{ fontSize: 14, padding: '6px 14px' }}>
                  <HelpCircle size={16} /> REQUIRES REVIEW
                </span>
              )}
              {inspection?.compliance_status === 'PENDING' && (
                <span className="badge badge-na" style={{ fontSize: 14, padding: '6px 14px' }}>
                  PENDING ANALYSIS
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Findings Summary Pills */}
        <div style={{ display: 'flex', gap: 12, marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--border)', flexWrap: 'wrap' }}>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
            <b>Rules Breakdown:</b>
          </div>
          <span className="badge badge-pass">{inspection?.findings_summary?.pass || 0} Pass</span>
          <span className="badge badge-fail">{inspection?.findings_summary?.fail || 0} Fail</span>
          <span className="badge badge-uncertain">{inspection?.findings_summary?.uncertain || 0} Uncertain</span>
          <span className="badge badge-na">{inspection?.findings_summary?.not_applicable || 0} N/A</span>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 12, borderBottom: '1px solid var(--border)', marginBottom: 20 }}>
        <button 
          onClick={() => setActiveTab('findings')}
          style={{
            padding: '10px 16px',
            border: 'none',
            background: 'transparent',
            fontSize: 14,
            fontWeight: 600,
            cursor: 'pointer',
            borderBottom: activeTab === 'findings' ? '2px solid var(--primary)' : '2px solid transparent',
            color: activeTab === 'findings' ? 'var(--primary)' : 'var(--text-muted)'
          }}
        >
          Compliance Findings ({findings.length})
        </button>

        <button 
          onClick={() => setActiveTab('declarations')}
          style={{
            padding: '10px 16px',
            border: 'none',
            background: 'transparent',
            fontSize: 14,
            fontWeight: 600,
            cursor: 'pointer',
            borderBottom: activeTab === 'declarations' ? '2px solid var(--primary)' : '2px solid transparent',
            color: activeTab === 'declarations' ? 'var(--primary)' : 'var(--text-muted)'
          }}
        >
          Extracted Declarations ({declarations.length})
        </button>

        <button 
          onClick={() => setActiveTab('images')}
          style={{
            padding: '10px 16px',
            border: 'none',
            background: 'transparent',
            fontSize: 14,
            fontWeight: 600,
            cursor: 'pointer',
            borderBottom: activeTab === 'images' ? '2px solid var(--primary)' : '2px solid transparent',
            color: activeTab === 'images' ? 'var(--primary)' : 'var(--text-muted)'
          }}
        >
          Package Photographs ({images.length})
        </button>
      </div>

      {/* Tab 1: Findings Matrix */}
      {activeTab === 'findings' && (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Clause Reference</th>
                <th>Statutory Requirement</th>
                <th>Observed Value</th>
                <th>Expected Condition</th>
                <th>Severity</th>
                <th>AI Verdict</th>
                <th>Inspector Verdict</th>
                <th>Adjudicate & RuleLens</th>
              </tr>
            </thead>
            <tbody>
              {findings.length > 0 ? (
                findings.map((f) => (
                  <tr key={f.id}>
                    <td style={{ fontWeight: 600, color: '#2563eb' }}>{f.clause_reference}</td>
                    <td style={{ fontWeight: 600 }}>{f.requirement_title}</td>
                    <td style={{ fontSize: 13, color: '#0f172a' }}>
                      {f.observed_value || <span style={{ color: '#94a3b8' }}>[Missing]</span>}
                    </td>
                    <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{f.expected_condition}</td>
                    <td>
                      <span className={`badge ${f.severity === 'CRITICAL' ? 'badge-fail' : 'badge-na'}`}>
                        {f.severity}
                      </span>
                    </td>
                    <td>
                      {f.ai_status === 'PASS' && <span className="badge badge-pass">PASS</span>}
                      {f.ai_status === 'FAIL' && <span className="badge badge-fail">FAIL</span>}
                      {f.ai_status === 'UNCERTAIN' && <span className="badge badge-uncertain">UNCERTAIN</span>}
                      {f.ai_status === 'NOT_APPLICABLE' && <span className="badge badge-na">N/A</span>}
                    </td>
                    <td>
                      {f.inspector_status ? (
                        <div>
                          <span className="badge" style={{ background: '#e0e7ff', color: '#3730a3', border: '1px solid #c7d2fe' }}>
                            {f.inspector_status} (Override)
                          </span>
                          {f.inspector_comment && (
                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={f.inspector_comment}>
                              "{f.inspector_comment}"
                            </div>
                          )}
                        </div>
                      ) : (
                        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Auto-Adjudicated</span>
                      )}
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <button 
                          onClick={() => {
                            if (images.length > 0) setRuleLensImage(images[0]);
                          }}
                          className="btn btn-secondary"
                          style={{ padding: '4px 8px', fontSize: 12, gap: 4 }}
                          title="Open Visual RuleLens"
                        >
                          <Eye size={13} /> RuleLens
                        </button>

                        <button 
                          onClick={() => handleOpenQuickOverride(f, 'PASS')}
                          className="btn btn-secondary"
                          style={{ padding: '4px 6px', color: '#16a34a' }}
                          title="Accept Finding (PASS)"
                        >
                          <CheckCircle2 size={15} />
                        </button>

                        <button 
                          onClick={() => handleOpenQuickOverride(f, 'FAIL')}
                          className="btn btn-secondary"
                          style={{ padding: '4px 6px', color: '#dc2626' }}
                          title="Reject Finding (FAIL)"
                        >
                          <XCircle size={15} />
                        </button>

                        <button 
                          onClick={() => handleOpenQuickOverride(f, 'UNCERTAIN')}
                          className="btn btn-secondary"
                          style={{ padding: '4px 6px', color: '#d97706' }}
                          title="Mark Finding Uncertain"
                        >
                          <HelpCircle size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                    No findings generated yet. Click "Run Compliance Analysis" above to evaluate regulatory rules.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 2: Declarations */}
      {activeTab === 'declarations' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: 0 }}>
              Statutory declarations extracted from packaging evidence via PP-OCRv4 and pattern recognition.
            </p>
            <button 
              onClick={handleOpenAddDecl}
              className="btn btn-primary"
              style={{ fontSize: 12, gap: 6, padding: '6px 12px' }}
            >
              <Plus size={14} /> Add Manual Declaration
            </button>
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Raw Declaration Text</th>
                  <th>Confidence</th>
                  <th>Extraction Method</th>
                  <th>Audit Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {declarations.length > 0 ? (
                  declarations.map((d) => (
                    <tr key={d.id}>
                      <td style={{ fontWeight: 600, color: '#2563eb' }}>{d.category}</td>
                      <td style={{ fontSize: 13, fontWeight: 500 }}>{d.raw_text}</td>
                      <td>
                        <span className="badge badge-pass">{Math.round(d.confidence * 100)}%</span>
                      </td>
                      <td>
                        <span className="badge badge-na">{d.extraction_method}</span>
                      </td>
                      <td>
                        {d.is_inspector_edited ? (
                          <span className="badge badge-uncertain">Inspector Edited</span>
                        ) : (
                          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Original AI Extraction</span>
                        )}
                      </td>
                      <td>
                        <button 
                          onClick={() => handleOpenEditDecl(d)}
                          className="btn btn-secondary"
                          style={{ padding: '4px 8px', fontSize: 12, gap: 4 }}
                        >
                          <Edit size={12} /> Edit
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                      No declarations extracted yet. Upload package photos and trigger analysis.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Images & Upload */}
      {activeTab === 'images' && (
        <div>
          {/* Uploader Card */}
          <div style={{
            background: 'var(--bg-card)',
            padding: 20,
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border)',
            marginBottom: 24,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 16
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
              <select
                value={uploadViewType}
                onChange={(e) => setUploadViewType(e.target.value)}
                style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13 }}
              >
                <option value="FRONT">Front Panel</option>
                <option value="BACK">Back Panel (Declarations)</option>
                <option value="SIDE">Side Panel</option>
                <option value="TOP">Top / Cap</option>
                <option value="BOTTOM">Bottom</option>
                <option value="MRP_PANEL">MRP / Net Quantity Close-Up</option>
              </select>

              <label className="btn btn-primary" style={{ cursor: 'pointer', gap: 8 }}>
                <Camera size={16} />
                {isUploading ? 'Uploading & Preprocessing...' : 'Upload Additional Evidence'}
                <input 
                  type="file" 
                  accept="image/jpeg,image/png,image/webp" 
                  onChange={handleFileUpload} 
                  style={{ display: 'none' }} 
                  disabled={isUploading}
                />
              </label>

              <button 
                onClick={handleRunAnalysis}
                disabled={analyzing || images.length === 0}
                className="btn btn-secondary"
                style={{ gap: 6, fontSize: 13 }}
              >
                <RefreshCw size={14} /> Rerun Analysis
              </button>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Supports JPG, PNG, WebP up to 25MB. Images are cryptographically hashed with SHA-256.
            </div>
          </div>

          {/* Image Cards Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20 }}>
            {images.map((img) => {
              const q = img.quality_assessment;
              return (
                <div key={img.id} style={{
                  background: 'var(--bg-card)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border)',
                  overflow: 'hidden',
                  boxShadow: 'var(--shadow-sm)'
                }}>
                  <div style={{ height: 220, background: '#020617', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <img 
                      src={img.processed_path || img.storage_path} 
                      alt={img.view_type} 
                      style={{ maxHeight: '100%', maxWidth: '100%', objectFit: 'contain' }}
                    />
                  </div>
                  <div style={{ padding: 16 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <span className="badge badge-na" style={{ fontWeight: 700 }}>{img.view_type} VIEW</span>
                      {img.is_acceptable ? (
                        <span className="badge badge-pass"><CheckCircle2 size={12} /> Clear Evidence</span>
                      ) : (
                        <span className="badge badge-uncertain"><AlertTriangle size={12} /> Quality Warning</span>
                      )}
                    </div>

                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>
                      Resolution: <b>{img.width}x{img.height} px</b> | Blur: <b>{q?.blur_score || 0}</b> | Quality: <b>{Math.round((q?.quality_score || 0) * 100)}%</b>
                    </div>

                    {q?.warnings && q.warnings.length > 0 && (
                      <div style={{ background: '#fef2f2', border: '1px solid #fecaca', padding: 8, borderRadius: 6, marginBottom: 12 }}>
                        {q.warnings.map((w, i) => (
                          <div key={i} style={{ fontSize: 11, color: '#b91c1c' }}>• {w}</div>
                        ))}
                      </div>
                    )}

                    <button 
                      onClick={() => setRuleLensImage(img)}
                      className="btn btn-secondary"
                      style={{ width: '100%', justifyContent: 'center', gap: 6, fontSize: 13 }}
                    >
                      <Eye size={15} /> Inspect in RuleLens
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Product Context Modal */}
      {showContextModal && (
        <div className="modal-overlay" onClick={() => setShowContextModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 540 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ fontSize: 17, fontWeight: 700 }}>Edit Product Regulatory Context</h3>
              <button onClick={() => setShowContextModal(false)} style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Commodity Category</label>
                <select
                  value={contextForm.commodity_category}
                  onChange={(e) => setContextForm({ ...contextForm, commodity_category: e.target.value })}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', marginTop: 4 }}
                >
                  <option value="FOOD">Food / Edible Product</option>
                  <option value="NON_FOOD">Non-Food Package</option>
                  <option value="COSMETIC">Cosmetic & Personal Care</option>
                  <option value="MEDICAL_DEVICE">Medical Device</option>
                  <option value="ELECTRONICS">Electronics & Electrical</option>
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Package Type</label>
                  <select
                    value={contextForm.package_type}
                    onChange={(e) => setContextForm({ ...contextForm, package_type: e.target.value })}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', marginTop: 4 }}
                  >
                    <option value="STANDARD">Standard Retail Package</option>
                    <option value="COMBINATION">Combination Package</option>
                    <option value="GROUP">Group Package</option>
                    <option value="MULTI_PIECE">Multi-Piece Package</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Origin Country</label>
                  <input
                    type="text"
                    value={contextForm.origin_country}
                    onChange={(e) => setContextForm({ ...contextForm, origin_country: e.target.value })}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', marginTop: 4 }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Declared Net Quantity</label>
                  <input
                    type="number"
                    step="any"
                    value={contextForm.declared_net_quantity}
                    onChange={(e) => setContextForm({ ...contextForm, declared_net_quantity: e.target.value })}
                    placeholder="e.g. 500"
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', marginTop: 4 }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Declared Unit</label>
                  <input
                    type="text"
                    value={contextForm.declared_unit}
                    onChange={(e) => setContextForm({ ...contextForm, declared_unit: e.target.value })}
                    placeholder="g, ml, kg..."
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', marginTop: 4 }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: 16, marginTop: 4 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={contextForm.is_food}
                    onChange={(e) => setContextForm({ ...contextForm, is_food: e.target.checked })}
                  />
                  Is Food Item
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={contextForm.is_imported}
                    onChange={(e) => setContextForm({ ...contextForm, is_imported: e.target.checked })}
                  />
                  Is Imported Commodity
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={contextForm.is_ecommerce}
                    onChange={(e) => setContextForm({ ...contextForm, is_ecommerce: e.target.checked })}
                  />
                  E-Commerce Listing
                </label>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 16 }}>
                <button 
                  onClick={() => setShowContextModal(false)}
                  className="btn btn-secondary"
                  disabled={savingContext}
                >
                  Cancel
                </button>
                <button 
                  onClick={handleSaveContext}
                  className="btn btn-primary"
                  disabled={savingContext}
                >
                  {savingContext ? 'Saving...' : 'Save Product Context'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Declaration Edit / Add Modal */}
      {declModalOpen && (
        <div className="modal-overlay" onClick={() => setDeclModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 500 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ fontSize: 17, fontWeight: 700 }}>
                {editingDeclId ? 'Edit Declaration' : 'Add Manual Declaration'}
              </h3>
              <button onClick={() => setDeclModalOpen(false)} style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Declaration Category</label>
                <select
                  value={declForm.category}
                  onChange={(e) => setDeclForm({ ...declForm, category: e.target.value })}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', marginTop: 4 }}
                >
                  <option value="MANUFACTURER">Manufacturer</option>
                  <option value="PACKER">Packer</option>
                  <option value="IMPORTER">Importer</option>
                  <option value="COUNTRY_OF_ORIGIN">Country of Origin</option>
                  <option value="COMMON_GENERIC_NAME">Common / Generic Name</option>
                  <option value="NET_QUANTITY">Net Quantity</option>
                  <option value="MRP">Maximum Retail Price (MRP)</option>
                  <option value="MANUFACTURE_DATE">Date of Manufacture</option>
                  <option value="PACK_DATE">Date of Packing</option>
                  <option value="BEST_BEFORE">Best Before</option>
                  <option value="USE_BY">Use By</option>
                  <option value="CONSUMER_CARE">Consumer Care Details</option>
                  <option value="UNIT_SALE_PRICE">Unit Sale Price (USP)</option>
                  <option value="DIMENSIONS">Package Dimensions</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Raw Declaration Text</label>
                <textarea
                  value={declForm.raw_text}
                  onChange={(e) => setDeclForm({ ...declForm, raw_text: e.target.value })}
                  placeholder="Enter verbatim or extracted declaration text..."
                  style={{
                    width: '100%',
                    minHeight: 80,
                    padding: '8px 12px',
                    borderRadius: 6,
                    border: '1px solid var(--border)',
                    marginTop: 4,
                    fontFamily: 'inherit',
                    fontSize: 13
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Measurement Unit (Optional)</label>
                <input
                  type="text"
                  value={declForm.unit}
                  onChange={(e) => setDeclForm({ ...declForm, unit: e.target.value })}
                  placeholder="e.g. g, ml, kg, cm"
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', marginTop: 4 }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 16 }}>
                <button 
                  onClick={() => setDeclModalOpen(false)}
                  className="btn btn-secondary"
                  disabled={savingDecl}
                >
                  Cancel
                </button>
                <button 
                  onClick={handleSaveDecl}
                  className="btn btn-primary"
                  disabled={savingDecl}
                >
                  {savingDecl ? 'Saving...' : 'Commit Declaration'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Adjudication / Override Modal */}
      {quickFinding && (
        <div className="modal-overlay" onClick={() => setQuickFinding(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 520 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ fontSize: 17, fontWeight: 700 }}>Inspector Finding Adjudication</h3>
              <button onClick={() => setQuickFinding(null)} style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <div style={{ background: '#f8fafc', padding: 12, borderRadius: 6, border: '1px solid var(--border)', marginBottom: 14 }}>
              <div style={{ fontSize: 12, color: '#2563eb', fontWeight: 700 }}>{quickFinding.clause_reference}</div>
              <div style={{ fontSize: 14, fontWeight: 600, marginTop: 2 }}>{quickFinding.requirement_title}</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                AI Verdict: <b>{quickFinding.ai_status}</b> | Observed: <b>{quickFinding.observed_value || '[Missing]'}</b>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Inspector Verdict Override</label>
                <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
                  {['PASS', 'FAIL', 'UNCERTAIN', 'NOT_APPLICABLE'].map((st) => (
                    <button
                      key={st}
                      type="button"
                      onClick={() => setQuickStatus(st)}
                      style={{
                        flex: 1,
                        padding: '8px 0',
                        borderRadius: 6,
                        fontSize: 12,
                        fontWeight: 700,
                        cursor: 'pointer',
                        border: quickStatus === st ? '2px solid #2563eb' : '1px solid var(--border)',
                        background: quickStatus === st ? '#2563eb' : 'white',
                        color: quickStatus === st ? 'white' : 'var(--text-main)'
                      }}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Statutory Inspector Comment / Justification</label>
                <textarea
                  value={quickComment}
                  onChange={(e) => setQuickComment(e.target.value)}
                  placeholder="Enter statutory justification (e.g. verified with manual physical micrometer or physical batch documents)..."
                  style={{
                    width: '100%',
                    minHeight: 80,
                    padding: '8px 12px',
                    borderRadius: 6,
                    border: '1px solid var(--border)',
                    marginTop: 4,
                    fontFamily: 'inherit',
                    fontSize: 12
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 14 }}>
                <button 
                  onClick={() => setQuickFinding(null)}
                  className="btn btn-secondary"
                  disabled={savingQuickOverride}
                >
                  Cancel
                </button>
                <button 
                  onClick={handleSaveQuickOverride}
                  className="btn btn-primary"
                  disabled={savingQuickOverride}
                >
                  {savingQuickOverride ? 'Logging to Audit Trail...' : 'Commit Adjudication'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* RuleLens Interactive Modal */}
      {ruleLensImage && (
        <RuleLensViewer 
          image={ruleLensImage}
          findings={findings}
          declarations={declarations}
          onOverrideFinding={handleOverrideFinding}
          onClose={() => setRuleLensImage(null)}
        />
      )}
    </div>
  );
};
