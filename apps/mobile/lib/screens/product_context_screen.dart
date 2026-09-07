import 'package:flutter/material.dart';
import '../core/api_service.dart';
import '../core/constants.dart';
import '../core/sync_manager.dart';
import 'camera_screen.dart';
import 'gallery_screen.dart';

class ProductContextScreen extends StatefulWidget {
  final String inspectionId;
  final String inspectionNumber;
  final String commodityName;
  final String? brandName;
  final String initialCategory;

  const ProductContextScreen({
    Key? key,
    required this.inspectionId,
    required this.inspectionNumber,
    required this.commodityName,
    this.brandName,
    this.initialCategory = 'FOOD',
  }) : super(key: key);

  @override
  _ProductContextScreenState createState() => _ProductContextScreenState();
}

class _ProductContextScreenState extends State<ProductContextScreen> {
  final _formKey = GlobalKey<FormState>();

  late bool _isFood;
  bool _isImported = false;
  late TextEditingController _originController;
  late TextEditingController _netQtyController;
  late TextEditingController _unitController;
  bool _isEcommerce = false;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _isFood = widget.initialCategory == 'FOOD';
    _originController = TextEditingController(text: 'India');
    _netQtyController = TextEditingController(text: '500');
    _unitController = TextEditingController(text: 'g');
  }

  Future<void> _handleSaveAndProceed() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isSaving = true);

    try {
      final qty = double.tryParse(_netQtyController.text.trim());
      final payload = {
        'commodity_category': _isFood ? 'FOOD' : 'NON_FOOD',
        'is_food': _isFood,
        'is_imported': _isImported,
        'origin_country': _originController.text.trim(),
        'declared_net_quantity': qty,
        'declared_unit': _unitController.text.trim(),
        'is_ecommerce': _isEcommerce,
      };

      // Always save to SyncManager offline cache
      SyncManager().updateInspectionContext(widget.inspectionId, payload);

      if (SyncManager().isOnline && !widget.inspectionId.startsWith('OFFLINE-')) {
        try {
          await ApiService().updateProductContext(widget.inspectionId, payload);
        } catch (_) {}
      }

      if (!mounted) return;
      _showEvidenceCaptureChoice();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Context update: ${e.toString().replaceAll("Exception: ", "")}')),
      );
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  void _showEvidenceCaptureChoice() {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Capture Packaging Evidence',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 6),
            const Text(
              'Photograph package panels (Front, Back, MRP Close-Up) using standard alignment.',
              style: TextStyle(fontSize: 12, color: AppColors.textMuted),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: () {
                Navigator.pop(ctx);
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(
                    builder: (_) => CameraScreen(
                      inspectionId: widget.inspectionId,
                      inspectionNumber: widget.inspectionNumber,
                    ),
                  ),
                );
              },
              icon: const Icon(Icons.camera_alt),
              label: const Text('Open Camera Viewfinder'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 12),
              ),
            ),
            const SizedBox(height: 10),
            OutlinedButton.icon(
              onPressed: () {
                Navigator.pop(ctx);
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(
                    builder: (_) => GalleryScreen(
                      inspectionId: widget.inspectionId,
                      inspectionNumber: widget.inspectionNumber,
                    ),
                  ),
                );
              },
              icon: const Icon(Icons.photo_library_outlined),
              label: const Text('Select from Device Gallery'),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 12),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Regulatory Product Context'),
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
              // Case Header Badge Card
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
                        Text(widget.inspectionNumber, style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary)),
                        const Text('STEP 2 OF 4', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.textMuted)),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${widget.commodityName} ${widget.brandName != null ? "(${widget.brandName})" : ""}',
                      style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 2),
                    const Text('Rule Baseline: Legal Metrology (PC) Rules 2011/2026', style: TextStyle(fontSize: 11, color: AppColors.textMuted)),
                  ],
                ),
              ),
              const SizedBox(height: 18),

              // Product Context Form
              Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.border),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Classification & Origin Mandates', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                    const SizedBox(height: 12),

                    // Food Checkbox
                    SwitchListTile(
                      title: const Text('Food / Edible Item', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                      subtitle: const Text('Requires Best Before / Date of Packing under Rule 6', style: TextStyle(fontSize: 11)),
                      value: _isFood,
                      onChanged: (v) => setState(() => _isFood = v),
                      contentPadding: EdgeInsets.zero,
                    ),
                    const Divider(),

                    // Imported Checkbox
                    SwitchListTile(
                      title: const Text('Imported Commodity', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                      subtitle: const Text('Mandates Importer Name & Country of Origin declaration', style: TextStyle(fontSize: 11)),
                      value: _isImported,
                      onChanged: (v) => setState(() => _isImported = v),
                      contentPadding: EdgeInsets.zero,
                    ),
                    const Divider(),

                    // E-commerce Checkbox
                    SwitchListTile(
                      title: const Text('E-Commerce Listing', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                      subtitle: const Text('Digital marketplace display requirements under Rule 6(10)', style: TextStyle(fontSize: 11)),
                      value: _isEcommerce,
                      onChanged: (v) => setState(() => _isEcommerce = v),
                      contentPadding: EdgeInsets.zero,
                    ),
                    const SizedBox(height: 14),

                    // Country of Origin
                    TextFormField(
                      controller: _originController,
                      decoration: InputDecoration(
                        labelText: 'Country of Origin',
                        prefixIcon: const Icon(Icons.public, size: 20),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      validator: (v) => (v == null || v.trim().isEmpty) ? 'Country of origin required' : null,
                    ),
                    const SizedBox(height: 14),

                    // Declared Net Qty & Unit
                    Row(
                      children: [
                        Expanded(
                          flex: 2,
                          child: TextFormField(
                            controller: _netQtyController,
                            keyboardType: const TextInputType.numberWithOptions(decimal: true),
                            decoration: InputDecoration(
                              labelText: 'Declared Net Quantity',
                              hintText: 'e.g. 500',
                              prefixIcon: const Icon(Icons.scale_outlined, size: 20),
                              border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          flex: 1,
                          child: TextFormField(
                            controller: _unitController,
                            decoration: InputDecoration(
                              labelText: 'Unit',
                              hintText: 'g, ml, kg',
                              border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // Save Button
              ElevatedButton(
                onPressed: _isSaving ? null : _handleSaveAndProceed,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
                child: _isSaving
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Text('Save Context & Capture Evidence ->', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
