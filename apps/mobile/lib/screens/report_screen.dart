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
  ReportModel? _report;
  bool _isLoading = true;
  bool _isFinalizing = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadOrCreateReport();
  }

  Future<void> _loadOrCreateReport() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // Try to fetch existing report
      try {
        final rep = await ApiService().getReport(widget.inspectionId);
        setState(() {
          _report = rep;
          _isLoading = false;
        });
        return;
      } catch (_) {
        // Generate new report if not exists yet
        final rep = await ApiService().generateReport(widget.inspectionId);
        setState(() {
          _report = rep;
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = e.toString().replaceAll('Exception: ', '');
        _isLoading = false;
      });
    }
  }

  Future<void> _finalizeCase() async {
    setState(() => _isFinalizing = true);
    try {
      await ApiService().finalizeInspection(widget.inspectionId);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Inspection case finalized into permanent Legal Metrology registry.'),
          backgroundColor: AppColors.passGreen,
        ),
      );
      _loadOrCreateReport();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Finalization failed: ${e.toString()}')),
      );
    } finally {
      if (mounted) setState(() => _isFinalizing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final baseUrl = StorageService().baseUrl;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Official Inspection Certificate'),
        backgroundColor: AppColors.darkBg,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadOrCreateReport,
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
                        ElevatedButton(onPressed: _loadOrCreateReport, child: const Text('Retry')),
                      ],
                    ),
                  ),
                )
              : _report == null
                  ? const Center(child: Text('No certificate generated.'))
                  : SingleChildScrollView(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          // Certificate Banner
                          Container(
                            padding: const EdgeInsets.all(20),
                            decoration: BoxDecoration(
                              gradient: const LinearGradient(
                                colors: [Color(0xFF0F172A), Color(0xFF1E293B)],
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                              ),
                              borderRadius: BorderRadius.circular(14),
                              boxShadow: [
                                BoxShadow(color: Colors.black.withOpacity(0.08), blurRadius: 10, offset: const Offset(0, 4)),
                              ],
                            ),
                            child: Column(
                              children: [
                                const Icon(Icons.verified, color: Color(0xFF60A5FA), size: 44),
                                const SizedBox(height: 10),
                                const Text(
                                  'STATUTORY COMPLIANCE CERTIFICATE',
                                  style: TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 0.5),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  _report!.certificateNumber,
                                  style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold, fontFamily: 'monospace'),
                                ),
                                const SizedBox(height: 12),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: _report!.complianceVerdict == 'COMPLIANT' ? AppColors.passGreen : AppColors.failRed,
                                    borderRadius: BorderRadius.circular(20),
                                  ),
                                  child: Text(
                                    _report!.complianceVerdict,
                                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 18),

                          // Metadata Card
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
                                const Text('Statutory Authentication Details', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                                const SizedBox(height: 12),

                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    const Text('Issuing Officer:', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
                                    Text(_report!.generatedBy, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    const Text('Case Number:', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
                                    Text(widget.inspectionNumber, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    const Text('Issued Date:', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
                                    Text(
                                      _report!.generatedAt.isNotEmpty
                                          ? DateTime.tryParse(_report!.generatedAt)?.toLocal().toString().split('.')[0] ?? _report!.generatedAt
                                          : 'Just Now',
                                      style: const TextStyle(fontSize: 12),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 10),
                                const Text('Cryptographic SHA-256 Digest:', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.textMuted)),
                                const SizedBox(height: 2),
                                Container(
                                  padding: const EdgeInsets.all(8),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFFF8FAFC),
                                    borderRadius: BorderRadius.circular(6),
                                    border: Border.all(color: AppColors.border),
                                  ),
                                  child: Text(
                                    _report!.pdfSha256,
                                    style: const TextStyle(fontFamily: 'monospace', fontSize: 10, color: Color(0xFF334155)),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 20),

                          // Download / View PDF Button
                          ElevatedButton.icon(
                            onPressed: () {
                              final fullUrl = _report!.pdfUrl.startsWith('http') ? _report!.pdfUrl : '$baseUrl${_report!.pdfUrl}';
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(content: Text('Certificate URL: $fullUrl')),
                              );
                            },
                            icon: const Icon(Icons.picture_as_pdf),
                            label: const Text('Download Official PDF Report', style: TextStyle(fontWeight: FontWeight.bold)),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.primary,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                            ),
                          ),
                          const SizedBox(height: 12),

                          // Finalize Button
                          OutlinedButton.icon(
                            onPressed: _isFinalizing ? null : _finalizeCase,
                            icon: const Icon(Icons.check_circle_outline, color: AppColors.passGreen),
                            label: _isFinalizing
                                ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                                : const Text('Freeze & Finalize Case', style: TextStyle(color: AppColors.passGreen, fontWeight: FontWeight.bold)),
                            style: OutlinedButton.styleFrom(
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              side: const BorderSide(color: AppColors.passBorder),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                            ),
                          ),
                        ],
                      ),
                    ),
    );
  }
}
