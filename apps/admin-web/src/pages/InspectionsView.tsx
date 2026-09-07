import React, { useState, useEffect } from 'react';
import { 
  ClipboardCheck, 
  Search, 
  Plus, 
  Filter, 
  ArrowUpRight, 
  CheckCircle2, 
  XCircle, 
  HelpCircle,
  FileSpreadsheet,
  Video
} from 'lucide-react';
import { api } from '../api/client';
import { WebcamModal } from '../components/WebcamModal';
import { InspectionSummary } from '../types';

interface InspectionsViewProps {
  onSelectInspection: (id: string) => void;
  showNewModal: boolean;
  setShowNewModal: (show: boolean) => void;
}

export const InspectionsView: React.FC<InspectionsViewProps> = ({
  onSelectInspection,
  showNewModal,
  setShowNewModal
}) => {
  const [inspections, setInspections] = useState<InspectionSummary[]>([]);
  const [search, setSearch] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [complianceFilter, setComplianceFilter] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  // New Inspection Form State
  const [commodityName, setCommodityName] = useState<string>('');
  const [brandName, setBrandName] = useState<string>('');
  const [category, setCategory] = useState<string>('FOOD_BEVERAGE');
  const [packageType, setPackageType] = useState<string>('SINGLE_PRE_PACKAGED');
  const [isImported, setIsImported] = useState<boolean>(false);
  const [isEcommerce, setIsEcommerce] = useState<boolean>(false);
  const [ruleVersion, setRuleVersion] = useState<string>('LMPC-2026-RULES');
  const [notes, setNotes] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [quickInspection, setQuickInspection] = useState<InspectionSummary | null>(null);

  const handleQuickWebcamScan = async () => {
    try {
      const now = new Date();
      const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const created = await api.createInspection({
        commodity_name: `Quick-Scan Product (${timeStr})`,
        brand_name: 'Retail Package',
        rule_version: 'LMPC-2026-RULES',
        notes: 'Created via Direct Webcam Scanner',
        context: {
          commodity_category: 'FOOD',
          is_food: true,
          origin_country: 'India'
        }
      });
      setQuickInspection(created);
    } catch (err: any) {
      alert(`Could not initialize quick scan: ${err.message}`);
    }
  };

  const fetchInspections = () => {
    setLoading(true);
    api.listInspections({
      search: search || undefined,
      status: statusFilter || undefined,
      compliance_status: complianceFilter || undefined
    })
      .then(setInspections)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchInspections();
  }, [statusFilter, complianceFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchInspections();
  };

  const handleCreateInspection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commodityName) return;
    setIsSubmitting(true);
    try {
      const created = await api.createInspection({
        commodity_name: commodityName,
        brand_name: brandName,
        rule_version: ruleVersion,
        notes: notes,
        context: {
          commodity_category: category,
          package_type: packageType,
          is_food: category === 'FOOD_BEVERAGE',
          is_imported: isImported,
          is_ecommerce: isEcommerce,
          target_rule_version: ruleVersion
        }
      });
      setShowNewModal(false);
      setCommodityName('');
      setBrandName('');
      setNotes('');
      onSelectInspection(created.id);
    } catch (err: any) {
      alert(`Error creating inspection: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page-body">
      {/* Control Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 16,
        marginBottom: 24
      }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ position: 'relative', width: 300 }}>
            <Search size={16} color="#94a3b8" style={{ position: 'absolute', left: 12, top: 10 }} />
            <input 
              type="text"
              placeholder="Search by ID, commodity, brand..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px 8px 36px',
                borderRadius: 8,
                border: '1px solid var(--border)',
                fontSize: 13,
                outline: 'none',
                background: 'white'
              }}
            />
          </div>
          <button type="submit" className="btn btn-secondary" style={{ padding: '8px 14px' }}>
            Filter
          </button>
        </form>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <select 
            value={complianceFilter}
            onChange={(e) => setComplianceFilter(e.target.value)}
            style={{
              padding: '8px 12px',
              borderRadius: 8,
              border: '1px solid var(--border)',
              fontSize: 13,
              background: 'white',
              outline: 'none'
            }}
          >
            <option value="">All Verdicts</option>
            <option value="COMPLIANT">Compliant</option>
            <option value="NON_COMPLIANT">Non-Compliant</option>
            <option value="REQUIRES_REVIEW">Requires Review</option>
          </select>

          <button 
            onClick={handleQuickWebcamScan}
            className="btn btn-primary"
            style={{ gap: 6, background: '#10b981', borderColor: '#059669' }}
          >
            <Video size={16} />
            Direct Webcam Scan
          </button>

          <button 
            onClick={() => setShowNewModal(true)}
            className="btn btn-secondary"
            style={{ gap: 6 }}
          >
            <Plus size={16} />
            New Inspection
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Inspection Number</th>
              <th>Commodity / Brand</th>
              <th>Rule Baseline</th>
              <th>Images</th>
              <th>Inspection Status</th>
              <th>Compliance Verdict</th>
              <th>Date</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={8} style={{ textAlign: 'center', padding: 32 }}>Loading inspections...</td></tr>
            ) : inspections.length > 0 ? (
              inspections.map((insp) => (
                <tr key={insp.id}>
                  <td style={{ fontWeight: 600, color: '#2563eb' }}>{insp.inspection_number}</td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{insp.commodity_name}</div>
                    {insp.brand_name && <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{insp.brand_name}</div>}
                  </td>
                  <td>
                    <span style={{ fontSize: 12, fontWeight: 500, color: '#475569' }}>{insp.rule_version}</span>
                  </td>
                  <td>
                    <span className="badge badge-na">{insp.total_images} photos</span>
                  </td>
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
                      Open Case <ArrowUpRight size={14} />
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: 32, color: 'var(--text-muted)' }}>
                  No inspections match your filter criteria.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* New Inspection Modal */}
      {showNewModal && (
        <div className="modal-overlay" onClick={() => setShowNewModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 650, padding: 28 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <ClipboardCheck size={22} color="#2563eb" />
                <h3 style={{ fontSize: 18, fontWeight: 700 }}>Initiate Legal Metrology Inspection</h3>
              </div>
              <button 
                onClick={() => setShowNewModal(false)}
                style={{ background: 'transparent', border: 'none', fontSize: 18, cursor: 'pointer', color: 'var(--text-muted)' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateInspection} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 6 }}>
                  Commodity Name *
                </label>
                <input 
                  type="text"
                  required
                  placeholder="e.g. Pure Ghee 1L Tin / Almonds 500g"
                  value={commodityName}
                  onChange={(e) => setCommodityName(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13 }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 6 }}>
                    Brand / Trademark
                  </label>
                  <input 
                    type="text"
                    placeholder="e.g. ApexFoods"
                    value={brandName}
                    onChange={(e) => setBrandName(e.target.value)}
                    style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13 }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 6 }}>
                    Commodity Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13, background: 'white' }}
                  >
                    <option value="FOOD_BEVERAGE">Food & Beverage (FSSAI Aligned)</option>
                    <option value="COSMETICS_PERSONAL_CARE">Cosmetics & Personal Care</option>
                    <option value="ELECTRONICS_APPLIANCES">Electronics & Electricals</option>
                    <option value="HOUSEHOLD_CLEANING">Household & Cleaning</option>
                    <option value="GENERAL_COMMODITY">General Packaged Commodity</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 6 }}>
                    Regulatory Rule Baseline
                  </label>
                  <select
                    value={ruleVersion}
                    onChange={(e) => setRuleVersion(e.target.value)}
                    style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13, background: 'white' }}
                  >
                    <option value="LMPC-2026-RULES">LMPC 2026 Modernized Rules</option>
                    <option value="LMPC-2021-AMENDMENT">LMPC 2021 USP Amendment</option>
                    <option value="LMPC-2017-AMENDMENT">LMPC 2017 E-Commerce Amendment</option>
                    <option value="LMPC-2011-BASE">LMPC 2011 Base Rules</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 6 }}>
                    Package Classification
                  </label>
                  <select
                    value={packageType}
                    onChange={(e) => setPackageType(e.target.value)}
                    style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13, background: 'white' }}
                  >
                    <option value="SINGLE_PRE_PACKAGED">Single Pre-Packaged Item</option>
                    <option value="MULTI_PIECE">Multi-Piece Package</option>
                    <option value="COMBINATION">Combination Package</option>
                    <option value="WHOLESALE">Wholesale Package</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 24, padding: '10px 0' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer' }}>
                  <input 
                    type="checkbox" 
                    checked={isImported} 
                    onChange={(e) => setIsImported(e.target.checked)} 
                    style={{ width: 16, height: 16 }}
                  />
                  <span>Imported Commodity (Enforces Origin & Importer rules)</span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer' }}>
                  <input 
                    type="checkbox" 
                    checked={isEcommerce} 
                    onChange={(e) => setIsEcommerce(e.target.checked)} 
                    style={{ width: 16, height: 16 }}
                  />
                  <span>E-Commerce Listing (Rule 6(10) audit)</span>
                </label>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 6 }}>
                  Inspection Location / Memo Notes
                </label>
                <textarea 
                  rows={2}
                  placeholder="e.g. Seized from retail supermarket depot during scheduled survey..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13, fontFamily: 'inherit' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 10 }}>
                <button 
                  type="button" 
                  onClick={() => setShowNewModal(false)} 
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  disabled={isSubmitting}
                  className="btn btn-primary"
                >
                  {isSubmitting ? 'Creating Case...' : 'Create Case & Upload Evidence'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Direct Webcam Scanner Modal */}
      {quickInspection && (
        <WebcamModal
          isOpen={!!quickInspection}
          inspectionId={quickInspection.id}
          inspectionNumber={quickInspection.inspection_number}
          onClose={() => {
            const id = quickInspection.id;
            setQuickInspection(null);
            fetchInspections();
            onSelectInspection(id);
          }}
          onUploadSuccess={() => {
            fetchInspections();
          }}
        />
      )}
    </div>
  );
};
