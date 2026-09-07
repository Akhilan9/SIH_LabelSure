import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../core/constants.dart';
import 'image_review_screen.dart';

class CameraScreen extends StatefulWidget {
  final String inspectionId;
  final String inspectionNumber;

  const CameraScreen({
    Key? key,
    required this.inspectionId,
    required this.inspectionNumber,
  }) : super(key: key);

  @override
  _CameraScreenState createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  final ImagePicker _picker = ImagePicker();
  final List<Map<String, String>> _capturedImages = []; // [{path, view_type}]
  String _activeViewType = 'FRONT';
  bool _isCapturing = false;

  final List<String> _viewTypes = [
    'FRONT',
    'BACK',
    'SIDE',
    'TOP',
    'BOTTOM',
    'MRP_PANEL'
  ];

  Future<void> _capturePhoto() async {
    setState(() => _isCapturing = true);
    try {
      final XFile? photo = await _picker.pickImage(
        source: ImageSource.camera,
        maxWidth: 2400,
        maxHeight: 2400,
        imageQuality: 92,
      );

      if (photo != null) {
        setState(() {
          _capturedImages.add({
            'path': photo.path,
            'view_type': _activeViewType,
          });

          // Auto-advance to next view type for smooth multi-shot workflow
          int nextIdx = _viewTypes.indexOf(_activeViewType) + 1;
          if (nextIdx < _viewTypes.length) {
            _activeViewType = _viewTypes[nextIdx];
          }
        });
      }
    } catch (e) {
      // In simulator/desktop environments where physical camera is unavailable, allow gallery pick or simulate sample
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Camera capture: ${e.toString()}')),
      );
    } finally {
      if (mounted) setState(() => _isCapturing = false);
    }
  }

  Future<void> _pickFromGallery() async {
    setState(() => _isCapturing = true);
    try {
      final XFile? photo = await _picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 2400,
        maxHeight: 2400,
        imageQuality: 92,
      );

      if (photo != null) {
        setState(() {
          _capturedImages.add({
            'path': photo.path,
            'view_type': _activeViewType,
          });

          int nextIdx = _viewTypes.indexOf(_activeViewType) + 1;
          if (nextIdx < _viewTypes.length) {
            _activeViewType = _viewTypes[nextIdx];
          }
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Gallery pick: ${e.toString()}')),
      );
    } finally {
      if (mounted) setState(() => _isCapturing = false);
    }
  }

  void _proceedToReview() {
    if (_capturedImages.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please capture at least one package photograph before proceeding.')),
      );
      return;
    }

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ImageReviewScreen(
          inspectionId: widget.inspectionId,
          inspectionNumber: widget.inspectionNumber,
          capturedImages: _capturedImages,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: Stack(
          children: [
            // Camera Viewfinder Simulation / Preview Container
            Center(
              child: AspectRatio(
                aspectRatio: 3 / 4,
                child: Container(
                  margin: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0F172A),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: Colors.white24),
                  ),
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      // Alignment Frame Overlay
                      Container(
                        margin: const EdgeInsets.all(28),
                        decoration: BoxDecoration(
                          border: Border.all(color: AppColors.primary, width: 2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Icon(Icons.crop_free, color: Colors.white54, size: 48),
                              const SizedBox(height: 12),
                              Text(
                                'Align $_activeViewType Package Label',
                                style: const TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.bold),
                              ),
                              const SizedBox(height: 4),
                              const Text(
                                'Ensure statutory text & MRP are clear and unblurred',
                                style: TextStyle(color: Colors.white38, fontSize: 10),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),

            // Top Bar
            Positioned(
              top: 10,
              left: 16,
              right: 16,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back, color: Colors.white),
                    onPressed: () => Navigator.pop(context),
                  ),
                  Column(
                    children: [
                      Text(
                        widget.inspectionNumber,
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13),
                      ),
                      Text(
                        '${_capturedImages.length} Evidence Shots Taken',
                        style: const TextStyle(color: Colors.white70, fontSize: 11),
                      ),
                    ],
                  ),
                  if (_capturedImages.isNotEmpty)
                    ElevatedButton(
                      onPressed: _proceedToReview,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                      ),
                      child: Text('Review (${_capturedImages.length})'),
                    )
                  else
                    const SizedBox(width: 48),
                ],
              ),
            ),

            // Bottom Panel: View Type Selector & Capture Trigger
            Positioned(
              bottom: 20,
              left: 0,
              right: 0,
              child: Column(
                children: [
                  // View Type Chips
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Row(
                      children: _viewTypes.map((type) {
                        final isSelected = _activeViewType == type;
                        final count = _capturedImages.where((img) => img['view_type'] == type).length;
                        return Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: ChoiceChip(
                            label: Text(count > 0 ? '$type ($count)' : type, style: const TextStyle(fontSize: 11)),
                            selected: isSelected,
                            selectedColor: AppColors.primary,
                            labelStyle: TextStyle(
                              color: isSelected ? Colors.white : Colors.white70,
                              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                            ),
                            backgroundColor: const Color(0xFF1E293B),
                            onSelected: (_) => setState(() => _activeViewType = type),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Controls Row (Gallery - Shutter - Help/Switch)
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      // Gallery Picker
                      IconButton(
                        onPressed: _isCapturing ? null : _pickFromGallery,
                        icon: const Icon(Icons.photo_library, color: Colors.white, size: 28),
                        tooltip: 'Pick from Gallery / Files',
                      ),

                      // Center Shutter Button
                      GestureDetector(
                        onTap: _isCapturing ? null : _capturePhoto,
                        child: Container(
                          width: 76,
                          height: 76,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            border: Border.all(color: Colors.white, width: 4),
                            color: _isCapturing ? AppColors.primary : Colors.white24,
                          ),
                          child: Center(
                            child: Container(
                              width: 58,
                              height: 58,
                              decoration: const BoxDecoration(
                                shape: BoxShape.circle,
                                color: Colors.white,
                              ),
                              child: const Icon(Icons.camera_alt, color: Color(0xFF0F172A), size: 30),
                            ),
                          ),
                        ),
                      ),

                      // Viewfinder Helper
                      IconButton(
                        onPressed: () {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text('Position the label within the frame. Capturing as $_activeViewType panel.'),
                              duration: const Duration(seconds: 2),
                            ),
                          );
                        },
                        icon: const Icon(Icons.info_outline, color: Colors.white70, size: 28),
                        tooltip: 'Camera Help',
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Tap Camera to shoot or Gallery to upload label photos',
                    style: TextStyle(color: Colors.white54, fontSize: 11),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
