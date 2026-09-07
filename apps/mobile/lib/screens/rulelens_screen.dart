import 'package:flutter/material.dart';
import '../core/api_service.dart';
import '../core/constants.dart';
import '../core/storage_service.dart';
import '../models/inspection.dart';
import 'inspector_review_screen.dart';

class RuleLensScreen extends StatefulWidget {
  final String inspectionId;
  final String inspectionNumber;

  const RuleLensScreen({
    Key? key,
    required this.inspectionId,
    required this.inspectionNumber,
  }) : super(key: key);

  @override
  _RuleLensScreenState createState() => _RuleLensScreenState();
}

class _RuleLensScreenState extends State<RuleLensScreen> {
  bool _isLoading = true;
  String? _error;
  Map<String, dynamic>? _ruleLensData;
  MobileFinding? _selectedFinding;
  String? _primaryImageUrl;

  @override
  void initState() {
    super.initState();
    _loadRuleLens();
  }

  Future<void> _loadRuleLens() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final data = await ApiService().getRuleLens(widget.inspectionId);
      setState(() {
        _ruleLensData = data;
        final findingsRaw = data['findings'] as List? ?? [];
        final findings = findingsRaw.map((f) => MobileFinding.fromJson(f)).toList();
        if (findings.isNotEmpty) {
          _selectedFinding = findings.first;
        }

        final images = data['images'] as List? ?? [];
        if (images.isNotEmpty) {
          final rawPath = images[0]['processed_path'] ?? images[0]['storage_path'] ?? '';
          final baseUrl = StorageService().baseUrl;
          _primaryImageUrl = rawPath.startsWith('http') ? rawPath : '$baseUrl$rawPath';
        }
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString().replaceAll('Exception: ', '');
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final findingsRaw = _ruleLensData?['findings'] as List? ?? [];
    final findings = findingsRaw.map((f) => MobileFinding.fromJson(f)).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('RuleLens™ Traceability'),
        backgroundColor: AppColors.darkBg,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadRuleLens,
          )
        ],
      ),
      backgroundColor: AppColors.background,
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: AppColors.failRed)))
              : Column(
                  children: [
                    // Visual Canvas with Bounding Boxes
                    Container(
                      height: 260,
                      color: const Color(0xFF020617),
                      child: Stack(
                        alignment: Alignment.center,
                        children: [
                          if (_primaryImageUrl != null)
                            Image.network(
                              _primaryImageUrl!,
                              fit: BoxFit.contain,
                              width: double.infinity,
                              height: 260,
                              errorBuilder: (_, __, ___) => const Center(
                                child: Text('Packaging photograph offline', style: TextStyle(color: Colors.white54)),
                              ),
                            )
                          else
                            const Center(
                              child: Text('No evidence images attached', style: TextStyle(color: Colors.white54)),
                            ),

                          // Bounding Box Overlays
                          if (_selectedFinding != null)
                            ..._selectedFinding!.evidenceReferences.map((ev) {
                              final bbox = ev['bbox'] as List? ?? [0, 0, 0, 0];
                              final x1 = (bbox[0] as num).toDouble();
                              final y1 = (bbox[1] as num).toDouble();
                              final x2 = (bbox[2] as num).toDouble();
                              final y2 = (bbox[3] as num).toDouble();

                              Color boxColor = AppColors.passGreen;
                              if (_selectedFinding!.finalStatus == 'FAIL') boxColor = AppColors.failRed;
                              if (_selectedFinding!.finalStatus == 'UNCERTAIN') boxColor = AppColors.uncertainAmber;

                              return Positioned(
                                left: x1 * 340,
                                top: y1 * 260,
                                width: ((x2 - x1) * 340).clamp(20.0, 300.0),
                                height: ((y2 - y1) * 260).clamp(16.0, 200.0),
                                child: Container(
                                  decoration: BoxDecoration(
                                    border: Border.all(color: boxColor, width: 2),
                                    color: boxColor.withOpacity(0.2),
                                  ),
                                ),
                              );
                            }).toList(),
                        ],
                      ),
                    ),

                    // Requirement Selection Chips
                    Container(
                      color: Colors.white,
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      child: SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: Row(
                          children: findings.map((f) {
                            final isSelected = _selectedFinding?.id == f.id;
                            Color indicatorColor = AppColors.passGreen;
                            if (f.finalStatus == 'FAIL') indicatorColor = AppColors.failRed;
                            if (f.finalStatus == 'UNCERTAIN') indicatorColor = AppColors.uncertainAmber;

                            return Padding(
                              padding: const EdgeInsets.only(right: 6),
                              child: ChoiceChip(
                                label: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Container(
                                      width: 6,
                                      height: 6,
                                      margin: const EdgeInsets.only(right: 6),
                                      decoration: BoxDecoration(shape: BoxShape.circle, color: indicatorColor),
                                    ),
                                    Text(f.clauseReference, style: const TextStyle(fontSize: 11)),
                                  ],
                                ),
                                selected: isSelected,
                                selectedColor: AppColors.primaryLight,
                                labelStyle: TextStyle(
                                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                                  color: isSelected ? AppColors.primary : AppColors.textMain,
                                ),
                                onSelected: (_) => setState(() => _selectedFinding = f),
                              ),
                            );
                          }).toList(),
                        ),
                      ),
                    ),

                    // Statutory Explanation Card
                    Expanded(
                      child: SingleChildScrollView(
                        padding: const EdgeInsets.all(16),
                        child: _selectedFinding != null
                            ? Container(
                                padding: const EdgeInsets.all(16),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(color: AppColors.border),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                      children: [
                                        Text(
                                          _selectedFinding!.clauseReference,
                                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.primary),
                                        ),
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                          decoration: BoxDecoration(
                                            color: _selectedFinding!.finalStatus == 'PASS'
                                                ? AppColors.passBg
                                                : _selectedFinding!.finalStatus == 'FAIL'
                                                    ? AppColors.failBg
                                                    : AppColors.uncertainBg,
                                            borderRadius: BorderRadius.circular(4),
                                          ),
                                          child: Text(
                                            _selectedFinding!.finalStatus,
                                            style: TextStyle(
                                              fontSize: 11,
                                              fontWeight: FontWeight.bold,
                                              color: _selectedFinding!.finalStatus == 'PASS'
                                                  ? AppColors.passGreen
                                                  : _selectedFinding!.finalStatus == 'FAIL'
                                                      ? AppColors.failRed
                                                      : AppColors.uncertainAmber,
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 6),
                                    Text(
                                      _selectedFinding!.requirementTitle,
                                      style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                                    ),
                                    const SizedBox(height: 10),

                                    const Text('Statutory Clause Citation & Explanation:', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.textMuted)),
                                    const SizedBox(height: 4),
                                    Text(
                                      _selectedFinding!.explanation,
                                      style: const TextStyle(fontSize: 13, height: 1.4, color: AppColors.textMain),
                                    ),
                                    const SizedBox(height: 12),

                                    Container(
                                      padding: const EdgeInsets.all(10),
                                      decoration: BoxDecoration(
                                        color: const Color(0xFFF8FAFC),
                                        borderRadius: BorderRadius.circular(6),
                                        border: Border.all(color: AppColors.border),
                                      ),
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Text('Observed Text: ${_selectedFinding!.observedValue ?? "[Not Detected]"}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                                          const SizedBox(height: 2),
                                          Text('Statutory Condition: ${_selectedFinding!.expectedCondition}', style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
                                        ],
                                      ),
                                    ),

                                    // Why Is It Wrong? – Hazard / Violation Explanation Engine
                                    if (_selectedFinding!.hazardExplanation != null || _selectedFinding!.finalStatus != 'PASS') ...[
                                      const SizedBox(height: 14),
                                      _buildHazardExplanationCard(
                                        _selectedFinding!.hazardExplanation ??
                                            HazardExplanationModel(
                                              detectedIssue: _selectedFinding!.explanation,
                                              applicableRule: '${_selectedFinding!.clauseReference} of Legal Metrology (Packaged Commodities) Rules, 2011',
                                              reasonForNonCompliance: 'Declared value "${_selectedFinding!.observedValue ?? "MISSING"}" does not satisfy statutory requirement "${_selectedFinding!.expectedCondition}".',
                                              consumerHarm: 'Compromises buyer price & specification transparency, exposing consumers to unverified labeling.',
                                              regulatoryRisk: 'Contravention punishable under Section 36(1) of Legal Metrology Act, 2009.',
                                              evidenceFromPackage: _selectedFinding!.observedValue != null
                                                  ? 'Observed declaration: "${_selectedFinding!.observedValue}"'
                                                  : 'No compliant declaration text observed in camera visual capture.',
                                            ),
                                      ),
                                    ],
                                    const SizedBox(height: 16),

                                    // Adjudication Trigger
                                    SizedBox(
                                      width: double.infinity,
                                      child: ElevatedButton.icon(
                                        onPressed: () async {
                                          final updated = await Navigator.push(
                                            context,
                                            MaterialPageRoute(
                                              builder: (_) => InspectorReviewScreen(
                                                finding: _selectedFinding!,
                                                inspectionId: widget.inspectionId,
                                              ),
                                            ),
                                          );
                                          if (updated == true) _loadRuleLens();
                                        },
                                        icon: const Icon(Icons.gavel, size: 16),
                                        label: const Text('Inspector Adjudication & Override'),
                                        style: ElevatedButton.styleFrom(
                                          backgroundColor: AppColors.primary,
                                          foregroundColor: Colors.white,
                                          padding: const EdgeInsets.symmetric(vertical: 12),
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              )
                            : const SizedBox(),
                      ),
                    ),
                  ],
                ),
    );
  }

  Widget _buildHazardExplanationCard(HazardExplanationModel hazard) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: const BoxDecoration(
              color: Color(0xFF0F172A),
              borderRadius: BorderRadius.vertical(top: Radius.circular(9)),
            ),
            child: Row(
              children: [
                const Icon(Icons.shield_outlined, color: Color(0xFF38BDF8), size: 16),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text(
                    'WHY IS IT WRONG? – HAZARD ANALYSIS',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 0.4,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0284C7).withOpacity(0.25),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: const Color(0xFF38BDF8), width: 0.8),
                  ),
                  child: const Text('5-Step Engine', style: TextStyle(color: Color(0xFF38BDF8), fontSize: 9, fontWeight: FontWeight.bold)),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              children: [
                _buildHazardStep(
                  stepNum: '1',
                  title: 'Detected Issue',
                  icon: Icons.search_rounded,
                  color: const Color(0xFFEA580C),
                  content: hazard.detectedIssue,
                ),
                const SizedBox(height: 8),
                _buildHazardStep(
                  stepNum: '2',
                  title: 'Applicable Statutory Rule',
                  icon: Icons.gavel_rounded,
                  color: const Color(0xFF0284C7),
                  content: hazard.applicableRule,
                ),
                const SizedBox(height: 8),
                _buildHazardStep(
                  stepNum: '3',
                  title: 'Reason for Non-Compliance',
                  icon: Icons.cancel_outlined,
                  color: AppColors.failRed,
                  content: hazard.reasonForNonCompliance,
                ),
                const SizedBox(height: 8),
                _buildHazardRiskStep(
                  consumerHarm: hazard.consumerHarm,
                  regulatoryRisk: hazard.regulatoryRisk,
                ),
                const SizedBox(height: 8),
                _buildHazardStep(
                  stepNum: '5',
                  title: 'Evidence from Package',
                  icon: Icons.camera_alt_outlined,
                  color: const Color(0xFF475569),
                  content: hazard.evidenceFromPackage,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHazardStep({
    required String stepNum,
    required String title,
    required IconData icon,
    required Color color,
    required String content,
  }) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 20,
            height: 20,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: color.withOpacity(0.12),
              shape: BoxShape.circle,
              border: Border.all(color: color.withOpacity(0.4)),
            ),
            child: Text(
              stepNum,
              style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(icon, size: 12, color: color),
                    const SizedBox(width: 4),
                    Text(
                      title,
                      style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: color),
                    ),
                  ],
                ),
                const SizedBox(height: 3),
                Text(
                  content,
                  style: const TextStyle(fontSize: 12, height: 1.35, color: AppColors.textMain),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHazardRiskStep({
    required String consumerHarm,
    required String regulatoryRisk,
  }) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 20,
            height: 20,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: const Color(0xFFDC2626).withOpacity(0.12),
              shape: BoxShape.circle,
              border: Border.all(color: const Color(0xFFDC2626).withOpacity(0.4)),
            ),
            child: const Text(
              '4',
              style: TextStyle(color: Color(0xFFDC2626), fontSize: 10, fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.warning_amber_rounded, size: 12, color: Color(0xFFDC2626)),
                    SizedBox(width: 4),
                    Text(
                      'Potential Consumer & Regulatory Risk',
                      style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFFDC2626)),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFEF2F2),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: const Color(0xFFFECACA)),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.people_outline, size: 12, color: Color(0xFFDC2626)),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          'Consumer Harm: $consumerHarm',
                          style: const TextStyle(fontSize: 11, color: Color(0xFF991B1B), height: 1.3),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 4),
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFFBEB),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: const Color(0xFFFDE68A)),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.policy_outlined, size: 12, color: Color(0xFFD97706)),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          'Regulatory Risk: $regulatoryRisk',
                          style: const TextStyle(fontSize: 11, color: Color(0xFF92400E), height: 1.3),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
