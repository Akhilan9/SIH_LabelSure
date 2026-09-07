import 'package:flutter/material.dart';
import '../core/api_service.dart';
import '../core/constants.dart';
import '../models/inspection.dart';
import 'inspector_review_screen.dart';
import 'rulelens_screen.dart';
import 'report_screen.dart';

class FindingsScreen extends StatefulWidget {
  final String inspectionId;
  final String inspectionNumber;

  const FindingsScreen({
    Key? key,
    required this.inspectionId,
    required this.inspectionNumber,
  }) : super(key: key);

  @override
  _FindingsScreenState createState() => _FindingsScreenState();
}

class _FindingsScreenState extends State<FindingsScreen> {
  List<MobileFinding> _findings = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchFindings();
  }

  Future<void> _fetchFindings() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final insp = await ApiService().getInspection(widget.inspectionId);
      setState(() {
        _findings = insp.findings;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString().replaceAll('Exception: ', '');
        _isLoading = false;
      });
    }
  }

  Widget _buildVerdictBadge(String status) {
    Color bg;
    Color text;
    IconData icon;

    switch (status) {
      case 'PASS':
        bg = AppColors.passBg;
        text = AppColors.passGreen;
        icon = Icons.check_circle;
        break;
      case 'FAIL':
        bg = AppColors.failBg;
        text = AppColors.failRed;
        icon = Icons.cancel;
        break;
      case 'UNCERTAIN':
        bg = AppColors.uncertainBg;
        text = AppColors.uncertainAmber;
        icon = Icons.help;
        break;
      default:
        bg = AppColors.naBg;
        text = AppColors.naSlate;
        icon = Icons.remove_circle_outline;
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: text),
          const SizedBox(width: 4),
          Text(status, style: TextStyle(color: text, fontWeight: FontWeight.bold, fontSize: 11)),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Compliance Findings'),
        backgroundColor: AppColors.darkBg,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _fetchFindings,
          ),
        ],
      ),
      backgroundColor: AppColors.background,
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: AppColors.failRed)))
              : _findings.isEmpty
                  ? const Center(child: Text('No findings recorded yet.'))
                  : Column(
                      children: [
                        // Sub-header
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                          color: Colors.white,
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text('${_findings.length} Statutory Rules Evaluated', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                              ElevatedButton.icon(
                                onPressed: () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) => ReportScreen(
                                        inspectionId: widget.inspectionId,
                                        inspectionNumber: widget.inspectionNumber,
                                      ),
                                    ),
                                  );
                                },
                                icon: const Icon(Icons.description, size: 14),
                                label: const Text('Official Report', style: TextStyle(fontSize: 12)),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: AppColors.primary,
                                  foregroundColor: Colors.white,
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                  visualDensity: VisualDensity.compact,
                                ),
                              ),
                            ],
                          ),
                        ),

                        // List of Findings
                        Expanded(
                          child: ListView.separated(
                            padding: const EdgeInsets.all(16),
                            itemCount: _findings.length,
                            separatorBuilder: (_, __) => const SizedBox(height: 12),
                            itemBuilder: (ctx, idx) {
                              final f = _findings[idx];
                              return Container(
                                padding: const EdgeInsets.all(14),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(10),
                                  border: Border.all(color: AppColors.border),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                      children: [
                                        Text(
                                          f.clauseReference,
                                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.primary),
                                        ),
                                        _buildVerdictBadge(f.finalStatus),
                                      ],
                                    ),
                                    const SizedBox(height: 6),
                                    Text(
                                      f.requirementTitle,
                                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppColors.textMain),
                                    ),
                                    const SizedBox(height: 6),

                                    // Evidence Comparison
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
                                          Text(
                                            'Observed: ${f.observedValue ?? "[Not Detected]"}',
                                            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF0F172A)),
                                          ),
                                          const SizedBox(height: 2),
                                          Text(
                                            'Mandate: ${f.expectedCondition}',
                                            style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                                          ),
                                        ],
                                      ),
                                    ),
                                    const SizedBox(height: 8),

                                    if (f.inspectorStatus != null)
                                      Container(
                                        padding: const EdgeInsets.all(8),
                                        margin: const EdgeInsets.only(bottom: 8),
                                        decoration: BoxDecoration(
                                          color: const Color(0xFFEFF6FF),
                                          borderRadius: BorderRadius.circular(6),
                                        ),
                                        child: Text(
                                          'Inspector Override: ${f.inspectorStatus} ${f.inspectorComment != null ? '— "${f.inspectorComment}"' : ""}',
                                          style: const TextStyle(fontSize: 11, color: Color(0xFF1E40AF), fontWeight: FontWeight.w600),
                                        ),
                                      ),

                                    // Action Buttons
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.end,
                                      children: [
                                        TextButton.icon(
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
                                          icon: const Icon(Icons.visibility, size: 14),
                                          label: const Text('RuleLens', style: TextStyle(fontSize: 12)),
                                        ),
                                        const SizedBox(width: 8),
                                        ElevatedButton.icon(
                                          onPressed: () async {
                                            final updated = await Navigator.push(
                                              context,
                                              MaterialPageRoute(
                                                builder: (_) => InspectorReviewScreen(
                                                  finding: f,
                                                  inspectionId: widget.inspectionId,
                                                ),
                                              ),
                                            );
                                            if (updated == true) _fetchFindings();
                                          },
                                          icon: const Icon(Icons.rate_review_outlined, size: 14),
                                          label: const Text('Adjudicate', style: TextStyle(fontSize: 12)),
                                          style: ElevatedButton.styleFrom(
                                            backgroundColor: AppColors.primary,
                                            foregroundColor: Colors.white,
                                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                            visualDensity: VisualDensity.compact,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              );
                            },
                          ),
                        ),
                      ],
                    ),
    );
  }
}
