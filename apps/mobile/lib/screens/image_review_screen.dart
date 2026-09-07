import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../core/api_service.dart';
import '../core/constants.dart';
import '../core/sync_manager.dart';
import 'analysis_screen.dart';

class ImageReviewScreen extends StatefulWidget {
  final String inspectionId;
  final String inspectionNumber;
  final List<Map<String, dynamic>> capturedImages; // [{bytes: Uint8List, view_type: String, name: String, path?: String}]

  const ImageReviewScreen({
    Key? key,
    required this.inspectionId,
    required this.inspectionNumber,
    required this.capturedImages,
  }) : super(key: key);

  @override
  _ImageReviewScreenState createState() => _ImageReviewScreenState();
}

class _ImageReviewScreenState extends State<ImageReviewScreen> {
  late List<Map<String, dynamic>> _images;
  bool _isUploading = false;
  double _uploadProgress = 0.0;
  String _uploadStatusText = '';

  @override
  void initState() {
    super.initState();
    _images = List.from(widget.capturedImages);
  }

  Future<void> _uploadAndAnalyze() async {
    if (_images.isEmpty) return;

    final isOfflineInspection = SyncManager().getInspection(widget.inspectionId) != null;
    if (!SyncManager().isOnline || isOfflineInspection) {
      // Offline-First Sync Workflow
      for (final img in _images) {
        final filePath = (img['path'] ?? img['name'] ?? 'offline_img.jpg') as String;
        SyncManager().addOfflineImage(
          localId: widget.inspectionId,
          viewType: (img['view_type'] ?? 'FRONT') as String,
          filePath: filePath,
        );
      }
      SyncManager().queueForSync(widget.inspectionId);

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('📦 Package images saved locally. Case queued for sync (State: QUEUED).'),
          backgroundColor: AppColors.primary,
        ),
      );

      // Return to home where sync banner/status will be shown
      Navigator.popUntil(context, (route) => route.isFirst);
      return;
    }

    setState(() {
      _isUploading = true;
      _uploadProgress = 0.0;
      _uploadStatusText = 'Starting statutory evidence upload...';
    });

    try {
      final total = _images.length;
      for (var i = 0; i < total; i++) {
        final img = _images[i];
        final viewType = (img['view_type'] ?? 'FRONT') as String;
        final fileName = (img['name'] ?? 'evidence_${i + 1}.jpg') as String;

        setState(() {
          _uploadStatusText = 'Uploading $viewType evidence (${i + 1}/$total)...';
          _uploadProgress = (i + 1) / total;
        });

        if (img['bytes'] != null) {
          await ApiService().uploadImageBytes(
            inspectionId: widget.inspectionId,
            bytes: img['bytes'] as Uint8List,
            fileName: fileName,
            viewType: viewType,
          );
        } else if (img['path'] != null) {
          await ApiService().uploadImage(
            widget.inspectionId,
            img['path'] as String,
            viewType,
          );
        }
      }

      if (!mounted) return;

      // Navigate to real-time Analysis Screen
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => AnalysisScreen(
            inspectionId: widget.inspectionId,
            inspectionNumber: widget.inspectionNumber,
          ),
        ),
      );
    } catch (e) {
      setState(() {
        _isUploading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Upload failed: ${e.toString().replaceAll("Exception: ", "")}'),
          backgroundColor: AppColors.failRed,
        ),
      );
    }
  }

  Widget _buildThumbnail(Map<String, dynamic> img) {
    if (img['bytes'] != null && (img['bytes'] as Uint8List).isNotEmpty) {
      return Image.memory(
        img['bytes'] as Uint8List,
        fit: BoxFit.cover,
        errorBuilder: (_, __, ___) => const Icon(Icons.broken_image, color: Colors.white54),
      );
    }
    return const Icon(Icons.image, color: Colors.white54);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Review Packaging Evidence'),
        backgroundColor: AppColors.darkBg,
        foregroundColor: Colors.white,
      ),
      backgroundColor: AppColors.background,
      body: Column(
        children: [
          // Case Banner
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.white,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(widget.inspectionNumber, style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary)),
                    Text('${_images.length} Panels Prepared for AI Inspection', style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.primaryLight,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: const Text('READY FOR OCR', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.primary)),
                ),
              ],
            ),
          ),

          // Upload Progress Banner if active
          if (_isUploading)
            Container(
              padding: const EdgeInsets.all(16),
              color: const Color(0xFFEFF6FF),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(_uploadStatusText, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.primary)),
                      Text('${(_uploadProgress * 100).toInt()}%', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.primary)),
                    ],
                  ),
                  const SizedBox(height: 8),
                  LinearProgressIndicator(
                    value: _uploadProgress,
                    backgroundColor: Colors.white,
                    valueColor: const AlwaysStoppedAnimation<Color>(AppColors.primary),
                  ),
                ],
              ),
            ),

          // Images List
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: _images.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (ctx, idx) {
                final img = _images[idx];
                final viewType = (img['view_type'] ?? 'FRONT') as String;
                final fileName = (img['name'] ?? 'shot_${idx + 1}.jpg') as String;

                return Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Row(
                    children: [
                      // Thumbnail
                      ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: Container(
                          width: 70,
                          height: 70,
                          color: const Color(0xFF0F172A),
                          child: _buildThumbnail(img),
                        ),
                      ),
                      const SizedBox(width: 14),

                      // Details
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: const Color(0xFFF1F5F9),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                '$viewType PANEL',
                                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF334155)),
                              ),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              fileName,
                              style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 2),
                            const Text('Tamper-Evident SHA-256 Validated', style: TextStyle(fontSize: 10, color: Color(0xFF16A34A))),
                          ],
                        ),
                      ),

                      // Delete Button
                      if (!_isUploading)
                        IconButton(
                          icon: const Icon(Icons.delete_outline, color: AppColors.failRed, size: 20),
                          onPressed: () {
                            setState(() => _images.removeAt(idx));
                          },
                        ),
                    ],
                  ),
                );
              },
            ),
          ),

          // Bottom Action
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.white,
            child: ElevatedButton(
              onPressed: (_isUploading || _images.isEmpty) ? null : _uploadAndAnalyze,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              child: _isUploading
                  ? const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)),
                        SizedBox(width: 10),
                        Text('Uploading Evidence to Central Server...'),
                      ],
                    )
                  : const Text('Upload & Run AI Compliance Analysis ->', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
            ),
          ),
        ],
      ),
    );
  }
}
