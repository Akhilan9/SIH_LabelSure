import 'package:flutter/material.dart';
import '../core/api_service.dart';
import '../core/constants.dart';
import '../models/inspection.dart';

class DeclarationsScreen extends StatefulWidget {
  final String inspectionId;
  final String inspectionNumber;

  const DeclarationsScreen({
    Key? key,
    required this.inspectionId,
    required this.inspectionNumber,
  }) : super(key: key);

  @override
  _DeclarationsScreenState createState() => _DeclarationsScreenState();
}

class _DeclarationsScreenState extends State<DeclarationsScreen> {
  List<DeclarationModel> _declarations = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchDeclarations();
  }

  Future<void> _fetchDeclarations() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final insp = await ApiService().getInspection(widget.inspectionId);
      setState(() {
        _declarations = insp.declarations;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString().replaceAll('Exception: ', '');
        _isLoading = false;
      });
    }
  }

  void _showEditDialog(DeclarationModel decl) {
    final textController = TextEditingController(text: decl.rawText);
    final unitController = TextEditingController(text: decl.unit ?? '');

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Edit ${decl.category}', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('Statutory Declaration Text:', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
            const SizedBox(height: 6),
            TextField(
              controller: textController,
              maxLines: 3,
              decoration: InputDecoration(
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                contentPadding: const EdgeInsets.all(10),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: unitController,
              decoration: InputDecoration(
                labelText: 'Unit (Optional)',
                hintText: 'g, ml, kg',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              final newText = textController.text.trim();
              if (newText.isEmpty) return;

              Navigator.pop(ctx);
              try {
                await ApiService().updateDeclaration(decl.id, {
                  'raw_text': newText,
                  'unit': unitController.text.trim().isNotEmpty ? unitController.text.trim() : null,
                });
                _fetchDeclarations();
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Declaration updated and logged to audit trail.')),
                );
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Update failed: ${e.toString()}')),
                );
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary, foregroundColor: Colors.white),
            child: const Text('Commit Edit'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Statutory Declarations'),
        backgroundColor: AppColors.darkBg,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _fetchDeclarations,
          )
        ],
      ),
      backgroundColor: AppColors.background,
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: AppColors.failRed)))
              : _declarations.isEmpty
                  ? const Center(
                      child: Text(
                        'No statutory declarations extracted yet.',
                        style: TextStyle(color: AppColors.textMuted),
                      ),
                    )
                  : ListView.separated(
                      padding: const EdgeInsets.all(16),
                      itemCount: _declarations.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 12),
                      itemBuilder: (ctx, idx) {
                        final d = _declarations[idx];
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
                                    d.category,
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.primary),
                                  ),
                                  Row(
                                    children: [
                                      if (d.isInspectorEdited)
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                          margin: const EdgeInsets.only(right: 6),
                                          decoration: BoxDecoration(
                                            color: AppColors.uncertainBg,
                                            borderRadius: BorderRadius.circular(4),
                                          ),
                                          child: const Text('EDITED', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppColors.uncertainAmber)),
                                        ),
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                        decoration: BoxDecoration(
                                          color: AppColors.passBg,
                                          borderRadius: BorderRadius.circular(4),
                                        ),
                                        child: Text(
                                          '${(d.confidence * 100).toInt()}% Conf.',
                                          style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppColors.passGreen),
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Text(
                                d.rawText,
                                style: const TextStyle(fontSize: 13, color: AppColors.textMain, height: 1.3),
                              ),
                              if (d.unit != null) ...[
                                const SizedBox(height: 4),
                                Text('Unit: ${d.unit}', style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
                              ],
                              const SizedBox(height: 10),
                              Align(
                                alignment: Alignment.centerRight,
                                child: TextButton.icon(
                                  onPressed: () => _showEditDialog(d),
                                  icon: const Icon(Icons.edit_outlined, size: 14),
                                  label: const Text('Edit Declaration', style: TextStyle(fontSize: 12)),
                                  style: TextButton.styleFrom(
                                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                    visualDensity: VisualDensity.compact,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
    );
  }
}
