import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import '../models/inspection.dart';
import 'storage_service.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  final StorageService _storage = StorageService();

  String get _baseUrl => _storage.baseUrl;
  String? get _token => _storage.authToken;

  Map<String, String> _headers({bool isJson = true}) {
    final headers = <String, String>{};
    if (isJson) {
      headers['Content-Type'] = 'application/json';
    }
    if (_token != null) {
      headers['Authorization'] = 'Bearer $_token';
    }
    return headers;
  }

  // 1. Authentication
  Future<UserModel> login(String username, String password) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'username': username, 'password': password}),
    );

    if (res.statusCode == 200) {
      final data = jsonDecode(res.body);
      final user = UserModel.fromJson(data);
      _storage.setAuth(data['access_token'], user);
      return user;
    } else {
      final err = jsonDecode(res.body);
      throw Exception(err['error']?['message'] ?? 'Login failed (${res.statusCode})');
    }
  }

  // 2. Inspections
  Future<List<InspectionModel>> listInspections() async {
    final res = await http.get(
      Uri.parse('$_baseUrl/api/inspections'),
      headers: _headers(),
    );

    if (res.statusCode == 200) {
      final list = jsonDecode(res.body) as List;
      final inspections = list.map((i) => InspectionModel.fromJson(i)).toList();
      _storage.cacheInspections(inspections);
      return inspections;
    } else {
      throw Exception('Failed to fetch inspections');
    }
  }

  Future<InspectionModel> getInspection(String id) async {
    final res = await http.get(
      Uri.parse('$_baseUrl/api/inspections/$id'),
      headers: _headers(),
    );

    if (res.statusCode == 200) {
      return InspectionModel.fromJson(jsonDecode(res.body));
    } else {
      throw Exception('Inspection not found');
    }
  }

  Future<InspectionModel> createInspection(Map<String, dynamic> payload) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/inspections'),
      headers: _headers(),
      body: jsonEncode(payload),
    );

    if (res.statusCode == 201) {
      return InspectionModel.fromJson(jsonDecode(res.body));
    } else {
      final err = jsonDecode(res.body);
      throw Exception(err['error']?['message'] ?? 'Failed to create inspection');
    }
  }

  // 3. Product Context
  Future<void> updateProductContext(String inspectionId, Map<String, dynamic> payload) async {
    final res = await http.patch(
      Uri.parse('$_baseUrl/api/inspections/$inspectionId/context'),
      headers: _headers(),
      body: jsonEncode(payload),
    );

    if (res.statusCode != 200) {
      throw Exception('Failed to update product context');
    }
  }

  // 4. Image Upload
  Future<InspectionImageModel> uploadImageBytes({
    required String inspectionId,
    required Uint8List bytes,
    required String fileName,
    required String viewType,
  }) async {
    final uri = Uri.parse('$_baseUrl/api/inspections/$inspectionId/images');
    final request = http.MultipartRequest('POST', uri);

    if (_token != null) {
      request.headers['Authorization'] = 'Bearer $_token';
    }
    request.fields['view_type'] = viewType;
    request.files.add(http.MultipartFile.fromBytes(
      'file',
      bytes,
      filename: fileName,
    ));

    final streamedRes = await request.send();
    final res = await http.Response.fromStream(streamedRes);

    if (res.statusCode == 201) {
      return InspectionImageModel.fromJson(jsonDecode(res.body));
    } else {
      throw Exception('Image upload failed: ${res.body}');
    }
  }

  Future<InspectionImageModel> uploadImage(String inspectionId, String filePath, String viewType) async {
    final uri = Uri.parse('$_baseUrl/api/inspections/$inspectionId/images');
    final request = http.MultipartRequest('POST', uri);
    
    if (_token != null) {
      request.headers['Authorization'] = 'Bearer $_token';
    }
    request.fields['view_type'] = viewType;
    request.files.add(await http.MultipartFile.fromPath('file', filePath));

    final streamedRes = await request.send();
    final res = await http.Response.fromStream(streamedRes);

    if (res.statusCode == 201) {
      return InspectionImageModel.fromJson(jsonDecode(res.body));
    } else {
      throw Exception('Image upload failed: ${res.body}');
    }
  }

  // 5. Compliance Analysis
  Future<Map<String, dynamic>> triggerAnalysis(String inspectionId) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/inspections/$inspectionId/analyze'),
      headers: _headers(),
    );

    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    } else {
      throw Exception('Analysis failed (${res.statusCode})');
    }
  }

  // 6. RuleLens Dossier
  Future<Map<String, dynamic>> getRuleLens(String inspectionId) async {
    final res = await http.get(
      Uri.parse('$_baseUrl/api/inspections/$inspectionId/rulelens'),
      headers: _headers(),
    );

    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    } else {
      throw Exception('Failed to fetch RuleLens data');
    }
  }

  // 7. Adjudication / Override Finding
  Future<void> overrideFinding(String findingId, String inspectorStatus, String? comment) async {
    final res = await http.patch(
      Uri.parse('$_baseUrl/api/findings/$findingId'),
      headers: _headers(),
      body: jsonEncode({
        'inspector_status': inspectorStatus,
        'inspector_comment': comment,
      }),
    );

    if (res.statusCode != 200) {
      throw Exception('Failed to record inspector finding override');
    }
  }

  // 8. Edit Declaration
  Future<void> updateDeclaration(String declarationId, Map<String, dynamic> payload) async {
    final res = await http.patch(
      Uri.parse('$_baseUrl/api/declarations/$declarationId'),
      headers: _headers(),
      body: jsonEncode(payload),
    );

    if (res.statusCode != 200) {
      throw Exception('Failed to update declaration');
    }
  }

  // 9. Finalize Inspection
  Future<void> finalizeInspection(String inspectionId) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/inspections/$inspectionId/finalize'),
      headers: _headers(),
    );

    if (res.statusCode != 200) {
      throw Exception('Failed to finalize inspection case');
    }
  }

  // 10. Reports
  Future<ReportModel> generateReport(String inspectionId) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/inspections/$inspectionId/report'),
      headers: _headers(),
    );

    if (res.statusCode == 201) {
      return ReportModel.fromJson(jsonDecode(res.body));
    } else {
      throw Exception('Failed to generate compliance report');
    }
  }

  Future<ReportModel> getReport(String inspectionId) async {
    final res = await http.get(
      Uri.parse('$_baseUrl/api/inspections/$inspectionId/report'),
      headers: _headers(),
    );

    if (res.statusCode == 200) {
      return ReportModel.fromJson(jsonDecode(res.body));
    } else {
      throw Exception('Report not found');
    }
  }

  // 11. Offline Sync Endpoints
  Future<bool> checkHealth() async {
    try {
      final res = await http.get(
        Uri.parse('$_baseUrl/health'),
      ).timeout(const Duration(seconds: 4));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<Map<String, dynamic>> syncOfflineInspection({
    required Map<String, dynamic> payload,
    required String idempotencyKey,
    required String clientId,
  }) async {
    final headers = _headers();
    headers['X-Idempotency-Key'] = idempotencyKey;
    headers['X-Client-ID'] = clientId;

    final res = await http.post(
      Uri.parse('$_baseUrl/api/sync/inspections'),
      headers: headers,
      body: jsonEncode(payload),
    );

    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    } else {
      final err = jsonDecode(res.body);
      throw Exception(err['error']?['message'] ?? 'Sync failed (${res.statusCode})');
    }
  }

  Future<Map<String, dynamic>> getSyncStatus(String idempotencyKey) async {
    final res = await http.get(
      Uri.parse('$_baseUrl/api/sync/status/$idempotencyKey'),
      headers: _headers(),
    );

    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    } else {
      throw Exception('Failed to get sync status');
    }
  }

  Future<List<Map<String, dynamic>>> listSyncQueue({String? clientId}) async {
    String url = '$_baseUrl/api/sync/queue';
    if (clientId != null) {
      url += '?client_id=$clientId';
    }
    final res = await http.get(
      Uri.parse(url),
      headers: _headers(),
    );

    if (res.statusCode == 200) {
      final list = jsonDecode(res.body) as List;
      return list.cast<Map<String, dynamic>>();
    } else {
      throw Exception('Failed to fetch sync queue');
    }
  }
}

