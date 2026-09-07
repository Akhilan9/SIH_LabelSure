import 'package:flutter/material.dart';
import '../core/api_service.dart';
import '../core/constants.dart';
import '../core/storage_service.dart';
import '../core/sync_manager.dart';
import '../models/inspection.dart';
import 'findings_screen.dart';
import 'new_inspection_screen.dart';

class HistoryScreen extends StatefulWidget {
  final int initialTab;

  const HistoryScreen({Key? key, this.initialTab = 0}) : super(key: key);

  @override
  _HistoryScreenState createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<InspectionModel> _serverInspections = [];
  List<Map<String, dynamic>> _localDrafts = [];
  bool _isLoading = true;
  String? _error;
  String _statusFilter = 'ALL';

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this, initialIndex: widget.initialTab);
    _loadAllData();
    SyncManager().addListener(_onSyncManagerUpdated);
  }

  @override
  void dispose() {
    SyncManager().removeListener(_onSyncManagerUpdated);
    _tabController.dispose();
    super.dispose();
  }

  void _onSyncManagerUpdated() {
    if (mounted) setState(() {});
  }

  Future<void> _loadAllData() async {
    setState(() {
      _isLoading = true;
      _error = null;
      _localDrafts = StorageService().getAllDrafts();
    });

    try {
      final list = await ApiService().listInspections();
      setState(() {
        _serverInspections = list;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString().replaceAll('Exception: ', '');
        _isLoading = false;
      });
    }
  }

  void _deleteDraft(String draftId) {
    StorageService().deleteDraft(draftId);
    setState(() {
      _localDrafts = StorageService().getAllDrafts();
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Draft deleted.')),
    );
  }

  void _resumeDraft(Map<String, dynamic> draft) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => NewInspectionScreen(initialDraft: draft),
      ),
    ).then((_) => _loadAllData());
  }

  Color _getSyncStateColor(String state) {
    switch (state) {
      case SyncState.queued:
        return const Color(0xFF3B82F6); // Blue
      case SyncState.uploading:
        return const Color(0xFF6366F1); // Indigo
      case SyncState.analyzing:
        return const Color(0xFF8B5CF6); // Purple
      case SyncState.reviewRequired:
        return const Color(0xFFF59E0B); // Amber
      case SyncState.synced:
      case SyncState.finalized:
        return const Color(0xFF10B981); // Green
      case SyncState.syncFailed:
        return const Color(0xFFEF4444); // Red
      case SyncState.draft:
      default:
        return const Color(0xFF6B7280); // Gray
    }
  }

  @override
  Widget build(BuildContext context) {
    var filtered = _serverInspections;
    if (_statusFilter != 'ALL') {
      filtered = filtered.where((i) => i.complianceStatus == _statusFilter).toList();
    }

    final syncQueue = SyncManager().allInspections;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Inspections & Offline Sync Queue'),
        backgroundColor: AppColors.darkBg,
        foregroundColor: Colors.white,
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppColors.primary,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white60,
          tabs: [
            Tab(text: 'Server (${_serverInspections.length})'),
            Tab(text: 'Sync Queue (${syncQueue.length})'),
            Tab(text: 'Drafts (${_localDrafts.length})'),
          ],
        ),
      ),
      backgroundColor: AppColors.background,
      body: TabBarView(
        controller: _tabController,
        children: [
          // Tab 1: Server Inspections
          _isLoading
              ? const Center(child: CircularProgressIndicator())
              : _error != null
                  ? Center(child: Text(_error!, style: const TextStyle(color: AppColors.failRed)))
                  : Column(
                      children: [
                        // Filter Chips
                        Container(
                          color: Colors.white,
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                          child: SingleChildScrollView(
                            scrollDirection: Axis.horizontal,
                            child: Row(
                              children: [
                                _buildFilterChip('ALL', 'All Cases'),
                                _buildFilterChip('COMPLIANT', 'Compliant'),
                                _buildFilterChip('NON_COMPLIANT', 'Non-Compliant'),
                                _buildFilterChip('REQUIRES_REVIEW', 'Requires Review'),
                              ],
                            ),
                          ),
                        ),

                        // List View
                        Expanded(
                          child: filtered.isEmpty
                              ? const Center(child: Text('No inspections matching filter.'))
                              : ListView.separated(
                                  padding: const EdgeInsets.all(16),
                                  itemCount: filtered.length,
                                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                                  itemBuilder: (ctx, idx) {
                                    final item = filtered[idx];
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
                                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                          children: [
                                            Expanded(
                                              child: Column(
                                                crossAxisAlignment: CrossAxisAlignment.start,
                                                children: [
                                                  Text(item.inspectionNumber, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.primary)),
                                                  const SizedBox(height: 2),
                                                  Text(
                                                    '${item.commodityName} ${item.brandName != null ? "(${item.brandName})" : ""}',
                                                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                                                  ),
                                                  const SizedBox(height: 2),
                                                  Text('Status: ${item.status} | Images: ${item.totalImages}', style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
                                                ],
                                              ),
                                            ),
                                            const Icon(Icons.chevron_right, color: AppColors.textLight),
                                          ],
                                        ),
                                      ),
                                    );
                                  },
                                ),
                        ),
                      ],
                    ),

          // Tab 2: Offline Sync Queue (8 States Engine)
          Column(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                color: Colors.white,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        Icon(
                          SyncManager().isOnline ? Icons.cloud_done : Icons.cloud_off,
                          color: SyncManager().isOnline ? const Color(0xFF10B981) : Colors.orange,
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          SyncManager().isOnline ? 'Online Engine Active' : 'Offline Mode (Local Storage)',
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),
                    Row(
                      children: [
                        if (SyncManager().queuedInspections.isNotEmpty)
                          ElevatedButton.icon(
                            onPressed: SyncManager().isSyncing
                                ? null
                                : () => SyncManager().synchronizePending(),
                            icon: SyncManager().isSyncing
                                ? const SizedBox(width: 12, height: 12, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                                : const Icon(Icons.sync, size: 14),
                            label: Text(SyncManager().isSyncing ? 'Syncing...' : 'Sync All'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.primary,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                              textStyle: const TextStyle(fontSize: 11),
                            ),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
              Expanded(
                child: syncQueue.isEmpty
                    ? const Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.check_circle_outline, size: 48, color: Colors.grey),
                            SizedBox(height: 10),
                            Text('Sync queue is clean. All local operations synchronized.', style: TextStyle(color: Colors.grey)),
                          ],
                        ),
                      )
                    : ListView.separated(
                        padding: const EdgeInsets.all(16),
                        itemCount: syncQueue.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 12),
                        itemBuilder: (ctx, idx) {
                          final item = syncQueue[idx];
                          final badgeColor = _getSyncStateColor(item.status);

                          return Container(
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(color: AppColors.border),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Expanded(
                                      child: Text(
                                        item.commodityName,
                                        style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                                      ),
                                    ),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                      decoration: BoxDecoration(
                                        color: badgeColor.withOpacity(0.12),
                                        borderRadius: BorderRadius.circular(6),
                                        border: Border.all(color: badgeColor),
                                      ),
                                      child: Text(
                                        item.status,
                                        style: TextStyle(color: badgeColor, fontSize: 10, fontWeight: FontWeight.bold),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                if (item.brandName != null)
                                  Text('Brand: ${item.brandName}', style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
                                Text('Idempotency Key: ${item.idempotencyKey.substring(0, 13)}...', style: const TextStyle(fontSize: 10, color: Colors.grey)),
                                Text('Photos attached: ${item.images.length} panels', style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
                                if (item.serverId != null)
                                  Text('Server Ref: ${item.inspectionNumber ?? item.serverId}', style: const TextStyle(fontSize: 11, color: AppColors.primary, fontWeight: FontWeight.w600)),
                                
                                if (item.syncError != null) ...[
                                  const SizedBox(height: 8),
                                  Container(
                                    padding: const EdgeInsets.all(8),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFFFEF2F2),
                                      borderRadius: BorderRadius.circular(6),
                                      border: Border.all(color: const Color(0xFFFCA5A5)),
                                    ),
                                    child: Row(
                                      children: [
                                        const Icon(Icons.error_outline, size: 14, color: AppColors.failRed),
                                        const SizedBox(width: 6),
                                        Expanded(
                                          child: Text(
                                            'Error: ${item.syncError}',
                                            style: const TextStyle(color: AppColors.failRed, fontSize: 10),
                                          ),
                                        ),
                                        IconButton(
                                          icon: const Icon(Icons.refresh, size: 16, color: AppColors.primary),
                                          onPressed: () => SyncManager().retryOperation(item.localId),
                                          tooltip: 'Retry Sync',
                                        ),
                                      ],
                                    ),
                                  ),
                                ],

                                const SizedBox(height: 8),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.end,
                                  children: [
                                    if (item.status == SyncState.syncFailed)
                                      TextButton.icon(
                                        onPressed: () => SyncManager().retryOperation(item.localId),
                                        icon: const Icon(Icons.refresh, size: 14),
                                        label: const Text('Retry', style: TextStyle(fontSize: 11)),
                                      ),
                                    if (item.status == SyncState.queued && !SyncManager().isSyncing)
                                      TextButton.icon(
                                        onPressed: () => SyncManager().synchronizePending(),
                                        icon: const Icon(Icons.cloud_upload, size: 14),
                                        label: const Text('Sync Now', style: TextStyle(fontSize: 11)),
                                      ),
                                    if (item.serverId != null)
                                      TextButton.icon(
                                        onPressed: () {
                                          Navigator.push(
                                            context,
                                            MaterialPageRoute(
                                              builder: (_) => FindingsScreen(
                                                inspectionId: item.serverId!,
                                                inspectionNumber: item.inspectionNumber ?? item.serverId!,
                                              ),
                                            ),
                                          );
                                        },
                                        icon: const Icon(Icons.visibility, size: 14),
                                        label: const Text('View Findings', style: TextStyle(fontSize: 11)),
                                      ),
                                    IconButton(
                                      icon: const Icon(Icons.delete_outline, size: 16, color: Colors.grey),
                                      onPressed: () => SyncManager().deleteInspection(item.localId),
                                      tooltip: 'Remove from Queue',
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          );
                        },
                      ),
              ),
            ],
          ),

          // Tab 3: Local Offline Drafts
          _localDrafts.isEmpty
              ? const Center(child: Text('No local drafts saved.'))
              : ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: _localDrafts.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (ctx, idx) {
                    final d = _localDrafts[idx];
                    return Container(
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
                                Text(
                                  d['commodity_name'] ?? 'Untitled Draft',
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                ),
                                if (d['brand_name'] != null && d['brand_name'].isNotEmpty)
                                  Text('Brand: ${d['brand_name']}', style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
                                if (d['saved_at'] != null)
                                  Text('Saved: ${d['saved_at']}', style: const TextStyle(fontSize: 10, color: Colors.grey)),
                              ],
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.edit, color: AppColors.primary, size: 20),
                            onPressed: () => _resumeDraft(d),
                          ),
                          IconButton(
                            icon: const Icon(Icons.delete_outline, color: AppColors.failRed, size: 20),
                            onPressed: () => _deleteDraft(d['id']),
                          ),
                        ],
                      ),
                    );
                  },
                ),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String status, String label) {
    final isSelected = _statusFilter == status;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: FilterChip(
        label: Text(label),
        selected: isSelected,
        selectedColor: AppColors.primary.withOpacity(0.15),
        checkmarkColor: AppColors.primary,
        labelStyle: TextStyle(
          color: isSelected ? AppColors.primary : AppColors.textMuted,
          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
          fontSize: 12,
        ),
        onSelected: (val) {
          setState(() => _statusFilter = status);
        },
      ),
    );
  }
}
