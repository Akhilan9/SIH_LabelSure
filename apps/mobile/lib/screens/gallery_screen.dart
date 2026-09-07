import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../core/constants.dart';
import 'image_review_screen.dart';

class GalleryScreen extends StatefulWidget {
  final String inspectionId;
  final String inspectionNumber;

  const GalleryScreen({
    Key? key,
    required this.inspectionId,
    required this.inspectionNumber,
  }) : super(key: key);

  @override
  _GalleryScreenState createState() => _GalleryScreenState();
}

class _GalleryScreenState extends State<GalleryScreen> {
  final ImagePicker _picker = ImagePicker();
  final List<Map<String, String>> _selectedImages = [];
  bool _isLoading = false;

  final List<String> _viewTypes = ['FRONT', 'BACK', 'SIDE', 'TOP', 'BOTTOM', 'MRP_PANEL'];

  Future<void> _pickImages() async {
    setState(() => _isLoading = true);
    try {
      final List<XFile> picked = await _picker.pickMultiImage(
        maxWidth: 2400,
        maxHeight: 2400,
        imageQuality: 92,
      );

      if (picked.isNotEmpty) {
        setState(() {
          for (var i = 0; i < picked.length; i++) {
            final viewType = i < _viewTypes.length ? _viewTypes[i] : 'FRONT';
            _selectedImages.add({
              'path': picked[i].path,
              'view_type': viewType,
            });
          }
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Gallery pick error: ${e.toString()}')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _proceedToReview() {
    if (_selectedImages.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select at least one photograph.')),
      );
      return;
    }

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ImageReviewScreen(
          inspectionId: widget.inspectionId,
          inspectionNumber: widget.inspectionNumber,
          capturedImages: _selectedImages,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Select Packaging Evidence'),
        backgroundColor: AppColors.darkBg,
        foregroundColor: Colors.white,
        actions: [
          if (_selectedImages.isNotEmpty)
            TextButton(
              onPressed: _proceedToReview,
              child: const Text('Review ->', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            ),
        ],
      ),
      backgroundColor: AppColors.background,
      body: _selectedImages.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.photo_library_outlined, size: 64, color: AppColors.textLight),
                  const SizedBox(height: 16),
                  const Text('No Images Selected Yet', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(height: 6),
                  const Text('Select multiple photographs from packaging photo gallery.', style: TextStyle(color: AppColors.textMuted, fontSize: 12)),
                  const SizedBox(height: 20),
                  ElevatedButton.icon(
                    onPressed: _isLoading ? null : _pickImages,
                    icon: const Icon(Icons.add_photo_alternate),
                    label: const Text('Browse Device Photos'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                    ),
                  ),
                ],
              ),
            )
          : Column(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  color: Colors.white,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('${_selectedImages.length} Photographs Selected', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                      TextButton.icon(
                        onPressed: _pickImages,
                        icon: const Icon(Icons.add, size: 16),
                        label: const Text('Add More', style: TextStyle(fontSize: 12)),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: GridView.builder(
                    padding: const EdgeInsets.all(16),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      crossAxisSpacing: 10,
                      mainAxisSpacing: 10,
                      childAspectRatio: 0.85,
                    ),
                    itemCount: _selectedImages.length,
                    itemBuilder: (ctx, idx) {
                      final item = _selectedImages[idx];
                      return Container(
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: AppColors.border),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Expanded(
                              child: ClipRRect(
                                borderRadius: const BorderRadius.vertical(top: Radius.circular(10)),
                                child: Container(
                                  color: const Color(0xFF0F172A),
                                  child: Center(
                                    child: Image.file(
                                      File(item['path']!),
                                      fit: BoxFit.cover,
                                      width: double.infinity,
                                      errorBuilder: (_, __, ___) => const Icon(Icons.image, color: Colors.white30, size: 36),
                                    ),
                                  ),
                                ),
                              ),
                            ),
                            Padding(
                              padding: const EdgeInsets.all(8),
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  DropdownButton<String>(
                                    value: item['view_type'],
                                    isDense: true,
                                    underline: const SizedBox(),
                                    items: _viewTypes.map((t) => DropdownMenuItem(value: t, child: Text(t, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)))).toList(),
                                    onChanged: (val) {
                                      setState(() {
                                        _selectedImages[idx]['view_type'] = val!;
                                      });
                                    },
                                  ),
                                  IconButton(
                                    icon: const Icon(Icons.delete_outline, size: 18, color: AppColors.failRed),
                                    onPressed: () {
                                      setState(() => _selectedImages.removeAt(idx));
                                    },
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
                Container(
                  padding: const EdgeInsets.all(16),
                  color: Colors.white,
                  child: ElevatedButton(
                    onPressed: _proceedToReview,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    child: Text('Review Evidence (${_selectedImages.length}) ->', style: const TextStyle(fontWeight: FontWeight.bold)),
                  ),
                ),
              ],
            ),
    );
  }
}
