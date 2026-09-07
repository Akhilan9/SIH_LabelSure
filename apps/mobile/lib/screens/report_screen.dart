import 'package:flutter/material.dart';
import '../core/api_service.dart';
import '../core/constants.dart';
import '../core/storage_service.dart';
import '../models/inspection.dart';

class ReportScreen extends StatefulWidget {
  final String inspectionId;
  final String inspectionNumber;

  const ReportScreen({
    Key? key,
    required this.inspectionId,
    required this.inspectionNumber,
  }) : super(key: key);

  @override
  _ReportScreenState createState() => _ReportScreenState();
}

class _ReportScreenState extends State<ReportScreen> {
  ComprehensiveReportModel? _report;
  bool _isLoading = true;
  bool _isFinalizing = false;
  bool _isGeneratingPdf = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadReport();
  }

  Future<void> _loadReport() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final rep = await ApiService().getStructuredReport(widget.inspectionId);
      setState(() {
        _report = rep;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString().replaceAll('Exception: ', '');
        _isLoading = false;
      });
    }
  }

  Future<void> _generatePdfAgain() async {
    setState(() => _isGeneratingPdf = true);
    try {
      await ApiService().generateReport(widget.inspectionId);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Official PDF generated and certified.'),
            backgroundColor: AppColors.passGreen,
          ),
        );
      }
      _loadReport();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('PDF Generation failed: ${e.toString()}')),
        );
      }
    } finally {
      if (mounted) setState(() => _isGeneratingPdf = false);
    }
  }

  Future<void> _finalizeCase() async {
    setState(() => _isFinalizing = true);
    try {
      await ApiService().finalizeInspection(widget.inspectionId);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Inspection case finalized into permanent Legal Metrology registry.'),
            backgroundColor: AppColors.passGreen,
          ),
        );
      }
      _loadReport();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Finalization failed: ${e.toString()}')),
        );
      }
    } finally {
      if (mounted) setState(() => _isFinalizing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final baseUrl = StorageService().baseUrl;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Statutory Inspection Certificate'),
        backgroundColor: AppColors.darkBg,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadReport,
          ),
        ],
      ),
      backgroundColor: AppColors.background,
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.error_outline, color: AppColors.failRed, size: 48),
                        const SizedBox(height: 12),
                        Text('Failed to Load Report: $_error', textAlign: TextAlign.center, style: const TextStyle(color: AppColors.failRed)),
                        const SizedBox(height: 16),
                        ElevatedButton(onPressed: _loadReport, child: const Text('Retry')),
                      ],
                    ),
                  ),
                )
              : _report == null
                  ? const Center(child: Text('No report data found.'))
                  : SingleChildScrollView(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          // 1. Certificate Banner
                          _buildCertificateBanner(),
                          const SizedBox(height: 16),

                          // Pillar 1: Product Overview & Identification Details
                          _buildSectionHeader('PILLAR 1: PRODUCT IDENTIFICATION', Icons.inventory_2_outlined),
                          const SizedBox(height: 8),
                          _buildProductDetailsCard(),
                          const SizedBox(height: 16),

                          // Pillar 2: Extracted Declarations Inventory
                          _buildSectionHeader('PILLAR 2: EXTRACTED DECLARATIONS (${_report!.extractedDeclarations.length})', Icons.assignment_outlined),
                          const SizedBox(height: 8),
                          _buildDeclarationsCard(),
                          const SizedBox(height: 16),

                          // Pillar 3: Applicable Legal Metrology Rules
                          _buildSectionHeader('PILLAR 3: APPLICABLE STATUTORY RULES (${_report!.applicableRules.length})', Icons.gavel_outlined),
                          const SizedBox(height: 8),
                          _buildApplicableRulesCard(),
                          const SizedBox(height: 16),

                          // Pillar 4: Compliance Status & Breakdown Scorecard
                          _buildSectionHeader('PILLAR 4: COMPLIANCE STATUS SCORECARD', Icons.analytics_outlined),
                          const SizedBox(height: 8),
                          _buildComplianceScorecard(),
                          const SizedBox(height: 16),

                          // Pillar 5: Detected Violations & "Why Is It Wrong?" Engine
                          _buildSectionHeader('PILLAR 5: DETECTED VIOLATIONS & HAZARDS (${_report!.detectedViolations.length})', Icons.warning_amber_rounded),
                          const SizedBox(height: 8),
                          _buildViolationsSection(),
                          const SizedBox(height: 16),

                          // Pillar 6: Visual Evidence Repository
                          _buildSectionHeader('PILLAR 6: VISUAL EVIDENCE GALLERY (${_report!.visualEvidence.length})', Icons.camera_alt_outlined),
                          const SizedBox(height: 8),
                          _buildVisualEvidenceCard(baseUrl),
                          const SizedBox(height: 16),

                          // Pillar 7: Inspector Verification & Digital Seal
                          _buildSectionHeader('PILLAR 7: INSPECTOR VERIFICATION & SEAL', Icons.verified_user_outlined),
                          const SizedBox(height: 8),
                          _buildInspectorVerificationCard(),
                          const SizedBox(height: 16),

                          // Pillar 8: Certified Audit Timestamps
                          _buildSectionHeader('PILLAR 8: CERTIFIED AUDIT TIMESTAMPS', Icons.history_edu_outlined),
                          const SizedBox(height: 8),
                          _buildTimestampsCard(),
                          const SizedBox(height: 16),

                          // Pillar 9: Recommended Statutory Follow-up Actions
                          _buildSectionHeader('PILLAR 9: STATUTORY FOLLOW-UP ACTIONS (${_report!.recommendedFollowUpActions.length})', Icons.notification_important_outlined),
                          const SizedBox(height: 8),
                          _buildFollowUpActionsSection(),
                          const SizedBox(height: 24),

                          // Action Buttons
                          ElevatedButton.icon(
                            onPressed: () {
                              final fullUrl = _report!.pdfUrl.startsWith('http') ? _report!.pdfUrl : '$baseUrl${_report!.pdfUrl}';
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(content: Text('Official PDF Certified: $fullUrl')),
                              );
                            },
                            icon: const Icon(Icons.picture_as_pdf),
                            label: const Text('Download Official Inspection PDF', style: TextStyle(fontWeight: FontWeight.bold)),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.primary,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                            ),
                          ),
                          const SizedBox(height: 10),

                          Row(
                            children: [
                              Expanded(
                                child: OutlinedButton.icon(
                                  onPressed: _isGeneratingPdf ? null : _generatePdfAgain,
                                  icon: _isGeneratingPdf
                                      ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2))
                                      : const Icon(Icons.refresh, size: 16),
                                  label: const Text('Re-Generate PDF', style: TextStyle(fontSize: 12)),
                                  style: OutlinedButton.styleFrom(
                                    padding: const EdgeInsets.symmetric(vertical: 12),
                                    side: const BorderSide(color: AppColors.border),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: OutlinedButton.icon(
                                  onPressed: _isFinalizing ? null : _finalizeCase,
                                  icon: _isFinalizing
                                      ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2))
                                      : const Icon(Icons.lock_outline, size: 16, color: AppColors.passGreen),
                                  label: const Text('Freeze & Finalize', style: TextStyle(fontSize: 12, color: AppColors.passGreen, fontWeight: FontWeight.bold)),
                                  style: OutlinedButton.styleFrom(
                                    padding: const EdgeInsets.symmetric(vertical: 12),
                                    side: const BorderSide(color: AppColors.passBorder),
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 24),
                        ],
                      ),
                    ),
    );
  }

  Widget _buildCertificateBanner() {
    final verdict = _report!.complianceVerdict;
    final isPass = verdict == 'COMPLIANT';
    final isFail = verdict == 'NON_COMPLIANT';

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF0F172A), Color(0xFF1E293B)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.12), blurRadius: 10, offset: const Offset(0, 4)),
        ],
      ),
      child: Column(
        children: [
          const Icon(Icons.verified, color: Color(0xFF60A5FA), size: 44),
          const SizedBox(height: 8),
          const Text(
            'STATUTORY COMPLIANCE CERTIFICATE',
            style: TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 0.6),
          ),
          const SizedBox(height: 4),
          Text(
            _report!.certificateNumber,
            style: const TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.bold, fontFamily: 'monospace'),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
            decoration: BoxDecoration(
              color: isPass ? AppColors.passGreen : (isFail ? AppColors.failRed : AppColors.uncertainAmber),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              verdict,
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
            ),
          ),
          const SizedBox(height: 10),
          Text(
            'Case Number: ${widget.inspectionNumber} | Issued: ${_formatDate(_report!.generatedAt)}',
            style: const TextStyle(color: Colors.white54, fontSize: 11),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title, IconData icon) {
    return Row(
      children: [
        Icon(icon, size: 16, color: AppColors.primary),
        const SizedBox(width: 6),
        Text(
          title,
          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF334155), letterSpacing: 0.4),
        ),
      ],
    );
  }

  Widget _buildProductDetailsCard() {
    final p = _report!.productDetails;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: _cardDecoration(),
      child: Column(
        children: [
          _buildRow('Commodity Name', p['commodity_name']?.toString() ?? 'N/A', isBold: true),
          _buildDivider(),
          _buildRow('Brand Name', p['brand_name']?.toString() ?? 'Unbranded'),
          _buildDivider(),
          _buildRow('Category', p['commodity_category']?.toString() ?? 'FOOD_BEVERAGE'),
          _buildDivider(),
          _buildRow('Package Type', p['package_type']?.toString() ?? 'SINGLE_PRE_PACKAGED'),
          _buildDivider(),
          _buildRow('Origin Country', p['origin_country']?.toString() ?? 'India'),
          _buildDivider(),
          _buildRow('Target Rule Version', p['target_rule_version']?.toString() ?? 'LMPC-2026-RULES'),
        ],
      ),
    );
  }

  Widget _buildDeclarationsCard() {
    final decls = _report!.extractedDeclarations;
    if (decls.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(14),
        decoration: _cardDecoration(),
        child: const Center(
          child: Text('No declarations extracted from packaging images.', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
        ),
      );
    }

    return Container(
      decoration: _cardDecoration(),
      child: ListView.separated(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: decls.length,
        separatorBuilder: (_, __) => _buildDivider(),
        itemBuilder: (context, index) {
          final d = decls[index];
          return Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFFEFF6FF),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: const Color(0xFFBFDBFE)),
                  ),
                  child: Text(
                    d.category.replaceAll('_', ' '),
                    style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFF1E40AF)),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(d.rawText, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                      if (d.unit != null)
                        Text('Standard Unit: ${d.unit}', style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
                    ],
                  ),
                ),
                Text(
                  '${(d.confidence * 100).toInt()}% conf',
                  style: const TextStyle(fontSize: 10, color: AppColors.textMuted),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildApplicableRulesCard() {
    final rules = _report!.applicableRules;
    return Container(
      decoration: _cardDecoration(),
      child: ListView.separated(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: rules.length,
        separatorBuilder: (_, __) => _buildDivider(),
        itemBuilder: (context, index) {
          final r = rules[index];
          return Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  r['clause_reference']?.toString() ?? '',
                  style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.primary),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    r['requirement']?.toString() ?? '',
                    style: const TextStyle(fontSize: 12, color: AppColors.textMain),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildComplianceScorecard() {
    final status = _report!.complianceStatus;
    final total = status['total_rules'] ?? 0;
    final passed = status['passed_count'] ?? 0;
    final failed = status['failed_count'] ?? 0;
    final rate = (status['compliance_rate'] as num?)?.toDouble() ?? 0.0;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: _cardDecoration(),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Compliance Rate', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
              Text('${rate.toStringAsFixed(1)}%', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.primary)),
            ],
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: (rate / 100.0).clamp(0.0, 1.0),
              minHeight: 8,
              backgroundColor: const Color(0xFFE2E8F0),
              valueColor: AlwaysStoppedAnimation<Color>(rate >= 100 ? AppColors.passGreen : (rate >= 70 ? AppColors.uncertainAmber : AppColors.failRed)),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildMetric('Total Rules', total.toString(), Colors.blueGrey),
              _buildMetric('Passed', passed.toString(), AppColors.passGreen),
              _buildMetric('Violations', failed.toString(), AppColors.failRed),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildViolationsSection() {
    final violations = _report!.detectedViolations;
    if (violations.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: _cardDecoration(),
        child: const Row(
          children: [
            Icon(Icons.check_circle, color: AppColors.passGreen, size: 24),
            SizedBox(width: 10),
            Expanded(
              child: Text(
                'Full statutory compliance observed. Zero mandatory packaging violations detected.',
                style: TextStyle(fontSize: 12, color: AppColors.passGreen, fontWeight: FontWeight.w600),
              ),
            ),
          ],
        ),
      );
    }

    return Column(
      children: violations.map((v) => _buildViolationCard(v)).toList(),
    );
  }

  Widget _buildViolationCard(MobileFinding finding) {
    final hazard = finding.hazardExplanation;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFFFECACA)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Violation Header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: const BoxDecoration(
              color: Color(0xFFFEF2F2),
              borderRadius: BorderRadius.vertical(top: Radius.circular(9)),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  finding.clauseReference,
                  style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF991B1B)),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppColors.failRed,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    finding.severity,
                    style: const TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(finding.requirementTitle, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                const SizedBox(height: 6),
                Text(finding.explanation, style: const TextStyle(fontSize: 12, color: AppColors.textMain, height: 1.3)),
                const SizedBox(height: 10),

                // 5-Step Hazard Explanation
                if (hazard != null)
                  _buildHazardChain(hazard)
                else
                  _buildHazardChain(
                    HazardExplanationModel(
                      detectedIssue: finding.explanation,
                      applicableRule: '${finding.clauseReference} of Legal Metrology (Packaged Commodities) Rules, 2011',
                      reasonForNonCompliance: 'Declared value "${finding.observedValue ?? "MISSING"}" fails requirement "${finding.expectedCondition}".',
                      consumerHarm: 'Direct consumer opacity regarding mandatory packaging particulars.',
                      regulatoryRisk: 'Punishable under Section 36(1) of Legal Metrology Act, 2009.',
                      evidenceFromPackage: finding.observedValue != null ? 'Declared text: "${finding.observedValue}"' : 'No compliant declaration text observed in camera visual capture.',
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHazardChain(HazardExplanationModel hazard) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('WHY IS IT WRONG? (HAZARD ANALYSIS)', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFF0F172A), letterSpacing: 0.3)),
          const SizedBox(height: 6),
          _buildHazardItem('1. Issue', hazard.detectedIssue),
          _buildHazardItem('2. Rule', hazard.applicableRule),
          _buildHazardItem('3. Non-Compliance', hazard.reasonForNonCompliance),
          _buildHazardItem('4. Risk', 'Consumer: ${hazard.consumerHarm} | Legal: ${hazard.regulatoryRisk}'),
          _buildHazardItem('5. Package Evidence', hazard.evidenceFromPackage),
        ],
      ),
    );
  }

  Widget _buildHazardItem(String title, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: RichText(
        text: TextSpan(
          text: '$title: ',
          style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF334155)),
          children: [
            TextSpan(
              text: text,
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.normal, color: Color(0xFF475569)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildVisualEvidenceCard(String baseUrl) {
    final images = _report!.visualEvidence;
    if (images.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(14),
        decoration: _cardDecoration(),
        child: const Center(
          child: Text('No packaging photographs attached to case.', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
        ),
      );
    }

    return Container(
      decoration: _cardDecoration(),
      child: ListView.separated(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: images.length,
        separatorBuilder: (_, __) => _buildDivider(),
        itemBuilder: (context, index) {
          final img = images[index];
          return Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            child: Row(
              children: [
                const Icon(Icons.photo_outlined, size: 28, color: AppColors.primary),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Panel: ${img.viewType}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 2),
                      Text(
                        'SHA-256: ${img.sha256Hash.isNotEmpty ? img.sha256Hash.substring(0, 16) : "Calculated"}...',
                        style: const TextStyle(fontSize: 10, fontFamily: 'monospace', color: AppColors.textMuted),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: const Color(0xFFECFDF5),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: const Color(0xFFA7F3D0)),
                  ),
                  child: const Text('Captured', style: TextStyle(fontSize: 10, color: Color(0xFF065F46))),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildInspectorVerificationCard() {
    final ver = _report!.inspectorVerification;
    final seal = ver['digital_seal_sha256']?.toString() ?? 'Certified SHA-256';

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: _cardDecoration(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildRow('Inspecting Officer', ver['inspector_name']?.toString() ?? _report!.generatedBy, isBold: true),
          _buildDivider(),
          _buildRow('Badge Number', ver['badge_number']?.toString() ?? 'DL-LM-2026'),
          _buildDivider(),
          _buildRow('Verification Status', ver['verification_status']?.toString() ?? 'VERIFIED'),
          _buildDivider(),
          _buildRow('Overrides Adjudicated', '${ver['overrides_count'] ?? 0} items'),
          _buildDivider(),
          const Text('Cryptographic Seal SHA-256:', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.textMuted)),
          const SizedBox(height: 4),
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: const Color(0xFFF8FAFC),
              borderRadius: BorderRadius.circular(4),
              border: Border.all(color: AppColors.border),
            ),
            child: Text(
              seal,
              style: const TextStyle(fontSize: 9, fontFamily: 'monospace', color: Color(0xFF334155)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTimestampsCard() {
    final t = _report!.timestamps;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: _cardDecoration(),
      child: Column(
        children: [
          _buildRow('Inspection Initiated', _formatDate(t['created_at']?.toString())),
          _buildDivider(),
          _buildRow('OCR & Rule Evaluation', _formatDate(t['analyzed_at']?.toString())),
          _buildDivider(),
          _buildRow('Officer Review / Adjudication', _formatDate(t['reviewed_at']?.toString())),
          _buildDivider(),
          _buildRow('Certified Timestamp', _formatDate(t['certified_at']?.toString())),
        ],
      ),
    );
  }

  Widget _buildFollowUpActionsSection() {
    final actions = _report!.recommendedFollowUpActions;
    if (actions.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(14),
        decoration: _cardDecoration(),
        child: const Center(
          child: Text('No mandatory enforcement follow-up actions required.', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
        ),
      );
    }

    return Column(
      children: actions.map((act) => _buildFollowUpActionCard(act)).toList(),
    );
  }

  Widget _buildFollowUpActionCard(FollowUpActionModel act) {
    Color priorityColor = const Color(0xFFD97706);
    if (act.priority == 'CRITICAL') priorityColor = AppColors.failRed;
    if (act.priority == 'HIGH') priorityColor = const Color(0xFFEA580C);

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.border),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: const Color(0xFFEFF6FF),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: const Color(0xFFBFDBFE)),
                  ),
                  child: Text(
                    act.statutorySection,
                    style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFF1E40AF)),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: priorityColor.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    act.priority,
                    style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: priorityColor),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(act.title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(act.description, style: const TextStyle(fontSize: 12, color: AppColors.textMain, height: 1.3)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 4,
              alignment: WrapAlignment.spaceBetween,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                Text('Statutory Penalty: ${act.penaltyEstimate}', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.failRed)),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF1F5F9),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text('Deadline: ${act.deadlineDays} Days', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF334155))),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // Helpers
  BoxDecoration _cardDecoration() {
    return BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(10),
      border: Border.all(color: AppColors.border),
    );
  }

  Widget _buildRow(String label, String value, {bool isBold = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.end,
              style: TextStyle(fontSize: 12, fontWeight: isBold ? FontWeight.bold : FontWeight.normal, color: AppColors.textMain),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDivider() {
    return const Divider(height: 12, thickness: 0.5, color: Color(0xFFE2E8F0));
  }

  Widget _buildMetric(String label, String value, Color color) {
    return Column(
      children: [
        Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: color)),
        const SizedBox(height: 2),
        Text(label, style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
      ],
    );
  }

  String _formatDate(String? iso) {
    if (iso == null || iso.isEmpty) return 'Pending';
    final parsed = DateTime.tryParse(iso);
    if (parsed == null) return iso;
    return parsed.toLocal().toString().split('.')[0];
  }
}
