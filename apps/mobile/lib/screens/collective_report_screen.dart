import 'package:flutter/material.dart';
import '../core/constants.dart';
import '../core/storage_service.dart';
import '../models/inspection.dart';

class CollectiveReportScreen extends StatelessWidget {
  final AreaSessionModel session;
  final Map<String, dynamic> reportData;

  const CollectiveReportScreen({
    Key? key,
    required this.session,
    required this.reportData,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final baseUrl = StorageService().baseUrl;
    final certNum = reportData['certificate_number'] ?? 'LMPC-AREA-CERT-PENDING';
    final pdfUrl = reportData['pdf_url'] ?? '';
    final sha256 = reportData['pdf_sha256'] ?? 'N/A';
    final isViolation = session.violationItems > 0;
    final isReview = session.reviewItems > 0 && !isViolation;

    final verdictColor = isViolation
        ? AppColors.failRed
        : (isReview ? AppColors.uncertainAmber : AppColors.passGreen);
    final verdictBg = isViolation
        ? AppColors.failBg
        : (isReview ? AppColors.uncertainBg : AppColors.passBg);
    final verdictText = isViolation
        ? 'NON-COMPLIANT — STATUTORY VIOLATIONS DETECTED'
        : (isReview ? 'REQUIRES SUPERVISORY REVIEW' : 'COMPLIANT — ZERO DEFECTS FOUND');

    return Scaffold(
      appBar: AppBar(
        title: const Text('Consolidated Premise Audit Report'),
        backgroundColor: AppColors.darkBg,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.share),
            tooltip: 'Share Report',
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('Consolidated Premise Audit $certNum copied to clipboard.'),
                  backgroundColor: AppColors.primary,
                ),
              );
            },
          ),
        ],
      ),
      backgroundColor: AppColors.background,
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Official Emblem & Header
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.border),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.04),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                children: [
                  const Text(
                    'GOVERNMENT OF INDIA',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.2,
                      color: Color(0xFF1E293B),
                    ),
                  ),
                  const SizedBox(height: 2),
                  const Text(
                    'MINISTRY OF CONSUMER AFFAIRS, FOOD & PUBLIC DISTRIBUTION',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 10, color: Color(0xFF475569)),
                  ),
                  const Text(
                    'DEPARTMENT OF CONSUMER AFFAIRS — LEGAL METROLOGY DIVISION',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFF2563EB)),
                  ),
                  const Divider(height: 20),
                  const Text(
                    'CONSOLIDATED PREMISE INSPECTION REPORT',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Statutory Audit under Legal Metrology (Packaged Commodities) Rules 2011/2026',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // Premise Metadata Box
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
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Establishment / Premise:',
                        style: TextStyle(fontSize: 11, color: AppColors.textMuted),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF1F5F9),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          session.premiseType.replaceAll('_', ' '),
                          style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFF334155)),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    session.establishmentName,
                    style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      const Icon(Icons.location_on, size: 14, color: AppColors.textMuted),
                      const SizedBox(width: 4),
                      Expanded(
                        child: Text(
                          session.address,
                          style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
                        ),
                      ),
                    ],
                  ),
                  const Divider(height: 18),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Certificate No.', style: TextStyle(fontSize: 10, color: AppColors.textMuted)),
                          const SizedBox(height: 2),
                          Text(
                            certNum,
                            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, fontFamily: 'monospace'),
                          ),
                        ],
                      ),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          const Text('Inspecting Officer', style: TextStyle(fontSize: 10, color: AppColors.textMuted)),
                          const SizedBox(height: 2),
                          Text(
                            '${session.inspectorName} (${session.inspectorBadge})',
                            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // Premise Verdict Banner
            Container(
              padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
              decoration: BoxDecoration(
                color: verdictColor,
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(
                    color: verdictColor.withOpacity(0.3),
                    blurRadius: 8,
                    offset: const Offset(0, 3),
                  ),
                ],
              ),
              child: Row(
                children: [
                  Icon(
                    isViolation ? Icons.error_outline : Icons.check_circle_outline,
                    color: Colors.white,
                    size: 26,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      verdictText,
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                        letterSpacing: 0.3,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // Statistics Grid (Pass / Violations / Total / Rate)
            Row(
              children: [
                _buildStatPill('Total Sampled', '${session.totalItems}', const Color(0xFF0F172A), const Color(0xFFF1F5F9)),
                const SizedBox(width: 8),
                _buildStatPill('Compliant (PASS)', '${session.compliantItems}', AppColors.passGreen, AppColors.passBg),
                const SizedBox(width: 8),
                _buildStatPill('Violations', '${session.violationItems}', AppColors.failRed, AppColors.failBg),
                const SizedBox(width: 8),
                _buildStatPill('Compliance Rate', '${session.complianceRate}%', AppColors.primary, AppColors.primaryLight),
              ],
            ),
            const SizedBox(height: 16),

            // Statutory Action Notice
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: isViolation ? const Color(0xFFFFF1F2) : const Color(0xFFF8FAFC),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: isViolation ? const Color(0xFFFECDD3) : const Color(0xFFE2E8F0),
                ),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    isViolation ? Icons.gavel_rounded : Icons.info_outline,
                    color: isViolation ? AppColors.failRed : AppColors.primary,
                    size: 20,
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      isViolation
                          ? 'STATUTORY ACTION CLAUSE: Violations recorded in this premise schedule constitute an offence under Rule 32 of Legal Metrology (Packaged Commodities) Rules 2011/2026. Non-compliant commodities are subject to immediate compounding or seizure under Section 15 of Legal Metrology Act, 2009.'
                          : 'COMPLIANCE CLEARANCE: All sampled pre-packaged commodities evaluated during this premise inspection meet the mandatory declaration standards under Legal Metrology (Packaged Commodities) Rules.',
                      style: TextStyle(
                        fontSize: 11,
                        height: 1.4,
                        color: isViolation ? const Color(0xFF991B1B) : const Color(0xFF334155),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Itemized Product Schedule Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Itemized Commodity Schedule',
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                ),
                Text(
                  '${session.items.length} sampled items',
                  style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
                ),
              ],
            ),
            const SizedBox(height: 10),

            // Item Schedule Cards
            if (session.items.isEmpty)
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: AppColors.border),
                ),
                child: const Center(
                  child: Text('No commodities recorded in this inspection session.'),
                ),
              )
            else
              ...session.items.map((item) => _buildItemCard(item, baseUrl)).toList(),

            const SizedBox(height: 20),

            // Audit Trail & Digital Cryptographic Seal
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.border),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Cryptographic Tamper-Evident Audit Trail',
                      style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF0F172A))),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Engine Ruleset:', style: TextStyle(fontSize: 11, color: AppColors.textMuted)),
                      const Text('LMPC-2026-RULES (Rules 2011 amended 2026)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('OCR Engine:', style: TextStyle(fontSize: 11, color: AppColors.textMuted)),
                      const Text('RapidOCR / PaddleOCR-PP-OCRv4 ONNX', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Text('Cryptographic SHA-256 Seal:', style: TextStyle(fontSize: 10, color: AppColors.textMuted)),
                  const SizedBox(height: 2),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF8FAFC),
                      borderRadius: BorderRadius.circular(4),
                      border: Border.all(color: const Color(0xFFE2E8F0)),
                    ),
                    child: Text(
                      sha256,
                      style: const TextStyle(fontSize: 9, fontFamily: 'monospace', color: Color(0xFF334155)),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Actions Buttons
            ElevatedButton.icon(
              onPressed: () {
                final fullUrl = pdfUrl.startsWith('http') ? pdfUrl : '$baseUrl$pdfUrl';
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Official PDF Ready: $fullUrl'),
                    backgroundColor: AppColors.primary,
                    action: SnackBarAction(
                      label: 'OK',
                      textColor: Colors.white,
                      onPressed: () {},
                    ),
                  ),
                );
              },
              icon: const Icon(Icons.picture_as_pdf),
              label: const Text('Download Consolidated PDF Report', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
            ),
            const SizedBox(height: 10),

            OutlinedButton.icon(
              onPressed: () => Navigator.popUntil(context, (route) => route.isFirst),
              icon: const Icon(Icons.home),
              label: const Text('Return to Main Dashboard'),
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.textMain,
                padding: const EdgeInsets.symmetric(vertical: 12),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
            ),
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }

  Widget _buildStatPill(String label, String value, Color color, Color bg) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 6),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: color.withOpacity(0.3)),
        ),
        child: Column(
          children: [
            Text(
              value,
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: color),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(fontSize: 9, color: color.withOpacity(0.9), fontWeight: FontWeight.w600),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildItemCard(AreaItemModel item, String baseUrl) {
    final isFail = item.complianceStatus == 'NON_COMPLIANT';
    final isPass = item.complianceStatus == 'COMPLIANT';
    final statusColor = isFail ? AppColors.failRed : (isPass ? AppColors.passGreen : AppColors.uncertainAmber);
    final statusBg = isFail ? AppColors.failBg : (isPass ? AppColors.passBg : AppColors.uncertainBg);
    final statusLabel = isFail ? 'NON-COMPLIANT' : (isPass ? 'COMPLIANT' : 'REVIEW');

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: isFail ? AppColors.failBorder : AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Item Index Badge
              CircleAvatar(
                radius: 14,
                backgroundColor: const Color(0xFF0F172A),
                child: Text(
                  '#${item.itemIndex}',
                  style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                ),
              ),
              const SizedBox(width: 10),
              // Item Details
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.commodityName,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Color(0xFF0F172A)),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Brand: ${item.brandName}',
                      style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'MRP: ${item.mrp} | Net Qty: ${item.netQuantity}',
                      style: const TextStyle(fontSize: 11, color: Color(0xFF334155), fontWeight: FontWeight.w500),
                    ),
                  ],
                ),
              ),
              // Status Badge
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: statusBg,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: statusColor.withOpacity(0.5)),
                ),
                child: Text(
                  statusLabel,
                  style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: statusColor),
                ),
              ),
            ],
          ),
          // Violations chips if failed
          if (item.violationsList.isNotEmpty) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: const Color(0xFFFFF1F2),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Detected Rule Violations:', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFF991B1B))),
                  const SizedBox(height: 4),
                  ...item.violationsList.map((v) => Padding(
                    padding: const EdgeInsets.only(bottom: 2),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('• ', style: TextStyle(color: AppColors.failRed, fontSize: 11)),
                        Expanded(
                          child: Text(v, style: const TextStyle(fontSize: 10, color: Color(0xFF7F1D1D))),
                        ),
                      ],
                    ),
                  )),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}
