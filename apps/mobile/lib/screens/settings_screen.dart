import 'package:flutter/material.dart';
import '../core/api_service.dart';
import '../core/constants.dart';
import '../core/storage_service.dart';
import 'login_screen.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({Key? key}) : super(key: key);

  @override
  _SettingsScreenState createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _urlController;
  final StorageService _storage = StorageService();
  bool _isTesting = false;
  String? _testResult;
  bool? _testSuccess;

  @override
  void initState() {
    super.initState();
    _urlController = TextEditingController(text: _storage.baseUrl);
  }

  void _saveUrl() {
    final text = _urlController.text.trim();
    if (text.isNotEmpty) {
      _storage.setBaseUrl(text);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Server endpoint updated to: ${_storage.baseUrl}')),
      );
    }
  }

  Future<void> _testConnection() async {
    _saveUrl();
    setState(() {
      _isTesting = true;
      _testResult = null;
      _testSuccess = null;
    });

    final stopwatch = Stopwatch()..start();
    final ok = await ApiService().checkHealth();
    stopwatch.stop();

    if (!mounted) return;
    setState(() {
      _isTesting = false;
      _testSuccess = ok;
      _testResult = ok
          ? 'Connected successfully (${stopwatch.elapsedMilliseconds}ms)'
          : 'Could not connect to ${_storage.baseUrl}. Ensure PC is on same WiFi and server is running.';
    });
  }

  void _handleLogout() {
    _storage.clearAuth();
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (_) => const LoginScreen()),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    final user = _storage.currentUser;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Inspector Settings & Diagnostics'),
        backgroundColor: AppColors.darkBg,
        foregroundColor: Colors.white,
      ),
      backgroundColor: AppColors.background,
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Officer Profile Card
          if (user != null) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.border),
              ),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 24,
                    backgroundColor: AppColors.primaryLight,
                    child: Text(
                      user.fullName.isNotEmpty ? user.fullName[0] : 'I',
                      style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(user.fullName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                        Text('Role: ${user.role} | Badge: ${user.badgeNumber ?? "N/A"}', style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
                        Text(user.email, style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],

          // Backend API Server Configuration
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
                const Text('FastAPI Central Server Endpoint', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 6),
                const Text(
                  'Android Emulator: http://10.0.2.2:8000\nDesktop / Web: http://127.0.0.1:8000\nPhysical Mobile Device: http://<LAN-IP>:8000',
                  style: TextStyle(fontSize: 11, color: AppColors.textMuted),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _urlController,
                  decoration: InputDecoration(
                    labelText: 'Server Base URL',
                    prefixIcon: const Icon(Icons.cloud_outlined, size: 20),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  ),
                ),
                const SizedBox(height: 10),
                Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  children: [
                    ActionChip(
                      avatar: const Icon(Icons.cloud_done, size: 14, color: Colors.green),
                      label: const Text('Live AI Cloud (labelsure-ai.loca.lt)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                      onPressed: () {
                        setState(() {
                          _urlController.text = 'https://labelsure-ai.loca.lt';
                          _storage.setBaseUrl('https://labelsure-ai.loca.lt');
                        });
                      },
                    ),
                    ActionChip(
                      avatar: const Icon(Icons.wifi, size: 14),
                      label: const Text('PC WiFi (192.168.0.219)', style: TextStyle(fontSize: 11)),
                      onPressed: () {
                        setState(() {
                          _urlController.text = 'http://192.168.0.219:8000';
                          _storage.setBaseUrl('http://192.168.0.219:8000');
                        });
                      },
                    ),
                    ActionChip(
                      avatar: const Icon(Icons.phone_android, size: 14),
                      label: const Text('Emulator (10.0.2.2)', style: TextStyle(fontSize: 11)),
                      onPressed: () {
                        setState(() {
                          _urlController.text = 'http://10.0.2.2:8000';
                          _storage.setBaseUrl('http://10.0.2.2:8000');
                        });
                      },
                    ),
                    ActionChip(
                      avatar: const Icon(Icons.computer, size: 14),
                      label: const Text('Localhost (127.0.0.1)', style: TextStyle(fontSize: 11)),
                      onPressed: () {
                        setState(() {
                          _urlController.text = AppConstants.desktopBaseUrl;
                          _storage.setBaseUrl(AppConstants.desktopBaseUrl);
                        });
                      },
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    ElevatedButton(
                      onPressed: _saveUrl,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      ),
                      child: const Text('Save URL'),
                    ),
                    const SizedBox(width: 8),
                    OutlinedButton.icon(
                      onPressed: _isTesting ? null : _testConnection,
                      icon: _isTesting
                          ? const SizedBox(width: 12, height: 12, child: CircularProgressIndicator(strokeWidth: 2))
                          : const Icon(Icons.network_check, size: 16),
                      label: Text(_isTesting ? 'Testing...' : 'Test Connection', style: const TextStyle(fontSize: 12)),
                    ),
                  ],
                ),
                if (_testResult != null) ...[
                  const SizedBox(height: 10),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: _testSuccess == true ? AppColors.passBg : AppColors.failBg,
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(
                        color: _testSuccess == true ? AppColors.passBorder : AppColors.failBorder,
                      ),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          _testSuccess == true ? Icons.check_circle : Icons.error_outline,
                          size: 16,
                          color: _testSuccess == true ? AppColors.passGreen : AppColors.failRed,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            _testResult!,
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: _testSuccess == true ? AppColors.passGreen : AppColors.failRed,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Local Drafts & Diagnostics Card
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
                const Text('Local Inspection Drafts', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 6),
                Text(
                  'Active Local Drafts: ${_storage.getAllDrafts().length}',
                  style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
                ),
                const SizedBox(height: 10),
                ElevatedButton.icon(
                  onPressed: () {
                    for (var draft in _storage.getAllDrafts()) {
                      _storage.deleteDraft(draft['id'] ?? '');
                    }
                    setState(() {});
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Local drafts cache cleared.')),
                    );
                  },
                  icon: const Icon(Icons.delete_outline, size: 16),
                  label: const Text('Clear All Local Drafts'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFFEE2E2),
                    foregroundColor: AppColors.failRed,
                    elevation: 0,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Sign Out Button
          if (user != null)
            ElevatedButton.icon(
              onPressed: _handleLogout,
              icon: const Icon(Icons.logout, size: 18),
              label: const Text('Sign Out of Terminal'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.darkBg,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
            ),
        ],
      ),
    );
  }
}
