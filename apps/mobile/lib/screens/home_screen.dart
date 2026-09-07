import 'package:flutter/material.dart';
import '../core/api_service.dart';
import '../core/constants.dart';
import '../core/storage_service.dart';
import '../core/sync_manager.dart';
import '../models/inspection.dart';
import 'new_inspection_screen.dart';
import 'camera_screen.dart';
import 'history_screen.dart';
import 'settings_screen.dart';
import 'findings_screen.dart';

class MobileHomeScreen extends StatefulWidget {
  const MobileHomeScreen({Key? key}) : super(key: key);

  @override
  _MobileHomeScreenState createState() => _MobileHomeScreenState();
}

class _MobileHomeScreenState extends State<MobileHomeScreen> {
  List<InspectionModel> _inspections = [];
  bool _isLoading = true;
  int _draftCount = 0;

  @override
  void initState() {
    super.initState();
    _loadDashboard();
    SyncManager().addListener(_onSyncUpdated);
  }

  @override
  void dispose() {
    SyncManager().removeListener(_onSyncUpdated);
    super.dispose();
  }

  void _onSyncUpdated() {
    if (mounted) setState(() {});
  }

  Future<void> _loadDashboard() async {
    setState(() {
      _isLoading = true;
      _draftCount = StorageService().getAllDrafts().length;
    });

    final user = StorageService().currentUser;
    final isOffline = !SyncManager().isOnline ||
        user?.badgeNumber == 'DL-LM-OFFLINE' ||
        user?.id == 'usr_offline_demo';

    if (isOffline) {
      // In offline mode, immediately populate from local cache
      setState(() {
        _inspections = StorageService().cachedInspections;
        _isLoading = false;
      });
      return;
    }

    try {
      final list = await ApiService().listInspections();
      setState(() {
        _inspections = list;
        _isLoading = false;
      });
    } catch (_) {
      final cached = StorageService().cachedInspections;
      setState(() {
        _inspections = cached;
        _isLoading = false;
      });
    }
  }

  Future<void> _startInstantCameraScan() async {
    final user = StorageService().currentUser;
    final isOffline = !SyncManager().isOnline ||
        user?.badgeNumber == 'DL-LM-OFFLINE' ||
        user?.id == 'usr_offline_demo';

    final now = DateTime.now();
    final timeStr = '${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}';

    if (isOffline) {
      // Instant 0ms local offline launch - zero waiting!
      _launchOfflineCameraScan(timeStr);
      return;
    }

    // If online, show dismissible progress dialog with 2.5-second timeout fallback
    bool dialogShowing = true;
    showDialog(
      context: context,
      barrierDismissible: true,
      builder: (ctx) => Center(
        child: Card(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const CircularProgressIndicator(),
                const SizedBox(height: 16),
                const Text(
                  'Launching Camera Scanner...',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                ),
                const SizedBox(height: 12),
                TextButton.icon(
                  onPressed: () {
                    dialogShowing = false;
                    Navigator.pop(ctx);
                    _launchOfflineCameraScan(timeStr);
                  },
                  icon: const Icon(Icons.flash_on, size: 16),
                  label: const Text('Launch Offline Scanner Immediately'),
                ),
              ],
            ),
          ),
        ),
      ),
    ).then((_) {
      dialogShowing = false;
    });

    try {
      final inspection = await ApiService().createInspection({
        'commodity_name': 'Scanned Label ($timeStr)',
        'rule_version': 'LMPC-2026-RULES',
        'notes': 'Created via Direct AI Camera Scan',
        'context': {
          'commodity_category': 'FOOD',
          'is_food': true,
          'origin_country': 'India',
        }
      }).timeout(const Duration(milliseconds: 2500));

      if (dialogShowing && mounted) {
        dialogShowing = false;
        Navigator.pop(context); // dismiss dialog
      }

      if (!mounted) return;
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => CameraScreen(
            inspectionId: inspection.id,
            inspectionNumber: inspection.inspectionNumber,
          ),
        ),
      ).then((_) => _loadDashboard());
    } catch (e) {
      // If server unreachable, timed out or socket failure, auto-fallback to offline scanner
      if (dialogShowing && mounted) {
        dialogShowing = false;
        Navigator.pop(context); // dismiss dialog
      }

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('⚡ Server unreachable. Launching camera scanner in Offline Field Mode.'),
          backgroundColor: Colors.blueGrey,
          duration: Duration(seconds: 2),
        ),
      );
      _launchOfflineCameraScan(timeStr);
    }
  }

  void _launchOfflineCameraScan(String timeStr) {
    final offlineInsp = SyncManager().createOfflineInspection(
      commodityName: 'Scanned Label ($timeStr)',
      notes: 'Created via Direct AI Camera Scan (Offline Mode)',
      initialContext: {
        'commodity_category': 'FOOD',
        'is_food': true,
        'origin_country': 'India',
      },
    );

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => CameraScreen(
          inspectionId: offlineInsp.localId,
          inspectionNumber: 'OFFLINE-${offlineInsp.localId.substring(0, 8).toUpperCase()}',
        ),
      ),
    ).then((_) => _loadDashboard());
  }

  @override
  Widget build(BuildContext context) {
    final user = StorageService().currentUser;
    final compliantCount = _inspections.where((i) => i.complianceStatus == 'COMPLIANT').length;
    final nonCompliantCount = _inspections.where((i) => i.complianceStatus == 'NON_COMPLIANT').length;
    final reviewCount = _inspections.where((i) => i.complianceStatus == 'REQUIRES_REVIEW').length;

    return Scaffold(
      appBar: AppBar(
        title: const Text('APEX LabelSure Inspector'),
        backgroundColor: AppColors.darkBg,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadDashboard,
          ),
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            onPressed: () {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const SettingsScreen()))
                  .then((_) => _loadDashboard());
            },
          ),
        ],
      ),
      backgroundColor: AppColors.background,
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _startInstantCameraScan,
        backgroundColor: AppColors.primary,
        icon: const Icon(Icons.camera_alt, color: Colors.white),
        label: const Text('Direct Scan', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
      ),
      body: RefreshIndicator(
        onRefresh: _loadDashboard,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Officer Identity Card
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF0F172A), Color(0xFF1E293B)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(14),
                  boxShadow: [
                    BoxShadow(color: Colors.black.withOpacity(0.06), blurRadius: 8, offset: const Offset(0, 3)),
                  ],
                ),
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 22,
                      backgroundColor: AppColors.primary,
                      child: Text(
                        user?.fullName.isNotEmpty == true ? user!.fullName[0] : 'I',
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            user?.fullName ?? 'Field Inspector',
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
                          ),
                          Text(
                            'Badge: ${user?.badgeNumber ?? "DL-LM-001"} | ${user?.role ?? "INSPECTOR"}',
                            style: const TextStyle(color: Colors.white70, fontSize: 11),
                          ),
                        ],
                      ),
                    ),
                    InkWell(
                      onTap: () {
                        final current = SyncManager().isOnline;
                        SyncManager().setManualOnlineOverride(!current);
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text(
                              !current
                                  ? 'Online engine enabled. Auto-synchronizing...'
                                  : 'Offline mode simulated. Operations will be queued locally.',
                            ),
                            duration: const Duration(seconds: 2),
                          ),
                        );
                      },
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: SyncManager().isOnline
                              ? const Color(0xFF10B981).withOpacity(0.2)
                              : Colors.orange.withOpacity(0.25),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(
                            color: SyncManager().isOnline ? const Color(0xFF10B981) : Colors.orange,
                          ),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              Icons.circle,
                              color: SyncManager().isOnline ? const Color(0xFF10B981) : Colors.orange,
                              size: 8,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              SyncManager().isOnline ? 'ONLINE' : 'OFFLINE',
                              style: TextStyle(
                                color: SyncManager().isOnline ? const Color(0xFF10B981) : Colors.orange,
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),

              // Offline Sync Queue Banner (8 States Engine)
              if (SyncManager().queuedInspections.isNotEmpty || SyncManager().isSyncing) ...[
                InkWell(
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const HistoryScreen(initialTab: 1)),
                    ).then((_) => _loadDashboard());
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: SyncManager().queuedInspections.any((i) => i.status == SyncState.syncFailed)
                            ? [const Color(0xFFFEF2F2), const Color(0xFFFEE2E2)]
                            : [const Color(0xFFEFF6FF), const Color(0xFFDBEAFE)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: SyncManager().queuedInspections.any((i) => i.status == SyncState.syncFailed)
                            ? const Color(0xFFFCA5A5)
                            : const Color(0xFF93C5FD),
                      ),
                    ),
                    child: Row(
                      children: [
                        SyncManager().isSyncing
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary),
                              )
                            : Icon(
                                SyncManager().queuedInspections.any((i) => i.status == SyncState.syncFailed)
                                    ? Icons.warning_amber_rounded
                                    : Icons.cloud_sync,
                                color: SyncManager().queuedInspections.any((i) => i.status == SyncState.syncFailed)
                                    ? AppColors.failRed
                                    : AppColors.primary,
                                size: 22,
                              ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                SyncManager().isSyncing
                                    ? 'Synchronizing offline inspections...'
                                    : SyncManager().queuedInspections.any((i) => i.status == SyncState.syncFailed)
                                        ? '${SyncManager().queuedInspections.where((i) => i.status == SyncState.syncFailed).length} sync operation(s) failed'
                                        : '${SyncManager().queuedInspections.length} inspection(s) queued for sync',
                                style: TextStyle(
                                  color: SyncManager().queuedInspections.any((i) => i.status == SyncState.syncFailed)
                                      ? AppColors.failRed
                                      : const Color(0xFF1E40AF),
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              Text(
                                SyncManager().isOnline ? 'Tap to view queue or sync now' : 'Will sync automatically when reconnected',
                                style: const TextStyle(fontSize: 10, color: AppColors.textMuted),
                              ),
                            ],
                          ),
                        ),
                        if (SyncManager().isOnline && !SyncManager().isSyncing)
                          ElevatedButton(
                            onPressed: () => SyncManager().synchronizePending(),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.primary,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              textStyle: const TextStyle(fontSize: 11),
                            ),
                            child: const Text('Sync Now'),
                          ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 12),
              ],

              // Local Drafts Banner if present
              if (_draftCount > 0) ...[
                InkWell(
                  onTap: () {
                    Navigator.push(context, MaterialPageRoute(builder: (_) => const HistoryScreen(initialTab: 2)))
                        .then((_) => _loadDashboard());
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: AppColors.uncertainBg,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: AppColors.uncertainBorder),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.drafts, color: AppColors.uncertainAmber, size: 20),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            '$_draftCount offline inspection draft(s) stored locally.',
                            style: const TextStyle(color: Color(0xFF92400E), fontSize: 12, fontWeight: FontWeight.bold),
                          ),
                        ),
                        const Text('Resume ->', style: TextStyle(color: AppColors.uncertainAmber, fontSize: 12, fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
                ),
                  const SizedBox(height: 16),
                ],

              // Direct AI Camera Scan (Direct Field Audit)
              InkWell(
                onTap: _startInstantCameraScan,
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF2563EB), Color(0xFF1D4ED8)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(14),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF2563EB).withOpacity(0.35),
                        blurRadius: 10,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(Icons.qr_code_scanner, color: Colors.white, size: 28),
                      ),
                      const SizedBox(width: 14),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Direct Camera Scan',
                              style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                            ),
                            SizedBox(height: 3),
                            Text(
                              'Point & shoot package label — AI auto-detects product, brand & declarations',
                              style: TextStyle(color: Colors.white70, fontSize: 11),
                            ),
                          ],
                        ),
                      ),
                      const Icon(Icons.arrow_forward_ios, color: Colors.white70, size: 16),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Quick Actions Grid
              Row(
                children: [
                  Expanded(
                    child: _buildActionTile(
                      icon: Icons.add_circle,
                      title: 'New Inspection',
                      subtitle: 'Initiate packaging case',
                      color: AppColors.primary,
                      onTap: () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const NewInspectionScreen()))
                            .then((_) => _loadDashboard());
                      },
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildActionTile(
                      icon: Icons.history,
                      title: 'Cases & Drafts',
                      subtitle: 'View inspection log',
                      color: const Color(0xFF0F172A),
                      onTap: () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const HistoryScreen()))
                            .then((_) => _loadDashboard());
                      },
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // Compliance Stats Row
              Row(
                children: [
                  _buildMetricPill('Compliant', '$compliantCount', AppColors.passGreen, AppColors.passBg),
                  const SizedBox(width: 8),
                  _buildMetricPill('Violations', '$nonCompliantCount', AppColors.failRed, AppColors.failBg),
                  const SizedBox(width: 8),
                  _buildMetricPill('Review', '$reviewCount', AppColors.uncertainAmber, AppColors.uncertainBg),
                ],
              ),
              const SizedBox(height: 20),

              // Recent Inspections Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Recent Statutory Inspections', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                  TextButton(
                    onPressed: () {
                      Navigator.push(context, MaterialPageRoute(builder: (_) => const HistoryScreen()))
                          .then((_) => _loadDashboard());
                    },
                    child: const Text('View All', style: TextStyle(fontSize: 12)),
                  ),
                ],
              ),
              const SizedBox(height: 8),

              // List of Recent Inspections
              if (_isLoading)
                const Center(child: Padding(padding: EdgeInsets.all(32), child: CircularProgressIndicator()))
              else if (_inspections.isEmpty)
                Container(
                  padding: const EdgeInsets.all(32),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: const Center(
                    child: Text('No field inspections logged yet. Tap "New Inspection" above to begin.', textAlign: TextAlign.center),
                  ),
                )
              else
                ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: _inspections.take(5).length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (ctx, idx) {
                    final item = _inspections[idx];
                    return InkWell(
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => FindingsScreen(
                              inspectionId: item.id,
                              inspectionNumber: item.inspectionNumber,
                            ),
                          ),
                        );
                      },
                      child: Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: AppColors.border),
                        ),
                        child: Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(item.inspectionNumber, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppColors.primary)),
                                  const SizedBox(height: 2),
                                  Text(
                                    '${item.commodityName} ${item.brandName != null ? "(${item.brandName})" : ""}',
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                  ),
                                  const SizedBox(height: 2),
                                  Text('Rule Baseline: ${item.ruleVersion}', style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
                                ],
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: item.complianceStatus == 'COMPLIANT'
                                    ? AppColors.passBg
                                    : item.complianceStatus == 'NON_COMPLIANT'
                                        ? AppColors.failBg
                                        : AppColors.uncertainBg,
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: Text(
                                item.complianceStatus,
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                  color: item.complianceStatus == 'COMPLIANT'
                                      ? AppColors.passGreen
                                      : item.complianceStatus == 'NON_COMPLIANT'
                                          ? AppColors.failRed
                                          : AppColors.uncertainAmber,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildActionTile({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color, size: 28),
            const SizedBox(height: 10),
            Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
            const SizedBox(height: 2),
            Text(subtitle, style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricPill(String label, String value, Color textCol, Color bgCol) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
        decoration: BoxDecoration(color: bgCol, borderRadius: BorderRadius.circular(8)),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(value, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: textCol)),
            Text(label, style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: textCol)),
          ],
        ),
      ),
    );
  }
}
