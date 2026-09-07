import 'package:flutter/material.dart';
import '../core/api_service.dart';
import '../core/constants.dart';
import '../models/inspection.dart';

class InspectorReviewScreen extends StatefulWidget {
  final MobileFinding finding;
  final String inspectionId;

  const InspectorReviewScreen({
    Key? key,
    required this.finding,
    required this.inspectionId,
  }) : super(key: key);

  @override
  _InspectorReviewScreenState createState() => _InspectorReviewScreenState();
}

class _InspectorReviewScreenState extends State<InspectorReviewScreen> {
  late String _selectedStatus;
  late TextEditingController _commentController;
  bool _isSubmitting = false;

  final List<String> _statuses = ['PASS', 'FAIL', 'UNCERTAIN', 'NOT_APPLICABLE'];

  @override
  void initState() {
    super.initState();
    _selectedStatus = widget.finding.inspectorStatus ?? widget.finding.finalStatus;
    _commentController = TextEditingController(text: widget.finding.inspectorComment ?? '');
  }

  Future<void> _handleCommit() async {
    setState(() => _isSubmitting = true);

    try {
      await ApiService().overrideFinding(
        widget.finding.id,
        _selectedStatus,
        _commentController.text.trim().isNotEmpty ? _commentController.text.trim() : null,
      );

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Adjudication recorded in tamper-evident audit ledger.'),
          backgroundColor: AppColors.passGreen,
        ),
      );
      Navigator.pop(context, true);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to record override: ${e.toString()}'),
          backgroundColor: AppColors.failRed,
        ),
      );
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Inspector Adjudication'),
        backgroundColor: AppColors.darkBg,
        foregroundColor: Colors.white,
      ),
      backgroundColor: AppColors.background,
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Statutory Mandate Card
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
                  Text(widget.finding.clauseReference, style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary)),
                  const SizedBox(height: 4),
                  Text(widget.finding.requirementTitle, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Text('Mandated Statutory Condition:', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.textMuted)),
                  Text(widget.finding.expectedCondition, style: const TextStyle(fontSize: 13, height: 1.3)),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      const Text('Original AI Verdict: ', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
                      Text(widget.finding.aiStatus, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 18),

            // Adjudication Controls Card
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
                  const Text('Inspector Decision Override', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                  const SizedBox(height: 12),

                  // Status Selector Buttons
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _statuses.map((status) {
                      final isSelected = _selectedStatus == status;
                      Color activeColor = AppColors.primary;
                      if (status == 'PASS') activeColor = AppColors.passGreen;
                      if (status == 'FAIL') activeColor = AppColors.failRed;
                      if (status == 'UNCERTAIN') activeColor = AppColors.uncertainAmber;

                      return ChoiceChip(
                        label: Text(status, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                        selected: isSelected,
                        selectedColor: activeColor.withOpacity(0.2),
                        labelStyle: TextStyle(color: isSelected ? activeColor : AppColors.textMain),
                        side: BorderSide(color: isSelected ? activeColor : AppColors.border, width: isSelected ? 2 : 1),
                        onSelected: (_) => setState(() => _selectedStatus = status),
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 16),

                  // Statutory Justification Comment
                  const Text('Statutory Justification & Notes:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.textMuted)),
                  const SizedBox(height: 6),
                  TextField(
                    controller: _commentController,
                    maxLines: 4,
                    decoration: InputDecoration(
                      hintText: 'e.g. Verified with manual calibrated micrometer or batch delivery log...',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                      contentPadding: const EdgeInsets.all(12),
                    ),
                  ),
                  const SizedBox(height: 10),
                  const Text(
                    'CRITICAL: Original AI verdict will be preserved in permanent audit logs. Overrides will update the legal certificate.',
                    style: TextStyle(fontSize: 10, color: AppColors.textMuted, fontStyle: FontStyle.italic),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Commit Button
            ElevatedButton(
              onPressed: _isSubmitting ? null : _handleCommit,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              child: _isSubmitting
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Text('Commit Statutory Adjudication', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
            ),
          ],
        ),
      ),
    );
  }
}
