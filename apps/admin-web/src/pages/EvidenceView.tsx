import React, { useState, useEffect } from 'react';
import { 
  Camera, 
  Search, 
  Filter, 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  AlertTriangle, 
  CheckCircle2, 
  ShieldCheck, 
  Eye, 
  FileText, 
  Hash, 
  Calendar,
  X,
  RefreshCw
} from 'lucide-react';
import { api } from '../api/client';
import { InspectionImage } from '../types';

interface EvidenceViewProps {
  onOpenInspection?: (inspectionId: string) => void;
}

export const EvidenceView: React.FC<EvidenceViewProps> = ({ onOpenInspection }) => {
  const [images, setImages] = useState<InspectionImage[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [viewTypeFilter, setViewTypeFilter] = useState<string>('ALL');
  const [qualityFilter, setQualityFilter] = useState<string>('ALL');
  const [selectedImage, setSelectedImage] = useState<InspectionImage | null>(null);
  const [zoomLevel, setZoomLevel] = useState<number>(1.0);

  const fetchImages = () => {
    setLoading(true);
    setError(null);
    const filterArg = viewTypeFilter === 'ALL' ? undefined : viewTypeFilter;
    api.listImages(filterArg)
      .then((data) => {
        let filtered = data;
        if (qualityFilter === 'ACCEPTABLE') {
          filtered = filtered.filter(img => img.is_acceptable);
        } else if (qualityFilter === 'WARNING') {
          filtered = filtered.filter(img => !img.is_acceptable);
        }
        setImages(filtered);
      })
      .catch((err: any) => setError(err.message || 'Failed to load evidence images'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchImages();
  }, [viewTypeFilter, qualityFilter]);

  return (
    <div className="page-body">
      {/* Header Banner */}
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
              background: 'rgba(59, 130, 246, 0.2)',
              padding: '6px 12px',
              borderRadius: 6,
              fontSize: 12,
              fontWeight: 700,
              color: '#60a5fa',
              letterSpacing: '0.04em'
            }}>
              STATUTORY EVIDENCE REPOSITORY
            </span>
            <span style={{ fontSize: 13, color: '#94a3b8' }}>
              SHA-256 Tamper-Evident Hashing
            </span>
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: '#f8fafc' }}>
            Packaging Photographic Evidence Gallery
          </h2>
          <p style={{ fontSize: 13, color: '#94a3b8', maxWidth: 650, marginTop: 4 }}>
            Original high-resolution packaging captures evaluated through computer vision quality diagnostics (Laplacian blur, brightness variance, skew orientation).
          </p>
        </div>

        <button 
          onClick={fetchImages}
          className="btn btn-secondary"
          style={{ background: '#334155', color: 'white', borderColor: '#475569', gap: 8 }}
        >
          <RefreshCw size={15} /> Refresh Evidence
        </button>
      </div>

      {/* Filter Bar */}
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
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Filter size={15} color="var(--text-muted)" />
            <span style={{ fontSize: 13, fontWeight: 600 }}>Panel View:</span>
            <select
              value={viewTypeFilter}
              onChange={(e) => setViewTypeFilter(e.target.value)}
              style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--border)', fontSize: 13 }}
            >
              <option value="ALL">All Panel Views</option>
              <option value="FRONT">Front Panel</option>
              <option value="BACK">Back Panel (Declarations)</option>
              <option value="SIDE">Side Panel</option>
              <option value="TOP">Top / Cap</option>
              <option value="BOTTOM">Bottom</option>
              <option value="MRP_PANEL">MRP Close-Up</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Quality Status:</span>
            <select
              value={qualityFilter}
              onChange={(e) => setQualityFilter(e.target.value)}
              style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--border)', fontSize: 13 }}
            >
              <option value="ALL">All Quality Conditions</option>
              <option value="ACCEPTABLE">Acceptable Evidence Only</option>
              <option value="WARNING">Has Quality Warning</option>
            </select>
          </div>
        </div>

        <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          Showing <b>{images.length}</b> verified photographic artifacts
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
          <RefreshCw size={28} className="spin" style={{ animation: 'spin 1s linear infinite', marginBottom: 12 }} />
          <p style={{ fontSize: 14 }}>Querying cryptographic evidence catalog...</p>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div style={{
          background: '#fef2f2',
          border: '1px solid #fca5a5',
          borderRadius: 'var(--radius-md)',
          padding: 20,
          color: '#b91c1c',
          marginBottom: 20,
          display: 'flex',
          alignItems: 'center',
          gap: 12
        }}>
          <AlertTriangle size={20} />
          <div>
            <b>Failed to retrieve evidence:</b> {error}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && images.length === 0 && (
        <div style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-lg)',
          border: '1px dashed var(--border)',
          padding: 60,
          textAlign: 'center',
          color: 'var(--text-muted)'
        }}>
          <Camera size={44} style={{ opacity: 0.3, marginBottom: 16 }} />
          <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-main)', marginBottom: 6 }}>
            No Packaging Evidence Found
          </h3>
          <p style={{ fontSize: 13, maxWidth: 450, margin: '0 auto 16px' }}>
            No photographic evidence matches the active filters. Upload package images during inspection case workflows.
          </p>
        </div>
      )}

      {/* Grid of Evidence Cards */}
      {!loading && !error && images.length > 0 && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
          gap: 20
        }}>
          {images.map((img) => {
            const q = img.quality_assessment;
            return (
              <div 
                key={img.id}
                style={{
                  background: 'var(--bg-card)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border)',
                  overflow: 'hidden',
                  boxShadow: 'var(--shadow-sm)',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  display: 'flex',
                  flexDirection: 'column'
                }}
              >
                {/* Image Canvas Preview */}
                <div 
                  onClick={() => setSelectedImage(img)}
                  style={{
                    height: 220,
                    background: '#020617',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                  title="Click to expand fullscreen"
                >
                  <img 
                    src={img.processed_path || img.storage_path} 
                    alt={img.view_type}
                    style={{ maxHeight: '100%', maxWidth: '100%', objectFit: 'contain' }}
                  />
                  <div style={{
                    position: 'absolute',
                    top: 10,
                    right: 10,
                    background: 'rgba(15, 23, 42, 0.75)',
                    padding: 6,
                    borderRadius: 6,
                    color: 'white'
                  }}>
                    <Maximize2 size={14} />
                  </div>
                </div>

                {/* Card Content */}
                <div style={{ padding: 16, display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                    <span className="badge badge-na" style={{ fontWeight: 700, letterSpacing: '0.04em' }}>
                      {img.view_type} VIEW
                    </span>
                    {img.is_acceptable ? (
                      <span className="badge badge-pass">
                        <CheckCircle2 size={12} /> Clear Evidence
                      </span>
                    ) : (
                      <span className="badge badge-uncertain">
                        <AlertTriangle size={12} /> Quality Warning
                      </span>
                    )}
                  </div>

                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>
                    Resolution: <b>{img.width} × {img.height} px</b> | Size: <b>{(img.file_size_bytes / 1024).toFixed(0)} KB</b>
                  </div>

                  <div style={{
                    background: '#f8fafc',
                    padding: 8,
                    borderRadius: 6,
                    border: '1px solid var(--border)',
                    marginBottom: 10,
                    fontSize: 11
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ color: 'var(--text-muted)' }}>Blur Sharpness:</span>
                      <b>{q?.blur_score?.toFixed(1) || 'N/A'}</b>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ color: 'var(--text-muted)' }}>Confidence Score:</span>
                      <b>{Math.round((q?.quality_score || 0) * 100)}%</b>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                      <span>SHA-256:</span>
                      <span title={img.sha256_hash}>{img.sha256_hash.slice(0, 14)}...</span>
                    </div>
                  </div>

                  {q?.warnings && q.warnings.length > 0 && (
                    <div style={{ background: '#fef2f2', border: '1px solid #fecaca', padding: '6px 10px', borderRadius: 6, marginBottom: 12 }}>
                      {q.warnings.map((w, i) => (
                        <div key={i} style={{ fontSize: 11, color: '#b91c1c' }}>• {w}</div>
                      ))}
                    </div>
                  )}

                  <div style={{ marginTop: 'auto', display: 'flex', gap: 8, paddingTop: 10 }}>
                    <button 
                      onClick={() => setSelectedImage(img)}
                      className="btn btn-secondary"
                      style={{ flex: 1, justifyContent: 'center', fontSize: 12, padding: '6px 0', gap: 6 }}
                    >
                      <Eye size={13} /> Inspect
                    </button>
                    {onOpenInspection && (
                      <button 
                        onClick={() => onOpenInspection(img.inspection_id)}
                        className="btn btn-primary"
                        style={{ flex: 1, justifyContent: 'center', fontSize: 12, padding: '6px 0', gap: 6 }}
                      >
                        <FileText size={13} /> View Case
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Fullscreen Lightbox Modal */}
      {selectedImage && (
        <div className="modal-overlay" onClick={() => { setSelectedImage(null); setZoomLevel(1.0); }}>
          <div 
            className="modal-content" 
            onClick={(e) => e.stopPropagation()} 
            style={{ maxWidth: 1000, width: '95%', height: '88vh', display: 'flex', flexDirection: 'column', padding: 0 }}
          >
            {/* Modal Header */}
            <div style={{
              background: '#0f172a',
              color: 'white',
              padding: '16px 24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderTopLeftRadius: 'var(--radius-lg)',
              borderTopRightRadius: 'var(--radius-lg)'
            }}>
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 700 }}>
                  High-Resolution Evidence Inspection ({selectedImage.view_type} VIEW)
                </h3>
                <p style={{ fontSize: 11, color: '#94a3b8', fontFamily: 'monospace' }}>
                  SHA-256: {selectedImage.sha256_hash}
                </p>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', background: '#1e293b', borderRadius: 6, padding: 2 }}>
                  <button 
                    onClick={() => setZoomLevel(prev => Math.max(0.6, prev - 0.2))}
                    style={{ background: 'transparent', border: 'none', color: 'white', padding: 6, cursor: 'pointer' }}
                    title="Zoom Out"
                  >
                    <ZoomOut size={16} />
                  </button>
                  <span style={{ fontSize: 12, padding: '0 8px', color: '#cbd5e1' }}>{Math.round(zoomLevel * 100)}%</span>
                  <button 
                    onClick={() => setZoomLevel(prev => Math.min(3.0, prev + 0.2))}
                    style={{ background: 'transparent', border: 'none', color: 'white', padding: 6, cursor: 'pointer' }}
                    title="Zoom In"
                  >
                    <ZoomIn size={16} />
                  </button>
                </div>

                <button 
                  onClick={() => { setSelectedImage(null); setZoomLevel(1.0); }}
                  style={{ background: '#334155', border: 'none', color: 'white', borderRadius: 6, padding: '6px 12px', cursor: 'pointer', fontSize: 13 }}
                >
                  Close
                </button>
              </div>
            </div>

            {/* Canvas Body */}
            <div style={{
              flexGrow: 1,
              background: '#020617',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              overflow: 'auto',
              padding: 24
            }}>
              <img 
                src={selectedImage.processed_path || selectedImage.storage_path} 
                alt="Package Evidence"
                style={{
                  maxWidth: '100%',
                  maxHeight: '70vh',
                  transform: `scale(${zoomLevel})`,
                  transformOrigin: 'center center',
                  transition: 'transform 0.15s ease-out'
                }}
              />
            </div>

            {/* Modal Footer Diagnostic Bar */}
            <div style={{
              padding: '12px 24px',
              borderTop: '1px solid var(--border)',
              background: 'white',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: 12,
              borderBottomLeftRadius: 'var(--radius-lg)',
              borderBottomRightRadius: 'var(--radius-lg)'
            }}>
              <div style={{ color: 'var(--text-muted)' }}>
                Dimensions: <b>{selectedImage.width} × {selectedImage.height} px</b> | MIME: <b>{selectedImage.mime_type}</b> | Uploaded: <b>{new Date(selectedImage.created_at).toLocaleString()}</b>
              </div>
              <div>
                {selectedImage.is_acceptable ? (
                  <span className="badge badge-pass"><CheckCircle2 size={12} /> Statutory Evidence Verified</span>
                ) : (
                  <span className="badge badge-uncertain"><AlertTriangle size={12} /> Advisory Quality Flag</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
