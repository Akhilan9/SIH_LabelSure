import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';
import '../core/api_service.dart';
import '../core/constants.dart';
import '../core/storage_service.dart';
import '../core/sync_manager.dart';
import '../models/inspection.dart';
import 'product_context_screen.dart';

class NewInspectionScreen extends StatefulWidget {
  final Map<String, dynamic>? initialDraft;

  const NewInspectionScreen({Key? key, this.initialDraft}) : super(key: key);

  @override
  _NewInspectionScreenState createState() => _NewInspectionScreenState();
}

class _NewInspectionScreenState extends State<NewInspectionScreen> {
  final _formKey = GlobalKey<FormState>();

  late TextEditingController _commodityController;
  late TextEditingController _brandController;
  late TextEditingController _locationController;
  late TextEditingController _batchController;

  String _packageType = 'STANDARD';
  String _category = 'FOOD';
  bool _isCreating = false;

  @override
  void initState() {
    super.initState();
    final d = widget.initialDraft;
    _commodityController = TextEditingController(text: d?['commodity_name'] ?? 'Atta / Whole Wheat Flour');
    _brandController = TextEditingController(text: d?['brand_name'] ?? 'Aashirvaad');
    _locationController = TextEditingController(text: d?['location'] ?? 'Supermarket Sector 18, Noida');
    _batchController = TextEditingController(text: d?['batch_number'] ?? 'BATCH-2026-X91');
    if (d?['package_type'] != null) _packageType = d!['package_type'];
    if (d?['commodity_category'] != null) _category = d!['commodity_category'];
  }

  void _saveLocalDraft() {
    if (_commodityController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter at least a commodity name to save draft.')),
      );
      return;
    }

    final draftId = widget.initialDraft?['id'] ?? const Uuid().v4();
    final draftData = {
      'id': draftId,
      'commodity_name': _commodityController.text.trim(),
      'brand_name': _brandController.text.trim(),
      'location': _locationController.text.trim(),
      'batch_number': _batchController.text.trim(),
      'package_type': _packageType,
      'commodity_category': _category,
      'saved_at': DateTime.now().toIso8601String(),
    };

    StorageService().saveDraft(draftId, draftData);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Inspection saved to local drafts.')),
    );
    Navigator.pop(context, true);
  }

  Future<void> _proceedToProductContext() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isCreating = true);

    try {
      if (SyncManager().isOnline) {
        final payload = {
          'commodity_name': _commodityController.text.trim(),
          'brand_name': _brandController.text.trim().isNotEmpty ? _brandController.text.trim() : null,
          'retail_establishment': _locationController.text.trim(),
          'batch_number': _batchController.text.trim(),
          'rule_version': 'LMPC-2026-RULES',
          'package_type': _packageType,
        };

        final insp = await ApiService().createInspection(payload);

        if (!mounted) return;
        if (widget.initialDraft != null) {
          StorageService().deleteDraft(widget.initialDraft!['id']);
        }

        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => ProductContextScreen(
              inspectionId: insp.id,
              inspectionNumber: insp.inspectionNumber,
              commodityName: insp.commodityName,
              brandName: insp.brandName,
              initialCategory: _category,
            ),
          ),
        );
        return;
      }
    } catch (_) {
      // Fall through to offline creation
    }

    // Offline Inspection Workflow
    final offlineInsp = SyncManager().createOfflineInspection(
      commodityName: _commodityController.text.trim(),
      brandName: _brandController.text.trim().isNotEmpty ? _brandController.text.trim() : null,
      location: _locationController.text.trim(),
      batchNumber: _batchController.text.trim(),
      packageType: _packageType,
    );

    if (!mounted) return;
    if (widget.initialDraft != null) {
      StorageService().deleteDraft(widget.initialDraft!['id']);
    }

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Offline inspection created. Proceeding to product context.'),
        backgroundColor: Colors.blueGrey,
      ),
    );

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => ProductContextScreen(
          inspectionId: offlineInsp.localId,
          inspectionNumber: 'OFFLINE-${offlineInsp.localId.substring(0, 8).toUpperCase()}',
          commodityName: offlineInsp.commodityName,
          brandName: offlineInsp.brandName,
          initialCategory: _category,
        ),
      ),
    );
    if (mounted) setState(() => _isCreating = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Initiate Field Inspection'),
        backgroundColor: AppColors.darkBg,
        foregroundColor: Colors.white,
      ),
      backgroundColor: AppColors.background,
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Notice Card
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppColors.primaryLight,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: AppColors.border),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.info_outline, color: AppColors.primary, size: 20),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Packaged commodity inspection under Section 18 of Legal Metrology Act, 2009.',
                        style: TextStyle(fontSize: 12, color: AppColors.primaryDark),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),

              // Commodity Name
              TextFormField(
                controller: _commodityController,
                decoration: InputDecoration(
                  labelText: 'Commodity Name *',
                  hintText: 'e.g. Atta, Edible Oil, Shampoo, Biscuits',
                  prefixIcon: const Icon(Icons.shopping_bag_outlined, size: 20),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                ),
                validator: (v) => (v == null || v.trim().isEmpty) ? 'Commodity name is mandatory' : null,
              ),
              const SizedBox(height: 14),

              // Brand / Trade Name
              TextFormField(
                controller: _brandController,
                decoration: InputDecoration(
                  labelText: 'Brand / Trade Name',
                  hintText: 'e.g. Aashirvaad, Fortune, Dove',
                  prefixIcon: const Icon(Icons.branding_watermark_outlined, size: 20),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
              const SizedBox(height: 14),

              // Commodity Category Dropdown
              DropdownButtonFormField<String>(
                value: _category,
                decoration: InputDecoration(
                  labelText: 'Commodity Category',
                  prefixIcon: const Icon(Icons.category_outlined, size: 20),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                ),
                items: const [
                  DropdownMenuItem(value: 'FOOD', child: Text('Food / Edible Item')),
                  DropdownMenuItem(value: 'NON_FOOD', child: Text('Non-Food Package')),
                  DropdownMenuItem(value: 'COSMETIC', child: Text('Cosmetics / Toiletries')),
                  DropdownMenuItem(value: 'ELECTRONICS', child: Text('Electronics & Appliances')),
                  DropdownMenuItem(value: 'MEDICAL_DEVICE', child: Text('Medical Device')),
                ],
                onChanged: (v) => setState(() => _category = v!),
              ),
              const SizedBox(height: 14),

              // Package Type Dropdown
              DropdownButtonFormField<String>(
                value: _packageType,
                decoration: InputDecoration(
                  labelText: 'Package Type',
                  prefixIcon: const Icon(Icons.inventory_2_outlined, size: 20),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                ),
                items: const [
                  DropdownMenuItem(value: 'STANDARD', child: Text('Standard Retail Package')),
                  DropdownMenuItem(value: 'COMBINATION', child: Text('Combination Package')),
                  DropdownMenuItem(value: 'GROUP', child: Text('Group Package')),
                  DropdownMenuItem(value: 'MULTI_PIECE', child: Text('Multi-Piece Package')),
                ],
                onChanged: (v) => setState(() => _packageType = v!),
              ),
              const SizedBox(height: 14),

              // Batch / Lot Number
              TextFormField(
                controller: _batchController,
                decoration: InputDecoration(
                  labelText: 'Batch / Lot Number',
                  hintText: 'e.g. B-9021',
                  prefixIcon: const Icon(Icons.numbers, size: 20),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
              const SizedBox(height: 14),

              // Retail Store / Location
              TextFormField(
                controller: _locationController,
                decoration: InputDecoration(
                  labelText: 'Inspection Store / Premises',
                  hintText: 'Store name, market address, city',
                  prefixIcon: const Icon(Icons.location_on_outlined, size: 20),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
              const SizedBox(height: 24),

              // Action Buttons
              ElevatedButton(
                onPressed: _isCreating ? null : _proceedToProductContext,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
                child: _isCreating
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Text('Proceed to Product Context ->', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
              ),
              const SizedBox(height: 12),

              OutlinedButton.icon(
                onPressed: _saveLocalDraft,
                icon: const Icon(Icons.save_outlined, size: 18),
                label: const Text('Save Local Draft'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
