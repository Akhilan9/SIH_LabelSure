import 'package:flutter/material.dart';
import '../core/api_service.dart';
import '../core/constants.dart';
import '../core/storage_service.dart';
import '../models/inspection.dart';

class EvidenceScreen extends StatefulWidget {
  final String inspectionId;
  final String inspectionNumber;

  const EvidenceScreen({
    Key? key,
    required this.inspectionId,
    required this.inspectionNumber,
  }) : super(key: key);

  @override
  _EvidenceScreenState createState() => _EvidenceScreenState();
}

class _EvidenceScreenState extends State<EvidenceScreen> {
  List<InspectionImageModel> _images = [];
  bool _isLoading = true;
  String? _error;
  InspectionImageModel? _selectedImage;

  @override
  void initState() {
    super.initState();
    _fetchEvidence();
  }

  Future<void> _fetchEvidence() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final insp = await ApiService().getInspection(widget.inspectionId);
      setState(() {
        _images = insp.images;
        if (_images.isNotEmpty) _selectedImage = _images.first;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString().replaceAll('Exception: ', '');
        _isLoading = false;
      });
    }
  }

  String _formatImageUrl(String path) {
    if (path.startsWith('http')) return path;
    final base = StorageService().baseUrl;
    return '$base$path';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Packaging Photographic Evidence'),
        backgroundColor: AppColors.darkBg,
        foregroundColor: Colors.white,
      ),
      backgroundColor: AppColors.background,
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: AppColors.failRed)))
              : _images.isEmpty
                  ? const Center(child: Text('No evidence photographs uploaded yet.'))
                  : Column(
                      children: [
                        // Main Focused Image Viewport
                        if (_selectedImage != null)
                          Container(
                            height: 280,
                            color: const Color(0xFF020617),
                            child: Center(
                              child: Image.network(
                                _formatImageUrl(_selectedImage!.processedPath ?? _selectedImage!.storagePath),
                                fit: BoxFit.contain,
                                errorBuilder: (_, __, ___) => const Center(
                                  child: Text('Photograph offline', style: TextStyle(color: Colors.white54)),
                                ),
                              ),
                            ),
                          ),

                        // Thumbnail Panel Selector
                        Container(
                          height: 80,
                          color: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
                          child: ListView.separated(
                            scrollDirection: Axis.horizontal,
                            itemCount: _images.length,
                            separatorBuilder: (_, __) => const SizedBox(width: 8),
                            itemBuilder: (ctx, idx) {
                              final img = _images[idx];
                              final isSelected = _selectedImage?.id == img.id;
                              return GestureDetector(
                                onTap: () => setState(() => _selectedImage = img),
                                child: Container(
                                  width: 64,
                                  decoration: BoxDecoration(
                                    border: Border.all(color: isSelected ? AppColors.primary : AppColors.border, width: isSelected ? 2 : 1),
                                    borderRadius: BorderRadius.circular(6),
                                    color: const Color(0xFF0F172A),
                                  ),
                                  child: ClipRRect(
                                    borderRadius: BorderRadius.circular(5),
                                    child: Image.network(
                                      _formatImageUrl(img.processedPath ?? img.storagePath),
                                      fit: BoxFit.cover,
                                      errorBuilder: (_, __, ___) => const Icon(Icons.broken_image, color: Colors.white30),
                                    ),
                                  ),
                                ),
                              );
                            },
                          ),
                        ),

                        // Selected Image Diagnostic Details
                        if (_selectedImage != null)
                          Expanded(
                            child: ListView(
                              padding: const EdgeInsets.all(16),
                              children: [
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
                                          Text(
                                            '${_selectedImage!.viewType} PANEL',
                                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppColors.primary),
                                          ),
                                          Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                            decoration: BoxDecoration(
                                              color: _selectedImage!.isAcceptable ? AppColors.passBg : AppColors.uncertainBg,
                                              borderRadius: BorderRadius.circular(6),
                                            ),
                                            child: Text(
                                              _selectedImage!.isAcceptable ? 'VERIFIED EVIDENCE' : 'QUALITY WARNING',
                                              style: TextStyle(
                                                fontSize: 10,
                                                fontWeight: FontWeight.bold,
                                                color: _selectedImage!.isAcceptable ? AppColors.passGreen : AppColors.uncertainAmber,
                                              ),
                                            ),
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 12),

                                      Text('Resolution: ${_selectedImage!.width} × ${_selectedImage!.height} px', style: const TextStyle(fontSize: 12)),
                                      const SizedBox(height: 4),
                                      Text('Blur Sharpness Score: ${_selectedImage!.blurScore.toStringAsFixed(1)}', style: const TextStyle(fontSize: 12)),
                                      const SizedBox(height: 4),
                                      Text('Quality Confidence: ${(_selectedImage!.qualityScore * 100).toInt()}%', style: const TextStyle(fontSize: 12)),
                                      const SizedBox(height: 8),

                                      const Text('SHA-256 Cryptographic Digest:', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.textMuted)),
                                      const SizedBox(height: 2),
                                      Container(
                                        padding: const EdgeInsets.all(8),
                                        decoration: BoxDecoration(
                                          color: const Color(0xFFF8FAFC),
                                          borderRadius: BorderRadius.circular(6),
                                          border: Border.all(color: AppColors.border),
                                        ),
                                        child: Text(
                                          _selectedImage!.sha256Hash,
                                          style: const TextStyle(fontFamily: 'monospace', fontSize: 10, color: Color(0xFF334155)),
                                        ),
                                      ),

                                      if (_selectedImage!.warnings.isNotEmpty) ...[
                                        const SizedBox(height: 12),
                                        ..._selectedImage!.warnings.map((w) => Padding(
                                              padding: const EdgeInsets.only(bottom: 4),
                                              child: Row(
                                                children: [
                                                  const Icon(Icons.warning_amber, size: 14, color: AppColors.failRed),
                                                  const SizedBox(width: 6),
                                                  Expanded(child: Text(w, style: const TextStyle(fontSize: 11, color: AppColors.failRed))),
                                                ],
                                              ),
                                            )),
                                      ],
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                      ],
                    ),
    );
  }
}
