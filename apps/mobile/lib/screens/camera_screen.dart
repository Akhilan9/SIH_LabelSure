import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../core/constants.dart';
import '../core/webcam/webcam_controller.dart';
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
  final WebcamController _webcam = WebcamController();
  final List<Map<String, dynamic>> _capturedImages = []; // [{bytes: Uint8List, view_type: String, name: String, path?: String}]
  String _activeViewType = 'FRONT';
  bool _isCapturing = false;
  bool _isFlashing = false;

  final List<String> _viewTypes = [
    'FRONT',
    'BACK',
    'SIDE',
    'TOP',
    'BOTTOM',
    'MRP_PANEL'
  ];

  @override
  void initState() {
    super.initState();
    _initializeCamera();
    if (!kIsWeb && !_webcam.isSupported) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted && _capturedImages.isEmpty && !_isCapturing) {
          _capturePhoto();
        }
      });
    }
  }

  Future<void> _initializeCamera() async {
    if (kIsWeb || _webcam.isSupported) {
      await _webcam.initialize();
      if (mounted) setState(() {});
    }
  }

  @override
  void dispose() {
    _webcam.dispose();
    super.dispose();
  }

  Future<void> _capturePhoto() async {
    setState(() => _isCapturing = true);
    
    // Quick shutter flash effect
    setState(() => _isFlashing = true);
    Future.delayed(const Duration(milliseconds: 150), () {
      if (mounted) setState(() => _isFlashing = false);
    });

    try {
      if (_webcam.isSupported && _webcam.isInitialized) {
        // Direct capture from live HTML5 webcam stream
        final bytes = await _webcam.captureFrame();
        if (bytes != null && bytes.isNotEmpty) {
          _recordCapturedPhoto(
            bytes: bytes,
            name: '${_activeViewType.toLowerCase()}_${DateTime.now().millisecondsSinceEpoch}.jpg',
          );
        } else {
          throw Exception('Webcam frame capture returned empty buffer.');
        }
      } else {
        // Fallback to ImagePicker (Native Android/iOS or file dialog fallback)
        final XFile? photo = await _picker.pickImage(
          source: ImageSource.camera,
          maxWidth: 2400,
          maxHeight: 2400,
          imageQuality: 92,
        );

        if (photo != null) {
          final bytes = await photo.readAsBytes();
          _recordCapturedPhoto(
            bytes: bytes,
            name: photo.name,
            path: photo.path,
          );
          if (mounted) _proceedToReview();
        } else if (_capturedImages.isEmpty && mounted) {
          Navigator.pop(context);
        }
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Camera capture: ${e.toString().replaceAll("Exception: ", "")}'),
          action: SnackBarAction(
            label: 'Pick File',
            textColor: Colors.amber,
            onPressed: _pickFromGallery,
          ),
        ),
      );
    } finally {
      if (mounted) setState(() => _isCapturing = false);
    }
  }

  void _recordCapturedPhoto({required Uint8List bytes, required String name, String? path}) {
    setState(() {
      _capturedImages.add({
        'bytes': bytes,
        'view_type': _activeViewType,
        'name': name,
        'path': path ?? name,
      });

      // Auto-advance to next view type for seamless multi-angle statutory scanning
      int nextIdx = _viewTypes.indexOf(_activeViewType) + 1;
      if (nextIdx < _viewTypes.length) {
        _activeViewType = _viewTypes[nextIdx];
      }
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('📸 Captured $_activeViewType evidence (${_capturedImages.length} ready)'),
        duration: const Duration(milliseconds: 1400),
      ),
    );
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
        final bytes = await photo.readAsBytes();
        _recordCapturedPhoto(
          bytes: bytes,
          name: photo.name,
          path: photo.path,
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('File selection: ${e.toString().replaceAll("Exception: ", "")}')),
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
            // Center Viewfinder: Live Webcam Stream with HUD Overlays
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
                  clipBehavior: Clip.antiAlias,
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      // Layer 1: Live Video Feed or Native Camera Trigger
                      if (_webcam.isSupported)
                        Positioned.fill(
                          child: _webcam.buildPreview(),
                        )
                      else if (_capturedImages.isEmpty)
                        const Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              CircularProgressIndicator(color: AppColors.primary),
                              SizedBox(height: 16),
                              Text(
                                'Opening Camera Directly...',
                                style: TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold),
                              ),
                            ],
                          ),
                        )
                      else
                        Positioned.fill(
                          child: Image.memory(
                            _capturedImages.last['bytes'] as Uint8List,
                            fit: BoxFit.contain,
                          ),
                        ),

                      // Layer 2: Shutter Flash Effect
                      if (_isFlashing)
                        Positioned.fill(
                          child: Container(color: Colors.white.withOpacity(0.85)),
                        ),

                      // Layer 3: Alignment Guide Reticle
                      IgnorePointer(
                        child: Container(
                          margin: const EdgeInsets.all(24),
                          decoration: BoxDecoration(
                            border: Border.all(
                              color: AppColors.primary.withOpacity(0.8),
                              width: 2.5,
                            ),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Stack(
                            children: [
                              // Corner Accent Marks
                              Positioned(
                                top: 8,
                                left: 8,
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: Colors.black.withOpacity(0.65),
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      const Icon(Icons.crop_free, color: Colors.amber, size: 14),
                                      const SizedBox(width: 4),
                                      Text(
                                        'TARGET: $_activeViewType',
                                        style: const TextStyle(color: Colors.amber, fontSize: 10, fontWeight: FontWeight.bold),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                              Positioned(
                                bottom: 8,
                                left: 8,
                                right: 8,
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: Colors.black.withOpacity(0.65),
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: const Text(
                                    'Ensure MRP, Net Wt & Legal Declarations are in focus',
                                    textAlign: TextAlign.center,
                                    style: TextStyle(color: Colors.white70, fontSize: 10),
                                  ),
                                ),
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

            // Bottom Panel: View Type Selector & Capture Controls
            Positioned(
              bottom: 20,
              left: 0,
              right: 0,
              child: Column(
                children: [
                  // View Type Selector Chips
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
                  const SizedBox(height: 20),

                  // Controls Row (Gallery/File Picker - Shutter - Restart Webcam)
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      // Upload from file
                      IconButton(
                        onPressed: _isCapturing ? null : _pickFromGallery,
                        icon: const Icon(Icons.photo_library, color: Colors.white, size: 28),
                        tooltip: 'Upload from Files / Gallery',
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
                              child: _isCapturing
                                  ? const Padding(
                                      padding: EdgeInsets.all(12),
                                      child: CircularProgressIndicator(strokeWidth: 3, color: Color(0xFF0F172A)),
                                    )
                                  : const Icon(Icons.camera_alt, color: Color(0xFF0F172A), size: 30),
                            ),
                          ),
                        ),
                      ),

                      // Reload / Switch Camera
                      IconButton(
                        onPressed: () async {
                          await _initializeCamera();
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(
                                _webcam.isInitialized
                                    ? 'Webcam refreshed successfully.'
                                    : 'Please ensure camera permissions are allowed in your browser address bar.',
                              ),
                              duration: const Duration(seconds: 2),
                            ),
                          );
                        },
                        icon: const Icon(Icons.refresh, color: Colors.white70, size: 28),
                        tooltip: 'Refresh Camera Stream',
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Text(
                    _webcam.isSupported && _webcam.isInitialized
                        ? 'Tap Camera to capture live webcam frame'
                        : 'Tap Shutter to photograph package or Gallery to pick photo',
                    style: const TextStyle(color: Colors.white54, fontSize: 11),
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
