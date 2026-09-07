import 'package:flutter/material.dart';
import '../core/api_service.dart';
import '../core/constants.dart';
import '../models/inspection.dart';

class InternationalComparisonScreen extends StatefulWidget {
  final String inspectionId;
  final String inspectionNumber;
  final String? initialJurisdiction;

  const InternationalComparisonScreen({
    Key? key,
    required this.inspectionId,
    required this.inspectionNumber,
    this.initialJurisdiction,
  }) : super(key: key);

  @override
  _InternationalComparisonScreenState createState() =>
      _InternationalComparisonScreenState();
}

class _InternationalComparisonScreenState
    extends State<InternationalComparisonScreen> {
  List<JurisdictionModel> _jurisdictions = [];
  String _selectedJurisdictionId = 'USA';
  InternationalComparisonModel? _comparison;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _selectedJurisdictionId = widget.initialJurisdiction ?? 'USA';
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final list = await ApiService().getInternationalJurisdictions();
      if (mounted) {
        setState(() {
          _jurisdictions = list;
          if (!_jurisdictions.any((j) => j.jurisdictionId == _selectedJurisdictionId) &&
              _jurisdictions.isNotEmpty) {
            _selectedJurisdictionId = _jurisdictions.first.jurisdictionId;
          }
        });
      }

      await _fetchComparison();
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString().replaceAll('Exception: ', '');
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _fetchComparison() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final comp = await ApiService().compareInspectionInternational(
        widget.inspectionId,
        jurisdiction: _selectedJurisdictionId,
      );
      if (mounted) {
        setState(() {
          _comparison = comp;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString().replaceAll('Exception: ', '');
          _isLoading = false;
        });
      }
    }
  }

  void _showScanIngredientsModal() {
    final textController = TextEditingController();
    List<BannedSubstanceModel> scanResults = [];
    bool isScanning = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setModalState) => Container(
          padding: EdgeInsets.only(
            left: 20,
            right: 20,
            top: 20,
            bottom: MediaQuery.of(context).viewInsets.bottom + 20,
          ),
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          ),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.biotech, color: AppColors.primary),
                        SizedBox(width: 8),
                        Text(
                          'Scan Ingredients for Global Bans',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () => Navigator.pop(ctx),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                const Text(
                  'Paste product ingredients or food additives to verify if any are banned in the EU, USA, UK, Canada, Australia, etc.',
                  style: TextStyle(fontSize: 12, color: Colors.black54),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: textController,
                  maxLines: 4,
                  decoration: InputDecoration(
                    hintText: 'e.g. Flour, Titanium Dioxide (E171), Brominated Vegetable Oil, sugar, artificial color...',
                    hintStyle: const TextStyle(fontSize: 13, color: Colors.black38),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    filled: true,
                    fillColor: Colors.grey.shade50,
                  ),
                ),
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: isScanning
                        ? null
                        : () async {
                            final input = textController.text.trim();
                            if (input.isEmpty) return;
                            setModalState(() => isScanning = true);
                            final results = await ApiService().scanTextForBannedSubstances(
                              input,
                              jurisdictionId: _selectedJurisdictionId,
                            );
                            setModalState(() {
                              scanResults = results;
                              isScanning = false;
                            });
                          },
                    icon: isScanning
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                          )
                        : const Icon(Icons.search),
                    label: Text(isScanning ? 'Analyzing Toxicology Database...' : 'Run Global Bans Scan'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                  ),
                ),
                if (scanResults.isNotEmpty) ...[
                  const SizedBox(height: 16),
                  Text(
                    'Detected Restricted/Banned Substances (${scanResults.length}):',
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.red),
                  ),
                  const SizedBox(height: 8),
                  ...scanResults.map((sub) => _buildBannedSubstanceCard(sub)),
                ] else if (!isScanning && textController.text.isNotEmpty) ...[
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.green.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.green.shade300),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.check_circle, color: Colors.green),
                        SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'No globally prohibited substances detected in this text.',
                            style: TextStyle(color: Colors.green, fontSize: 13, fontWeight: FontWeight.bold),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildVerdictBanner() {
    if (_comparison == null) return const SizedBox.shrink();
    final c = _comparison!;

    Color cardBg;
    Color accentColor;
    IconData iconData;
    String verdictLabel;

    switch (c.overallVerdict) {
      case 'APPROVED_FOR_EXPORT':
        cardBg = const Color(0xFFE8F5E9);
        accentColor = const Color(0xFF2E7D32);
        iconData = Icons.verified;
        verdictLabel = 'READY FOR EXPORT';
        break;
      case 'ACTION_REQUIRED':
        cardBg = const Color(0xFFFFF8E1);
        accentColor = const Color(0xFFF57F17);
        iconData = Icons.warning_amber_rounded;
        verdictLabel = 'LABEL REVISION REQUIRED';
        break;
      case 'EXPORT_BLOCKED':
      default:
        cardBg = const Color(0xFFFFEBEE);
        accentColor = const Color(0xFFC62828);
        iconData = Icons.block;
        verdictLabel = 'EXPORT BLOCKED';
        break;
    }

    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: accentColor.withOpacity(0.4), width: 1.5),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: accentColor.withOpacity(0.15),
                  shape: BoxShape.circle,
                ),
                child: Icon(iconData, color: accentColor, size: 28),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          verdictLabel,
                          style: TextStyle(
                            color: accentColor,
                            fontWeight: FontWeight.w900,
                            fontSize: 15,
                            letterSpacing: 0.5,
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                          decoration: BoxDecoration(
                            color: accentColor,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            '${c.exportReadinessScore}% Readiness',
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      c.verdictSummary,
                      style: const TextStyle(fontSize: 13, color: Colors.black87, fontWeight: FontWeight.w500),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          const Divider(height: 1),
          const SizedBox(height: 10),
          Text(
            c.executiveSummary,
            style: const TextStyle(fontSize: 12.5, color: Colors.black87, height: 1.4),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              _buildStatChip(
                'Critical Blockers: ${c.blockersCount}',
                c.blockersCount > 0 ? Colors.red.shade700 : Colors.green.shade700,
                c.blockersCount > 0 ? Colors.red.shade50 : Colors.green.shade50,
              ),
              const SizedBox(width: 8),
              _buildStatChip(
                'Modifications: ${c.warningsCount}',
                Colors.orange.shade800,
                Colors.orange.shade50,
              ),
              const SizedBox(width: 8),
              _buildStatChip(
                'Rules: ${c.totalRequirements}',
                Colors.blueGrey.shade800,
                Colors.blueGrey.shade50,
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatChip(String label, Color textColor, Color bgColor) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: textColor.withOpacity(0.3)),
      ),
      child: Text(
        label,
        style: TextStyle(color: textColor, fontSize: 11, fontWeight: FontWeight.bold),
      ),
    );
  }

  Widget _buildBannedSubstancesSection() {
    if (_comparison == null || _comparison!.bannedSubstances.isEmpty) {
      return const SizedBox.shrink();
    }

    final bans = _comparison!.bannedSubstances;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF0F0),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.red.shade700, width: 2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.dangerous, color: Colors.red, size: 24),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'GLOBAL BANNED INGREDIENTS DETECTED (${bans.length})',
                  style: TextStyle(
                    color: Colors.red.shade900,
                    fontWeight: FontWeight.w900,
                    fontSize: 14,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          const Text(
            'The following substances were detected on this product label and are prohibited or heavily restricted in international jurisdictions with documented health hazards:',
            style: TextStyle(fontSize: 12, color: Colors.black87),
          ),
          const SizedBox(height: 12),
          ...bans.map((b) => _buildBannedSubstanceCard(b)),
        ],
      ),
    );
  }

  static Widget _buildBannedSubstanceCard(BannedSubstanceModel sub) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.red.shade200),
        boxShadow: [
          BoxShadow(
            color: Colors.red.withOpacity(0.04),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  sub.canonicalName,
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                    color: Colors.black87,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: sub.isBannedInTarget ? Colors.red.shade700 : Colors.orange.shade700,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  sub.isBannedInTarget ? 'BANNED IN DESTINATION' : 'BANNED GLOBALLY',
                  style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            'Matched on label as: "${sub.matchedTerm}"',
            style: const TextStyle(fontSize: 12, color: Colors.black54, fontStyle: FontStyle.italic),
          ),
          if (sub.description != null) ...[
            const SizedBox(height: 4),
            Text(
              sub.description!,
              style: const TextStyle(fontSize: 12, color: Colors.black87),
            ),
          ],
          const SizedBox(height: 8),
          // Indian Status vs Global Status
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: sub.allowedInIndia ? Colors.amber.shade50 : Colors.red.shade50,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: sub.allowedInIndia ? Colors.amber.shade300 : Colors.red.shade200,
              ),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  sub.allowedInIndia ? Icons.info_outline : Icons.cancel,
                  size: 16,
                  color: sub.allowedInIndia ? Colors.amber.shade900 : Colors.red,
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        sub.allowedInIndia
                            ? 'Indian FSSAI Status: Permitted in India'
                            : 'Indian FSSAI Status: Prohibited in India',
                        style: TextStyle(
                          fontSize: 11.5,
                          fontWeight: FontWeight.bold,
                          color: sub.allowedInIndia ? Colors.amber.shade900 : Colors.red.shade900,
                        ),
                      ),
                      if (sub.indianStatusNote != null)
                        Text(
                          sub.indianStatusNote!,
                          style: const TextStyle(fontSize: 11, color: Colors.black87),
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          // Country Bans breakdown
          Text(
            'Banned / Restricted in ${sub.totalCountriesBanned} Jurisdictions:',
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.black87),
          ),
          const SizedBox(height: 6),
          ...sub.allBans.map((ban) => Container(
                margin: const EdgeInsets.only(bottom: 6),
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.grey.shade50,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: Colors.grey.shade200),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.public, size: 14, color: AppColors.primary),
                        const SizedBox(width: 4),
                        Text(
                          ban.countryName,
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                        ),
                        const Spacer(),
                        if (ban.banYear != null)
                          Text(
                            'Since ${ban.banYear}',
                            style: const TextStyle(fontSize: 10, color: Colors.black54),
                          ),
                      ],
                    ),
                    if (ban.healthConcern != null) ...[
                      const SizedBox(height: 2),
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Health Hazard: ',
                            style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.red),
                          ),
                          Expanded(
                            child: Text(
                              ban.healthConcern!,
                              style: const TextStyle(fontSize: 11, color: Colors.red),
                            ),
                          ),
                        ],
                      ),
                    ],
                    if (ban.legalCitation != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        'Statutory Citation: ${ban.legalCitation}',
                        style: const TextStyle(fontSize: 10.5, color: Colors.black54),
                      ),
                    ],
                    if (ban.reasonSummary != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        ban.reasonSummary!,
                        style: const TextStyle(fontSize: 11, color: Colors.black87),
                      ),
                    ],
                  ],
                ),
              )),
        ],
      ),
    );
  }

  Widget _buildComparisonMatrix() {
    if (_comparison == null || _comparison!.comparisonMatrix.isEmpty) {
      return const SizedBox.shrink();
    }

    final matrix = _comparison!.comparisonMatrix;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Metrological Declaration Comparison',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 4),
          const Text(
            'Side-by-side analysis of mandatory packaging declarations between Indian Legal Metrology (LMPC) and target export regulations.',
            style: TextStyle(fontSize: 12, color: Colors.black54),
          ),
          const SizedBox(height: 12),
          ...matrix.map((item) => _buildMatrixCard(item)),
        ],
      ),
    );
  }

  Widget _buildMatrixCard(ComparisonMatrixItemModel item) {
    Color badgeColor;
    String badgeText;

    switch (item.exportStatus) {
      case 'COMPLIANT':
        badgeColor = Colors.green.shade700;
        badgeText = 'COMPLIANT';
        break;
      case 'PROHIBITED_IN_TARGET':
        badgeColor = Colors.red.shade700;
        badgeText = 'PROHIBITED IN TARGET';
        break;
      case 'DIFFERENT_SPECIFICATION':
        badgeColor = Colors.blue.shade700;
        badgeText = 'DIFFERENT SPEC';
        break;
      case 'ACTION_REQUIRED':
      default:
        badgeColor = Colors.orange.shade800;
        badgeText = 'ACTION REQUIRED';
        break;
    }

    return Card(
      elevation: 1,
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    item.title,
                    style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.bold),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: badgeColor,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    badgeText,
                    style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            // Target Regulation
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.blueGrey.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.gavel, size: 13, color: Colors.blueGrey.shade700),
                      const SizedBox(width: 4),
                      Text(
                        'Target Market Law ($_selectedJurisdictionId):',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: Colors.blueGrey.shade800,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    item.targetRule,
                    style: const TextStyle(fontSize: 12, color: Colors.black87),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 8),
            // Indian Regulation
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.orange.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.flag, size: 13, color: Colors.orange.shade800),
                      const SizedBox(width: 4),
                      Text(
                        'Indian LMPC 2011/2026 Requirement:',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: Colors.orange.shade900,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    item.indianRule,
                    style: const TextStyle(fontSize: 12, color: Colors.black87),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Indian Label Detection: ${item.indianLabelStatus}',
                    style: const TextStyle(
                      fontSize: 11,
                      fontStyle: FontStyle.italic,
                      color: Colors.black54,
                    ),
                  ),
                ],
              ),
            ),
            if (item.actionRequired != null) ...[
              const SizedBox(height: 8),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFFE3F2FD),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.blue.shade300),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.arrow_circle_right, size: 15, color: Colors.blue),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Action Required for Export:',
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: Colors.blue,
                            ),
                          ),
                          Text(
                            item.actionRequired!,
                            style: const TextStyle(fontSize: 12, color: Colors.black87),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('International Metrology'),
        backgroundColor: AppColors.darkBg,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.biotech),
            tooltip: 'Scan Ingredients for Bans',
            onPressed: _showScanIngredientsModal,
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Reload',
            onPressed: _fetchComparison,
          ),
        ],
      ),
      backgroundColor: AppColors.background,
      body: Column(
        children: [
          // Subheader with jurisdiction selector
          Container(
            color: Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Row(
                children: _jurisdictions.map((j) {
                  final isSelected = j.jurisdictionId == _selectedJurisdictionId;
                  return Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                    child: ChoiceChip(
                      label: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(j.flagEmoji, style: const TextStyle(fontSize: 16)),
                          const SizedBox(width: 6),
                          Text(
                            j.countryName.split('(').first.trim(),
                            style: TextStyle(
                              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                      selected: isSelected,
                      selectedColor: AppColors.primary.withOpacity(0.15),
                      checkmarkColor: AppColors.primary,
                      backgroundColor: Colors.grey.shade100,
                      onSelected: (val) {
                        if (val && _selectedJurisdictionId != j.jurisdictionId) {
                          setState(() {
                            _selectedJurisdictionId = j.jurisdictionId;
                          });
                          _fetchComparison();
                        }
                      },
                    ),
                  );
                }).toList(),
              ),
            ),
          ),
          // Content
          Expanded(
            child: _isLoading
                ? const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        CircularProgressIndicator(),
                        SizedBox(height: 12),
                        Text(
                          'Comparing against international regulations...',
                          style: TextStyle(fontSize: 13, color: Colors.black54),
                        ),
                      ],
                    ),
                  )
                : _error != null
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.all(20),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Icon(Icons.error_outline, size: 48, color: Colors.red),
                              const SizedBox(height: 8),
                              Text(
                                _error!,
                                textAlign: TextAlign.center,
                                style: const TextStyle(color: Colors.red),
                              ),
                              const SizedBox(height: 12),
                              ElevatedButton(
                                onPressed: _fetchComparison,
                                child: const Text('Try Again'),
                              ),
                            ],
                          ),
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _fetchComparison,
                        child: ListView(
                          children: [
                            _buildVerdictBanner(),
                            _buildBannedSubstancesSection(),
                            _buildComparisonMatrix(),
                            const SizedBox(height: 32),
                          ],
                        ),
                      ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showScanIngredientsModal,
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.biotech),
        label: const Text('Scan Ingredients'),
      ),
    );
  }
}
