import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../core/api_service.dart';
import '../core/constants.dart';
import '../core/storage_service.dart';
import '../models/inspection.dart';
import 'collective_report_screen.dart';

class InspectionAreaScreen extends StatefulWidget {
  final AreaSessionModel? initialSession;

  const InspectionAreaScreen({Key? key, this.initialSession}) : super(key: key);

  @override
  _InspectionAreaScreenState createState() => _InspectionAreaScreenState();
}

class _InspectionAreaScreenState extends State<InspectionAreaScreen> {
  AreaSessionModel? _currentSession;
  bool _isLoading = false;
  bool _isProcessingItem = false;
  String _processingMessage = '';
  final ImagePicker _picker = ImagePicker();

  // Setup Form Controllers
  final _nameController = TextEditingController(text: 'Reliance Smart Superstore');
  final _addressController = TextEditingController(text: '100 Feet Road, Indiranagar, Bengaluru');
  final _districtController = TextEditingController(text: 'Bengaluru East');
  String _selectedPremiseType = 'RETAIL_SUPERMARKET';

  final List<Map<String, String>> _premiseTypes = [
    {'value': 'RETAIL_SUPERMARKET', 'label': 'Retail Supermarket / Mall'},
    {'value': 'WHOLESALE_MANDI', 'label': 'Wholesale Mandi / Market'},
    {'value': 'WAREHOUSE_DEPOT', 'label': 'Warehouse / Logistics Depot'},
    {'value': 'PACKAGING_HUB', 'label': 'Packaging & Bottling Center'},
    {'value': 'ECOMMERCE_FULFILLMENT', 'label': 'E-Commerce Fulfillment Hub'},
  ];

  @override
  void initState() {
    super.initState();
    if (widget.initialSession != null) {
      _currentSession = widget.initialSession;
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _addressController.dispose();
    _districtController.dispose();
    super.dispose();
  }

  Future<void> _createSession() async {
    final name = _nameController.text.trim();
    if (name.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter an establishment or center name')),
      );
      return;
    }

    setState(() => _isLoading = true);
    final user = StorageService().currentUser;

    try {
      final session = await ApiService().createAreaSession({
        'establishment_name': name,
        'premise_type': _selectedPremiseType,
        'address': _addressController.text.trim(),
        'district': _districtController.text.trim(),
        'inspector_name': user?.fullName ?? 'Authorized Legal Metrology Inspector',
        'inspector_badge': user?.badgeNumber ?? 'DL-LM-001',
      });

      setState(() {
        _currentSession = session;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to start area session: $e')),
      );
    }
  }

  Future<void> _captureProductItem(ImageSource source) async {
    if (_currentSession == null) return;

    try {
      final XFile? photo = await _picker.pickImage(
        source: source,
        maxWidth: 2400,
        maxHeight: 2400,
        imageQuality: 90,
      );

      if (photo == null) return;

      setState(() {
        _isProcessingItem = true;
        _processingMessage = 'Extracting label declarations & evaluating LMPC rules...';
      });

      final bytes = await photo.readAsBytes();
      final item = await ApiService().addAreaProductItem(
        sessionId: _currentSession!.id,
        bytes: bytes,
        fileName: photo.name,
      );

      // Refresh session data
      try {
        final updatedSession = await ApiService().getAreaSession(_currentSession!.id);
        setState(() {
          _currentSession = updatedSession;
          _isProcessingItem = false;
        });
      } catch (_) {
        // Local fallback update
        final updatedItems = List<AreaItemModel>.from(_currentSession!.items)..add(item);
        final total = updatedItems.length;
        final compliant = updatedItems.where((i) => i.complianceStatus == 'COMPLIANT').length;
        final violations = updatedItems.where((i) => i.complianceStatus == 'NON_COMPLIANT').length;
        final reviews = updatedItems.where((i) => i.complianceStatus == 'REQUIRES_REVIEW').length;
        final rate = total > 0 ? (compliant / total * 100.0) : 0.0;

        setState(() {
          _currentSession = AreaSessionModel(
            id: _currentSession!.id,
            sessionNumber: _currentSession!.sessionNumber,
            establishmentName: _currentSession!.establishmentName,
            premiseType: _currentSession!.premiseType,
            address: _currentSession!.address,
            district: _currentSession!.district,
            inspectorName: _currentSession!.inspectorName,
            inspectorBadge: _currentSession!.inspectorBadge,
            notes: _currentSession!.notes,
            inspectionDate: _currentSession!.inspectionDate,
            status: _currentSession!.status,
            complianceVerdict: violations > 0 ? 'NON_COMPLIANT' : (reviews > 0 ? 'REQUIRES_REVIEW' : 'COMPLIANT'),
            totalItems: total,
            compliantItems: compliant,
            violationItems: violations,
            reviewItems: reviews,
            complianceRate: double.parse(rate.toStringAsFixed(1)),
            items: updatedItems,
          );
          _isProcessingItem = false;
        });
      }

      if (mounted) {
        final isPass = item.complianceStatus == 'COMPLIANT';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Sampled Item #${item.itemIndex}: ${item.commodityName} -> ${isPass ? 'COMPLIANT (PASS)' : 'VIOLATION DETECTED'}',
            ),
            backgroundColor: isPass ? AppColors.passGreen : AppColors.failRed,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isProcessingItem = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to audit product: $e')),
        );
      }
    }
  }

  Future<void> _deleteItem(AreaItemModel item) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Remove Sampled Product?'),
        content: Text('Remove "${item.commodityName}" (#${item.itemIndex}) from this premise tray?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Remove', style: TextStyle(color: AppColors.failRed)),
          ),
        ],
      ),
    );

    if (confirmed != true || _currentSession == null) return;

    try {
      await ApiService().deleteAreaProductItem(_currentSession!.id, item.id);
      final updated = await ApiService().getAreaSession(_currentSession!.id);
      setState(() => _currentSession = updated);
    } catch (_) {
      // Local fallback removal
      final items = List<AreaItemModel>.from(_currentSession!.items)..removeWhere((i) => i.id == item.id);
      for (int i = 0; i < items.length; i++) {
        // reindex
      }
      setState(() {
        _currentSession = AreaSessionModel(
          id: _currentSession!.id,
          sessionNumber: _currentSession!.sessionNumber,
          establishmentName: _currentSession!.establishmentName,
          premiseType: _currentSession!.premiseType,
          address: _currentSession!.address,
          district: _currentSession!.district,
          inspectorName: _currentSession!.inspectorName,
          inspectorBadge: _currentSession!.inspectorBadge,
          notes: _currentSession!.notes,
          inspectionDate: _currentSession!.inspectionDate,
          status: _currentSession!.status,
          complianceVerdict: _currentSession!.complianceVerdict,
          totalItems: items.length,
          compliantItems: items.where((i) => i.complianceStatus == 'COMPLIANT').length,
          violationItems: items.where((i) => i.complianceStatus == 'NON_COMPLIANT').length,
          reviewItems: items.where((i) => i.complianceStatus == 'REQUIRES_REVIEW').length,
          complianceRate: items.isNotEmpty ? (items.where((i) => i.complianceStatus == 'COMPLIANT').length / items.length * 100) : 0.0,
          items: items,
        );
      });
    }
  }

  Future<void> _generateCollectiveReport() async {
    if (_currentSession == null || _currentSession!.items.isEmpty) return;

    setState(() => _isLoading = true);

    try {
      final reportData = await ApiService().generateCollectiveReport(_currentSession!.id);
      setState(() => _isLoading = false);

      if (!mounted) return;
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => CollectiveReportScreen(
            session: _currentSession!,
            reportData: reportData,
          ),
        ),
      );
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
      if (!mounted) return;
      // Offline fallback navigation
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => CollectiveReportScreen(
            session: _currentSession!,
            reportData: {
              'certificate_number': 'LMPC-AREA-CERT-${_currentSession!.sessionNumber.replaceAll("AREA-", "")}',
              'pdf_url': '/storage/reports/collective_report_${_currentSession!.id}.pdf',
              'pdf_sha256': 'OFFLINE_SEAL_${DateTime.now().millisecondsSinceEpoch}',
            },
          ),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          _currentSession == null ? 'Inspection Center Hub' : _currentSession!.establishmentName,
          style: const TextStyle(fontSize: 16),
        ),
        backgroundColor: AppColors.darkBg,
        foregroundColor: Colors.white,
        actions: [
          if (_currentSession != null)
            IconButton(
              icon: const Icon(Icons.refresh),
              tooltip: 'Refresh Session',
              onPressed: () async {
                setState(() => _isLoading = true);
                try {
                  final s = await ApiService().getAreaSession(_currentSession!.id);
                  setState(() {
                    _currentSession = s;
                    _isLoading = false;
                  });
                } catch (_) {
                  setState(() => _isLoading = false);
                }
              },
            ),
        ],
      ),
      backgroundColor: AppColors.background,
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : (_currentSession == null ? _buildPremiseSetupView() : _buildActiveAuditView()),
    );
  }

  // 1. Setup Screen for establishing a Center or Premise Session
  Widget _buildPremiseSetupView() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF1E293B), Color(0xFF0F172A)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
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
                        color: AppColors.primary.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(Icons.storefront, color: Colors.blueAccent, size: 28),
                    ),
                    const SizedBox(width: 14),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Inspection Area / Center',
                            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 17),
                          ),
                          SizedBox(height: 3),
                          Text(
                            'Audit multiple products & generate a collective report',
                            style: TextStyle(color: Colors.white70, fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const Divider(color: Colors.white12, height: 24),
                const Text(
                  'Establish a premise session to sample packaged commodities sequentially at a retail outlet, mandi, warehouse, or packaging hub. The system generates an official consolidated compliance certificate covering all items.',
                  style: TextStyle(color: Colors.white70, fontSize: 12, height: 1.4),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Premise Details Form Card
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            elevation: 0,
            color: Colors.white,
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Premise & Establishment Profile', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                  const SizedBox(height: 16),

                  // Establishment Name
                  TextField(
                    controller: _nameController,
                    decoration: const InputDecoration(
                      labelText: 'Establishment / Center Name *',
                      hintText: 'e.g. Reliance Smart Superstore',
                      prefixIcon: Icon(Icons.business),
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 14),

                  // Premise Type Dropdown
                  DropdownButtonFormField<String>(
                    value: _selectedPremiseType,
                    decoration: const InputDecoration(
                      labelText: 'Premise Category *',
                      prefixIcon: Icon(Icons.category),
                      border: OutlineInputBorder(),
                    ),
                    items: _premiseTypes.map((t) {
                      return DropdownMenuItem<String>(
                        value: t['value'],
                        child: Text(t['label']!, style: const TextStyle(fontSize: 13)),
                      );
                    }).toList(),
                    onChanged: (val) {
                      if (val != null) setState(() => _selectedPremiseType = val);
                    },
                  ),
                  const SizedBox(height: 14),

                  // Address
                  TextField(
                    controller: _addressController,
                    decoration: const InputDecoration(
                      labelText: 'Physical Address / Market Location',
                      hintText: 'Street, Area, Pin Code',
                      prefixIcon: Icon(Icons.place),
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 14),

                  // District
                  TextField(
                    controller: _districtController,
                    decoration: const InputDecoration(
                      labelText: 'Jurisdiction District',
                      prefixIcon: Icon(Icons.map),
                      border: OutlineInputBorder(),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          ElevatedButton.icon(
            onPressed: _createSession,
            icon: const Icon(Icons.play_arrow),
            label: const Text('Start Premise Audit & Sample Products', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
          ),
        ],
      ),
    );
  }

  // 2. Active Premise Audit Screen with Rapid Shutter Tray
  Widget _buildActiveAuditView() {
    final s = _currentSession!;
    final baseUrl = StorageService().baseUrl;

    return Column(
      children: [
        // Top Premise Banner & Live Scorecard
        Container(
          padding: const EdgeInsets.all(16),
          color: Colors.white,
          child: Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: const Color(0xFFEFF6FF),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                s.sessionNumber,
                                style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppColors.primary),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              s.premiseType.replaceAll('_', ' '),
                              style: const TextStyle(fontSize: 10, color: AppColors.textMuted),
                            ),
                          ],
                        ),
                        const SizedBox(height: 2),
                        Text(
                          s.establishmentName,
                          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.edit_outlined, size: 20, color: AppColors.textMuted),
                    tooltip: 'Change Establishment',
                    onPressed: () => setState(() => _currentSession = null),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // Scorecard Matrix
              Row(
                children: [
                  _buildMetricCell('Sampled', '${s.totalItems}', const Color(0xFF0F172A), const Color(0xFFF1F5F9)),
                  const SizedBox(width: 6),
                  _buildMetricCell('Pass', '${s.compliantItems}', AppColors.passGreen, AppColors.passBg),
                  const SizedBox(width: 6),
                  _buildMetricCell('Violations', '${s.violationItems}', AppColors.failRed, AppColors.failBg),
                  const SizedBox(width: 6),
                  _buildMetricCell('Rate', '${s.complianceRate}%', AppColors.primary, AppColors.primaryLight),
                ],
              ),
            ],
          ),
        ),

        // Shutter Action Card
        Container(
          margin: const EdgeInsets.all(12),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF2563EB), Color(0xFF1E40AF)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(14),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF2563EB).withOpacity(0.3),
                blurRadius: 8,
                offset: const Offset(0, 3),
              ),
            ],
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Rapid Product Shutter',
                      style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Point camera at item #${s.items.length + 1} to grab and audit instantly',
                      style: const TextStyle(color: Colors.white70, fontSize: 11),
                    ),
                  ],
                ),
              ),
              ElevatedButton.icon(
                onPressed: _isProcessingItem ? null : () => _captureProductItem(ImageSource.camera),
                icon: const Icon(Icons.camera_alt, size: 18),
                label: const Text('Snap Item', style: TextStyle(fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white,
                  foregroundColor: AppColors.primary,
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
              const SizedBox(width: 6),
              IconButton(
                icon: const Icon(Icons.photo_library, color: Colors.white70, size: 22),
                tooltip: 'Pick from Gallery',
                onPressed: _isProcessingItem ? null : () => _captureProductItem(ImageSource.gallery),
              ),
            ],
          ),
        ),

        // Processing Banner
        if (_isProcessingItem)
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: BoxDecoration(
              color: const Color(0xFFFEF3C7),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: const Color(0xFFFCD34D)),
            ),
            child: Row(
              children: [
                const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFFD97706)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    _processingMessage,
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF92400E)),
                  ),
                ),
              ],
            ),
          ),

        // Sampled Products Tray Header
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Sampled Products Tray (${s.items.length})',
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Color(0xFF0F172A)),
              ),
              if (s.items.isNotEmpty)
                Text(
                  '${s.violationItems} violation(s)',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                    color: s.violationItems > 0 ? AppColors.failRed : AppColors.passGreen,
                  ),
                ),
            ],
          ),
        ),

        // Product Tray List
        Expanded(
          child: s.items.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.inventory_2_outlined, size: 48, color: Colors.grey.shade400),
                      const SizedBox(height: 12),
                      const Text(
                        'No commodities sampled yet at this center',
                        style: TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF475569)),
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        'Tap "Snap Item" to photograph your first product label',
                        style: TextStyle(fontSize: 12, color: AppColors.textMuted),
                      ),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  itemCount: s.items.length,
                  itemBuilder: (ctx, idx) {
                    final item = s.items[idx];
                    return _buildTrayItemCard(item, baseUrl);
                  },
                ),
        ),

        // Bottom Bar: Generate Collective Report
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white,
            border: Border(top: BorderSide(color: AppColors.border)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 6,
                offset: const Offset(0, -2),
              ),
            ],
          ),
          child: SafeArea(
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        '${s.totalItems} Items in Report',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                      ),
                      Text(
                        s.violationItems > 0
                            ? '${s.violationItems} violation(s) flagged for seizure'
                            : 'All sampled items compliant',
                        style: TextStyle(
                          fontSize: 11,
                          color: s.violationItems > 0 ? AppColors.failRed : AppColors.passGreen,
                        ),
                      ),
                    ],
                  ),
                ),
                ElevatedButton.icon(
                  onPressed: s.items.isEmpty ? null : _generateCollectiveReport,
                  icon: const Icon(Icons.summarize, size: 18),
                  label: const Text('Generate Collective Report', style: TextStyle(fontWeight: FontWeight.bold)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF0F172A),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildMetricCell(String label, String value, Color color, Color bg) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 4),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(6),
        ),
        child: Column(
          children: [
            Text(
              value,
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: color),
            ),
            Text(
              label,
              style: TextStyle(fontSize: 9, color: color.withOpacity(0.9), fontWeight: FontWeight.w600),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTrayItemCard(AreaItemModel item, String baseUrl) {
    final isFail = item.complianceStatus == 'NON_COMPLIANT';
    final isPass = item.complianceStatus == 'COMPLIANT';
    final statusColor = isFail ? AppColors.failRed : (isPass ? AppColors.passGreen : AppColors.uncertainAmber);
    final statusBg = isFail ? AppColors.failBg : (isPass ? AppColors.passBg : AppColors.uncertainBg);

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: BorderSide(color: isFail ? AppColors.failBorder : AppColors.border),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CircleAvatar(
                  radius: 13,
                  backgroundColor: const Color(0xFF1E293B),
                  child: Text('#${item.itemIndex}', style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        item.commodityName,
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Color(0xFF0F172A)),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Brand: ${item.brandName} | MRP: ${item.mrp}',
                        style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                      ),
                      Text(
                        'Declared Net Qty: ${item.netQuantity}',
                        style: const TextStyle(fontSize: 11, color: Color(0xFF334155)),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: statusBg,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: statusColor.withOpacity(0.5)),
                  ),
                  child: Text(
                    isFail ? 'VIOLATION' : (isPass ? 'PASS' : 'REVIEW'),
                    style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: statusColor),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 16, color: Colors.grey),
                  tooltip: 'Remove',
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                  onPressed: () => _deleteItem(item),
                ),
              ],
            ),
            if (item.violationsList.isNotEmpty) ...[
              const SizedBox(height: 8),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFF1F2),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: item.violationsList.map((v) => Text(
                    '• $v',
                    style: const TextStyle(fontSize: 10, color: Color(0xFF991B1B)),
                  )).toList(),
                ),
              ),
            ],
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                OutlinedButton.icon(
                  onPressed: () => _viewIndividualReport(item),
                  icon: const Icon(Icons.picture_as_pdf, size: 14),
                  label: const Text('Individual Certificate', style: TextStyle(fontSize: 11)),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    visualDensity: VisualDensity.compact,
                    foregroundColor: const Color(0xFF0F172A),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _viewIndividualReport(AreaItemModel item) async {
    if (_currentSession == null) return;
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => const Center(child: CircularProgressIndicator()),
    );

    try {
      final rep = await ApiService().generateAreaItemReport(_currentSession!.id, item.id);
      if (!mounted) return;
      Navigator.pop(context); // close loader

      final cert = rep['certificate_number'] ?? 'LMPC-CERT';
      final pdf = rep['pdf_url'] ?? '';
      final baseUrl = StorageService().baseUrl;
      final fullUrl = pdf.startsWith('http') ? pdf : '$baseUrl$pdf';

      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: Row(
            children: [
              const Icon(Icons.verified, color: AppColors.passGreen, size: 22),
              const SizedBox(width: 8),
              const Text('Individual Certificate', style: TextStyle(fontSize: 16)),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(item.commodityName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
              const SizedBox(height: 4),
              Text('Brand: ${item.brandName} | MRP: ${item.mrp}', style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
              const Divider(height: 20),
              Text('Certificate: $cert', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, fontFamily: 'monospace')),
              const SizedBox(height: 6),
              Text(
                'Verdict: ${item.complianceStatus}',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: item.complianceStatus == 'COMPLIANT' ? AppColors.passGreen : AppColors.failRed,
                ),
              ),
              const SizedBox(height: 12),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(color: const Color(0xFFF1F5F9), borderRadius: BorderRadius.circular(6)),
                child: Text('PDF: $fullUrl', style: const TextStyle(fontSize: 10, fontFamily: 'monospace', color: Color(0xFF334155))),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Close'),
            ),
            ElevatedButton.icon(
              onPressed: () {
                Navigator.pop(ctx);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Report Ready: $fullUrl'), backgroundColor: AppColors.primary),
                );
              },
              icon: const Icon(Icons.download, size: 16),
              label: const Text('Download PDF'),
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary, foregroundColor: Colors.white),
            ),
          ],
        ),
      );
    } catch (e) {
      if (mounted) {
        Navigator.pop(context); // close loader
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Item report: $e')),
        );
      }
    }
  }
}
