import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'webcam_controller.dart';

WebcamController createWebcamController() => WebcamStubController();

class WebcamStubController implements WebcamController {
  @override
  bool get isSupported => false;

  @override
  bool get isInitialized => false;

  @override
  bool get isLoading => false;

  @override
  String? get errorMessage => null;

  @override
  Future<void> initialize() async {}

  @override
  Widget buildPreview() => const SizedBox();

  @override
  Future<Uint8List?> captureFrame() async => null;

  @override
  void dispose() {}
}
