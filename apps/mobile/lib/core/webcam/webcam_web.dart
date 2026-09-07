// ignore_for_file: avoid_web_libraries_in_flutter
import 'dart:async';
import 'dart:html' as html;
import 'dart:typed_data';
import 'dart:ui_web' as ui_web;
import 'package:flutter/material.dart';
import 'webcam_controller.dart';

WebcamController createWebcamController() => WebcamWebController();

class WebcamWebController implements WebcamController {
  html.VideoElement? _videoElement;
  html.MediaStream? _mediaStream;
  String? _viewType;
  bool _initialized = false;
  bool _loading = false;
  String? _errorMessage;

  @override
  bool get isSupported => true;

  @override
  bool get isInitialized => _initialized;

  @override
  bool get isLoading => _loading;

  @override
  String? get errorMessage => _errorMessage;

  @override
  Future<void> initialize() async {
    if (_initialized && _videoElement != null) return;

    _loading = true;
    _errorMessage = null;

    try {
      final mediaDevices = html.window.navigator.mediaDevices;
      if (mediaDevices == null) {
        throw Exception('Webcam capture is not supported in this browser environment.');
      }

      // Generate unique view type identifier for PlatformViewRegistry
      final viewId = 'labelsure-webcam-${DateTime.now().microsecondsSinceEpoch}';
      _viewType = viewId;

      _videoElement = html.VideoElement()
        ..autoplay = true
        ..muted = true
        ..setAttribute('playsinline', 'true')
        ..style.width = '100%'
        ..style.height = '100%'
        ..style.objectFit = 'cover'
        ..style.backgroundColor = '#000000';

      // Request media stream from webcam with environment/rear priority
      html.MediaStream stream;
      try {
        stream = await mediaDevices.getUserMedia({
          'video': {
            'facingMode': {'ideal': 'environment'},
            'width': {'ideal': 1920},
            'height': {'ideal': 1080},
          },
          'audio': false,
        });
      } catch (_) {
        // Fallback to default video constraint if specific facingMode fails
        stream = await mediaDevices.getUserMedia({
          'video': true,
          'audio': false,
        });
      }

      _mediaStream = stream;
      _videoElement!.srcObject = stream;
      await _videoElement!.play();

      // Register view factory with dart:ui_web
      ui_web.platformViewRegistry.registerViewFactory(
        viewId,
        (int id) => _videoElement!,
      );

      _initialized = true;
    } catch (e) {
      _initialized = false;
      final msg = e.toString().toLowerCase();
      if (msg.contains('notallowederror') || msg.contains('permission denied')) {
        _errorMessage = 'Webcam permission was blocked by the browser. Please click the lock or camera icon in your address bar, select "Allow", and try again.';
      } else if (msg.contains('notfounderror') || msg.contains('devices not found')) {
        _errorMessage = 'No camera device detected. Please ensure your webcam is connected or pick photos from files.';
      } else {
        _errorMessage = 'Could not start webcam stream: ${e.toString().replaceAll("Exception: ", "")}';
      }
    } finally {
      _loading = false;
    }
  }

  @override
  Widget buildPreview() {
    if (_errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.videocam_off, color: Colors.orange, size: 48),
              const SizedBox(height: 12),
              const Text(
                'Camera Stream Unavailable',
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
              ),
              const SizedBox(height: 8),
              Text(
                _errorMessage!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white70, fontSize: 11),
              ),
            ],
          ),
        ),
      );
    }

    if (_loading || !_initialized || _viewType == null) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(color: Colors.white),
            SizedBox(height: 12),
            Text('Initializing live webcam...', style: TextStyle(color: Colors.white70, fontSize: 12)),
          ],
        ),
      );
    }

    return HtmlElementView(viewType: _viewType!);
  }

  @override
  Future<Uint8List?> captureFrame() async {
    if (_videoElement == null || !_initialized) return null;

    try {
      final video = _videoElement!;
      final width = video.videoWidth > 0 ? video.videoWidth : 1280;
      final height = video.videoHeight > 0 ? video.videoHeight : 720;

      final canvas = html.CanvasElement(width: width, height: height);
      final ctx = canvas.context2D;
      ctx.drawImage(video, 0, 0);

      final blob = await canvas.toBlob('image/jpeg', 0.92);
      final reader = html.FileReader();
      final completer = Completer<Uint8List>();

      reader.onLoadEnd.listen((_) {
        final result = reader.result;
        if (result is Uint8List) {
          completer.complete(result);
        } else if (result is ByteBuffer) {
          completer.complete(result.asUint8List());
        } else if (result is List<int>) {
          completer.complete(Uint8List.fromList(result));
        } else {
          completer.complete(Uint8List(0));
        }
      });

      reader.readAsArrayBuffer(blob);
      return await completer.future;
    } catch (e) {
      return null;
    }
  }

  @override
  void dispose() {
    try {
      if (_mediaStream != null) {
        for (final track in _mediaStream!.getTracks()) {
          track.stop();
        }
      }
      _videoElement?.pause();
      _videoElement?.srcObject = null;
      _videoElement?.remove();
    } catch (_) {}

    _mediaStream = null;
    _videoElement = null;
    _initialized = false;
  }
}
