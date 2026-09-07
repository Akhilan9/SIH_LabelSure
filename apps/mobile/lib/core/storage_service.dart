import '../models/inspection.dart';
import 'constants.dart';

class StorageService {
  static final StorageService _instance = StorageService._internal();
  factory StorageService() => _instance;
  StorageService._internal();

  // Persistent active officer session - launches app directly without login or server prompts
  String? _authToken = 'session_field_officer_active';
  UserModel? _currentUser = UserModel(
    id: 'usr_field_inspector_01',
    username: 'inspector1',
    fullName: 'Field Officer (Inspector)',
    email: 'inspector@labelsure.gov.in',
    role: 'INSPECTOR',
    badgeNumber: 'DL-LM-001',
  );
  String _baseUrl = AppConstants.defaultBaseUrl;

  final Map<String, Map<String, dynamic>> _draftInspections = {};
  final List<InspectionModel> _cachedInspections = [];

  // Auth State
  String? get authToken => _authToken;
  UserModel? get currentUser => _currentUser;
  String get baseUrl => _baseUrl;

  void setAuth(String token, UserModel user) {
    _authToken = token;
    _currentUser = user;
  }

  void clearAuth() {
    _authToken = null;
    _currentUser = null;
  }

  void setBaseUrl(String url) {
    if (url.endsWith('/')) {
      _baseUrl = url.substring(0, url.length - 1);
    } else {
      _baseUrl = url;
    }
  }

  // Draft Inspections Management
  void saveDraft(String draftId, Map<String, dynamic> draftData) {
    _draftInspections[draftId] = draftData;
  }

  Map<String, dynamic>? getDraft(String draftId) {
    return _draftInspections[draftId];
  }

  List<Map<String, dynamic>> getAllDrafts() {
    return _draftInspections.values.toList();
  }

  void deleteDraft(String draftId) {
    _draftInspections.remove(draftId);
  }

  // Inspection Cache
  void cacheInspections(List<InspectionModel> list) {
    _cachedInspections.clear();
    _cachedInspections.addAll(list);
  }

  List<InspectionModel> get cachedInspections => List.unmodifiable(_cachedInspections);

  List<InspectionModel> getCachedInspections() {
    return List.unmodifiable(_cachedInspections);
  }
}
