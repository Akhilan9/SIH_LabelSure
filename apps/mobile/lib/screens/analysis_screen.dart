import 'package:flutter/material.dart';
import '../core/api_service.dart';
import '../core/constants.dart';
import 'findings_screen.dart';
import 'declarations_screen.dart';
import 'rulelens_screen.dart';

class AnalysisScreen extends StatefulWidget {
  final String inspectionId;
  final String inspectionNumber;

  const AnalysisScreen({
    Key? key,
    required this.inspectionId,
    required this.inspectionNumber,
  }) : super(key: key);

  @override
  _AnalysisScreenState createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen> {
  bool _isAnalyzing = true;
  String? _error;
  Map<String, dynamic>? _analysisResult;

  int _step = 0;
  final List<String> _steps = [
    'Image Quality & Blur Analysis (Laplacian Variance)',
    'PP-OCRv4 Text Extraction & Normalized Bounding Boxes',
    'Statutory Declaration Parser (14 Mandatory Fields)',
    'Legal Metrology Rule Engine Evaluation (LMPC 2026)',
    'RuleLens Grounding & Statutory Explainability Generation'
  ];

  @override
  void initState() {
    super.initState();
    _executeAnalysis();
  }

  Future<void> _executeAnalysis() async {
    setState(() {
      _isAnalyzing = true;
      _error = null;
      _step = 0;
    });

    // Animate through pipeline steps
    for (var i = 0; i < _steps.length; i++) {
      if (!mounted) return;
      setState(() => _step = i);
      await Future.delayed(const Duration(milliseconds: 400));
    }

    try {
      final res = await ApiService().triggerAnalysis(widget.inspectionId);
      if (!mounted) return;
      setState(() {
        _analysisResult = res;
        _isAnalyzing = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString().replaceAll('Exception: ', '');
        _isAnalyzing = false;
      });
    }
  }

  Widget _buildVerdictBanner() {
    final status = _analysisResult?['compliance_status'] ?? 'PENDING';
    Color bgColor;
    Color textColor;
    IconData icon;
    String label;

    switch (status) {
      case 'COMPLIANT':
        bgColor = AppColors.passBg;
        textColor = AppColors.passGreen;
        icon = Icons.check_circle;
        label = 'COMPLIANT WITH LEGAL METROLOGY RULES';
        break;
      case 'NON_COMPLIANT':
        bgColor = AppColors.failBg;
        textColor = AppColors.failRed;
        icon = Icons.cancel;
        label = 'STATUTORY NON-COMPLIANCE DETECTED';
        break;
      case 'REQUIRES_REVIEW':
      default:
        bgColor = AppColors.uncertainBg;
        textColor = AppColors.uncertainAmber;
        icon = Icons.help;
        label = 'REQUIRES INSPECTOR REVIEW / UNCERTAIN EVIDENCE';
        break;
    }

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: textColor.withOpacity(0.4)),
      ),
      child: Column(
        children: [
          Icon(icon, color: textColor, size: 40),
          const SizedBox(height: 8),
          Text(
            label,
            textAlign: TextAlign.center,
            style: TextStyle(color: textColor, fontWeight: FontWeight.bold, fontSize: 13),
          ),
          const SizedBox(height: 4),
          Text(
            'Enforcement Rule Set: ${_analysisResult?["rule_version"] ?? "LMPC-2026-RULES"}',
            style: TextStyle(color: textColor.withOpacity(0.8), fontSize: 11),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Compliance Pipeline'),
        backgroundColor: AppColors.darkBg,
        foregroundColor: Colors.white,
      ),
      backgroundColor: AppColors.background,
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Case Tag
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppColors.border),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(widget.inspectionNumber, style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary)),
                  const Text('ON-DEVICE ORCHESTRATION', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppColors.textMuted)),
                ],
              ),
            ),
            const SizedBox(height: 18),

            if (_isAnalyzing) ...[
              const SizedBox(height: 20),
              const Center(
                child: SizedBox(
                  width: 56,
                  height: 56,
                  child: CircularProgressIndicator(strokeWidth: 3, color: AppColors.primary),
                ),
              ),
              const SizedBox(height: 24),
              const Text(
                'Running PaddleOCR PP-OCRv4 & Rule Engine...',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 20),

              // Animated Pipeline Steps Card
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.border),
                ),
                child: Column(
                  children: List.generate(_steps.length, (idx) {
                    final isDone = idx < _step;
                    final isCurrent = idx == _step;
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      child: Row(
                        children: [
                          if (isDone)
                            const Icon(Icons.check_circle, color: AppColors.passGreen, size: 20)
                          else if (isCurrent)
                            const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary),
                            )
                          else
                            const Icon(Icons.radio_button_unchecked, color: AppColors.textLight, size: 20),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              _steps[idx],
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: isCurrent ? FontWeight.bold : FontWeight.normal,
                                color: isCurrent ? AppColors.textMain : AppColors.textMuted,
                              ),
                            ),
                          ),
                        ],
                      ),
                    );
                  }),
                ),
              ),
            ] else if (_error != null) ...[
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.failBg,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.failBorder),
                ),
                child: Column(
                  children: [
                    const Icon(Icons.error_outline, color: AppColors.failRed, size: 40),
                    const SizedBox(height: 8),
                    const Text('Analysis Failed', style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.failRed)),
                    const SizedBox(height: 4),
                    Text(_error!, textAlign: TextAlign.center, style: const TextStyle(fontSize: 12, color: AppColors.failRed)),
                    const SizedBox(height: 14),
                    ElevatedButton(
                      onPressed: _executeAnalysis,
                      style: ElevatedButton.styleFrom(backgroundColor: AppColors.failRed, foregroundColor: Colors.white),
                      child: const Text('Retry Analysis'),
                    ),
                  ],
                ),
              ),
            ] else ...[
              // Results Display
              _buildVerdictBanner(),
              const SizedBox(height: 18),

              // Summary Counts Card
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.border),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Statutory Rules Breakdown', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                    const SizedBox(height: 12),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        _buildStatTile('PASS', '${_analysisResult?["findings_summary"]?["pass"] ?? 0}', AppColors.passGreen),
                        _buildStatTile('FAIL', '${_analysisResult?["findings_summary"]?["fail"] ?? 0}', AppColors.failRed),
                        _buildStatTile('UNCERTAIN', '${_analysisResult?["findings_summary"]?["uncertain"] ?? 0}', AppColors.uncertainAmber),
                        _buildStatTile('N/A', '${_analysisResult?["findings_summary"]?["not_applicable"] ?? 0}', AppColors.naSlate),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Navigation Buttons
              ElevatedButton.icon(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => FindingsScreen(
                        inspectionId: widget.inspectionId,
                        inspectionNumber: widget.inspectionNumber,
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.checklist_rtl),
                label: const Text('View Compliance Findings Matrix ->', style: TextStyle(fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
              const SizedBox(height: 10),

              OutlinedButton.icon(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => RuleLensScreen(
                        inspectionId: widget.inspectionId,
                        inspectionNumber: widget.inspectionNumber,
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.visibility),
                label: const Text('Inspect in RuleLens™ Viewfinder'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
              const SizedBox(height: 10),

              TextButton.icon(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => DeclarationsScreen(
                        inspectionId: widget.inspectionId,
                        inspectionNumber: widget.inspectionNumber,
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.list_alt, size: 18),
                label: const Text('View Extracted Statutory Declarations'),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildStatTile(String title, String count, Color color) {
    return Column(
      children: [
        Text(count, style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: color)),
        const SizedBox(height: 2),
        Text(title, style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: color)),
      ],
    );
  }
}
