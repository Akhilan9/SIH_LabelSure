import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:uuid/uuid.dart';
import 'api_service.dart';
import 'storage_service.dart';

/// 8 Official Lifecycle States for Legal Metrology Packaged Commodity Inspections
class SyncState {
  static const String draft = 'DRAFT';
  static const String queued = 'QUEUED';
  static const String uploading = 'UPLOADING';
  static const String analyzing = 'ANALYZING';
  static const String reviewRequired = 'REVIEW_REQUIRED';
  static const String finalized = 'FINALIZED';
  static const String synced = 'SYNCED';
  static const String syncFailed = 'SYNC_FAILED';

  static const List<String> all = [
    draft,
    queued,
    uploading,
    analyzing,
    reviewRequired,
    finalized,
    synced,
    syncFailed,
  ];
}

class OfflineImage {
  final String id;
  final String viewType;
  final String? filePath;
  final String? base64Data;
  final String filename;
  bool isUploaded;

  OfflineImage({
    required this.id,
    required this.viewType,
    this.filePath,
    this.base64Data,
    required this.filename,
    this.isUploaded = false,
  });

  Map<String, dynamic> toJson() => {
    'id': id,
    'view_type': viewType,
    'file_path': filePath,
    'base64_data': base64Data,
    'filename': filename,
    'is_uploaded': isUploaded,
  };

  factory OfflineImage.fromJson(Map<String, dynamic> json) => OfflineImage(
    id: json['id'] ?? const Uuid().v4(),
    viewType: json['view_type'] ?? 'FRONT',
    filePath: json['file_path'],
    base64Data: json['base64_data'],
    filename: json['filename'] ?? 'panel.jpg',
    isUploaded: json['is_uploaded'] ?? false,
  );
}

class OfflineInspection {
  final String localId;
  final String idempotencyKey; // Immutable UUIDv4 for zero duplicate ingestion
  String? serverId;
  String? inspectionNumber;
  String commodityName;
  String? brandName;
  String? location;
  String? batchNumber;
  String ruleVersion;
  String packageType;
  String? notes;
  String status; // One of SyncState
  Map<String, dynamic> context;
  List<OfflineImage> images;
  String? syncError;
  int retryCount;
  final DateTime createdAt;
  DateTime updatedAt;

  OfflineInspection({
    required this.localId,
    required this.idempotencyKey,
    this.serverId,
    this.inspectionNumber,
    required this.commodityName,
    this.brandName,
    this.location,
    this.batchNumber,
    this.ruleVersion = 'LMPC-2026-RULES',
    this.packageType = 'STANDARD',
    this.notes,
    this.status = SyncState.draft,
    Map<String, dynamic>? context,
    List<OfflineImage>? images,
    this.syncError,
    this.retryCount = 0,
    DateTime? createdAt,
    DateTime? updatedAt,
  })  : context = context ?? {},
        images = images ?? [],
        createdAt = createdAt ?? DateTime.now(),
        updatedAt = updatedAt ?? DateTime.now();

  Map<String, dynamic> toJson() => {
    'local_id': localId,
    'idempotency_key': idempotencyKey,
    'server_id': serverId,
    'inspection_number': inspectionNumber,
    'commodity_name': commodityName,
    'brand_name': brandName,
    'location': location,
    'batch_number': batchNumber,
    'rule_version': ruleVersion,
    'package_type': packageType,
    'notes': notes,
    'status': status,
    'context': context,
    'images': images.map((i) => i.toJson()).toList(),
    'sync_error': syncError,
    'retry_count': retryCount,
    'created_at': createdAt.toIso8601String(),
    'updated_at': updatedAt.toIso8601String(),
  };

  factory OfflineInspection.fromJson(Map<String, dynamic> json) => OfflineInspection(
    localId: json['local_id'],
    idempotencyKey: json['idempotency_key'] ?? const Uuid().v4(),
    serverId: json['server_id'],
    inspectionNumber: json['inspection_number'],
    commodityName: json['commodity_name'] ?? 'Packaged Commodity',
    brandName: json['brand_name'],
    location: json['location'],
    batchNumber: json['batch_number'],
    ruleVersion: json['rule_version'] ?? 'LMPC-2026-RULES',
    packageType: json['package_type'] ?? 'STANDARD',
    notes: json['notes'],
    status: json['status'] ?? SyncState.draft,
    context: Map<String, dynamic>.from(json['context'] ?? {}),
    images: (json['images'] as List? ?? []).map((i) => OfflineImage.fromJson(i)).toList(),
    syncError: json['sync_error'],
    retryCount: json['retry_count'] ?? 0,
    createdAt: DateTime.tryParse(json['created_at'] ?? '') ?? DateTime.now(),
    updatedAt: DateTime.tryParse(json['updated_at'] ?? '') ?? DateTime.now(),
  );
}

class SyncManager extends ChangeNotifier {
  static final SyncManager _instance = SyncManager._internal();
  factory SyncManager() => _instance;
  SyncManager._internal() {
    _startConnectivityMonitor();
  }

  final Map<String, OfflineInspection> _inspections = {};
  final String _clientId = 'mobile-officer-${const Uuid().v4().substring(0, 8)}';

  bool _isOnline = false; // Safe default: offline until server responds
  bool? _manualOnlineOverride;
  bool _isSyncing = false;
  Timer? _monitorTimer;

  bool get isOnline => _manualOnlineOverride ?? _isOnline;
  bool get isSyncing => _isSyncing;
  String get clientId => _clientId;

  List<OfflineInspection> get allInspections => _inspections.values.toList();
  List<OfflineInspection> get queuedInspections =>
      _inspections.values.where((i) => i.status == SyncState.queued || i.status == SyncState.syncFailed).toList();
  List<OfflineInspection> get drafts =>
      _inspections.values.where((i) => i.status == SyncState.draft).toList();
  List<OfflineInspection> get synced =>
      _inspections.values.where((i) => i.status == SyncState.synced || i.status == SyncState.reviewRequired || i.status == SyncState.finalized).toList();

  void setManualOnlineOverride(bool? override) {
    _manualOnlineOverride = override;
    notifyListeners();
    if (isOnline) {
      synchronizePending();
    }
  }

  void _startConnectivityMonitor() {
    _monitorTimer?.cancel();
    if (Platform.environment.containsKey('FLUTTER_TEST')) {
      _isOnline = true;
      return;
    }
    ApiService().checkHealth().then((h) {
      _isOnline = h;
      notifyListeners();
    });
    _monitorTimer = Timer.periodic(const Duration(seconds: 10), (_) async {
      final wasOnline = isOnline;
      final healthy = await ApiService().checkHealth();
      if (_isOnline != healthy) {
        _isOnline = healthy;
        notifyListeners();
        // Auto-synchronize upon reconnect!
        if (!wasOnline && isOnline) {
          synchronizePending();
        }
      }
    });
  }

  void clearEmptyDrafts() {
    _inspections.removeWhere((id, insp) => insp.images.isEmpty && insp.status == SyncState.draft);
    notifyListeners();
  }

  // 1. Create Offline Inspection (status: DRAFT)
  OfflineInspection createOfflineInspection({
    required String commodityName,
    String? brandName,
    String? location,
    String? batchNumber,
    String packageType = 'STANDARD',
    String? notes,
    Map<String, dynamic>? initialContext,
  }) {
    final localId = const Uuid().v4();
    final idempotencyKey = const Uuid().v4(); // Unique key guarantees zero duplicates on sync

    final inspection = OfflineInspection(
      localId: localId,
      idempotencyKey: idempotencyKey,
      commodityName: commodityName,
      brandName: brandName,
      location: location,
      batchNumber: batchNumber,
      packageType: packageType,
      notes: notes,
      status: SyncState.draft,
      context: initialContext ?? {},
    );

    _inspections[localId] = inspection;
    notifyListeners();
    return inspection;
  }

  OfflineInspection? getInspection(String localId) => _inspections[localId];

  // 2. Update Context
  void updateInspectionContext(String localId, Map<String, dynamic> context) {
    final insp = _inspections[localId];
    if (insp != null) {
      insp.context.addAll(context);
      insp.updatedAt = DateTime.now();
      notifyListeners();
    }
  }

  // 3. Attach Offline Image
  void addOfflineImage({
    required String localId,
    required String viewType,
    String? filePath,
    String? base64Data,
    String? filename,
  }) {
    final insp = _inspections[localId];
    if (insp != null) {
      insp.images.add(OfflineImage(
        id: const Uuid().v4(),
        viewType: viewType,
        filePath: filePath,
        base64Data: base64Data,
        filename: filename ?? '${viewType.toLowerCase()}_panel.jpg',
      ));
      insp.updatedAt = DateTime.now();
      notifyListeners();
    }
  }

  // 4. Queue for Sync (status: QUEUED)
  void queueForSync(String localId) {
    final insp = _inspections[localId];
    if (insp != null) {
      insp.status = SyncState.queued;
      insp.syncError = null;
      insp.updatedAt = DateTime.now();
      notifyListeners();

      if (isOnline) {
        synchronizePending();
      }
    }
  }

  // 5. Synchronize All Pending Items with Server
  Future<void> synchronizePending() async {
    if (_isSyncing) return;

    final healthy = await ApiService().checkHealth();
    if (!healthy) {
      _isOnline = false;
      _isSyncing = false;
      notifyListeners();
      return;
    }
    _isOnline = true;
    _isSyncing = true;
    notifyListeners();

    final pending = _inspections.values
        .where((i) => i.status == SyncState.queued || i.status == SyncState.syncFailed)
        .toList();

    for (final insp in pending) {
      await _syncSingleInspection(insp);
    }

    _isSyncing = false;
    notifyListeners();
  }

  Future<void> retryOperation(String localId) async {
    final insp = _inspections[localId];
    if (insp == null) return;

    final healthy = await ApiService().checkHealth();
    if (!healthy) {
      _isOnline = false;
      insp.syncError = 'Server unreachable at ${StorageService().baseUrl}. Check WiFi or Settings.';
      notifyListeners();
      return;
    }

    _isOnline = true;
    insp.status = SyncState.queued;
    insp.syncError = null;
    notifyListeners();
    await _syncSingleInspection(insp);
    notifyListeners();
  }

  Future<void> retryAllFailed() async {
    final failed = _inspections.values.where((i) => i.status == SyncState.syncFailed).toList();
    for (final f in failed) {
      f.status = SyncState.queued;
      f.syncError = null;
    }
    notifyListeners();
    await synchronizePending();
  }

  // Internal: Perform Single Inspection Sync through the 8 states
  Future<void> _syncSingleInspection(OfflineInspection insp) async {
    try {
      // Transition to UPLOADING
      insp.status = SyncState.uploading;
      insp.retryCount += 1;
      insp.updatedAt = DateTime.now();
      notifyListeners();

      // Encode images to base64 if filePath exists and base64Data is missing
      final imagesPayload = <Map<String, dynamic>>[];
      for (final img in insp.images) {
        String? b64 = img.base64Data;
        if (b64 == null && img.filePath != null) {
          try {
            final bytes = await File(img.filePath!).readAsBytes();
            b64 = base64Encode(bytes);
          } catch (_) {}
        }
        if (b64 != null) {
          imagesPayload.add({
            'view_type': img.viewType,
            'image_base64': b64,
            'filename': img.filename,
          });
        }
      }

      final payload = {
        'commodity_name': insp.commodityName,
        'brand_name': insp.brandName,
        'retail_establishment': insp.location,
        'batch_number': insp.batchNumber,
        'rule_version': insp.ruleVersion,
        'notes': insp.notes,
        'context': insp.context,
        'images': imagesPayload,
        'auto_analyze': true,
      };

      // Transition to ANALYZING once upload is sent
      insp.status = SyncState.analyzing;
      notifyListeners();

      final res = await ApiService().syncOfflineInspection(
        payload: payload,
        idempotencyKey: insp.idempotencyKey,
        clientId: _clientId,
      );

      insp.serverId = res['inspection_id'];
      insp.inspectionNumber = res['inspection_number'];
      final serverStatus = res['status'];

      if (serverStatus == 'REVIEW_REQUIRED') {
        insp.status = SyncState.reviewRequired;
      } else {
        insp.status = SyncState.synced;
      }

      insp.syncError = null;
      insp.updatedAt = DateTime.now();
      for (final img in insp.images) {
        img.isUploaded = true;
      }
    } catch (e) {
      insp.status = SyncState.syncFailed;
      insp.syncError = e.toString().replaceAll('Exception: ', '');
      insp.updatedAt = DateTime.now();
    }
  }

  void deleteInspection(String localId) {
    _inspections.remove(localId);
    notifyListeners();
  }

  @override
  void dispose() {
    _monitorTimer?.cancel();
    super.dispose();
  }
}
