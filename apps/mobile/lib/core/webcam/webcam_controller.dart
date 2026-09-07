import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'webcam_stub.dart'
    if (dart.library.html) 'webcam_web.dart';

abstract class WebcamController {
  factory WebcamController() => createWebcamController();

  bool get isSupported;
  bool get isInitialized;
  bool get isLoading;
  String? get errorMessage;

  Future<void> initialize();
  Widget buildPreview();
  Future<Uint8List?> captureFrame();
  void dispose();
}
