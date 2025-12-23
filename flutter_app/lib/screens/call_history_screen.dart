import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../providers/app_state.dart';
import '../services/api_service.dart';

class CallHistoryScreen extends StatefulWidget {
  const CallHistoryScreen({super.key});

  @override
  State<CallHistoryScreen> createState() => _CallHistoryScreenState();
}

class _CallHistoryScreenState extends State<CallHistoryScreen> {
  late ApiService _apiService;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _apiService = Provider.of<ApiService>(context, listen: false);
    _loadCallHistory();
  }

  Future<void> _loadCallHistory() async {
    setState(() => _isLoading = true);
    try {
      final history = await _apiService.getCallHistory(limit: 50);
      Provider.of<AppState>(context, listen: false).setCallHistory(history);
    } catch (e) {
      _showError('Failed to load call history: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Call History'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadCallHistory,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Consumer<AppState>(
              builder: (context, appState, child) {
                if (appState.callHistory.isEmpty) {
                  return _buildEmptyState();
                }
                return _buildCallList(appState.callHistory);
              },
            ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.history,
            size: 64,
            color: Colors.grey[400],
          ),
          const SizedBox(height: 16),
          Text(
            'No call history yet',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          Text(
            'Answered calls will appear here',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Colors.grey[600],
                ),
          ),
        ],
      ),
    );
  }

  Widget _buildCallList(List<Map<String, dynamic>> calls) {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: calls.length,
      itemBuilder: (context, index) {
        final call = calls[index];
        return _buildCallCard(call);
      },
    );
  }

  Widget _buildCallCard(Map<String, dynamic> call) {
    final callerNumber = call['caller_number'] ?? 'Unknown';
    final startTime = call['start_time'];
    final duration = call['duration'] ?? 0.0;
    final messageCount = (call['messages'] as List?)?.length ?? 0;

    String formattedTime = 'Unknown time';
    if (startTime != null) {
      try {
        final dateTime = DateTime.parse(startTime);
        formattedTime = DateFormat('MMM dd, yyyy - hh:mm a').format(dateTime);
      } catch (e) {
        // Keep default
      }
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ExpansionTile(
        leading: const CircleAvatar(
          child: Icon(Icons.phone),
        ),
        title: Text(callerNumber),
        subtitle: Text(formattedTime),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              _formatDuration(duration),
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            Text(
              '$messageCount messages',
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[600],
              ),
            ),
          ],
        ),
        children: [
          _buildCallDetails(call),
        ],
      ),
    );
  }

  Widget _buildCallDetails(Map<String, dynamic> call) {
    final messages = call['messages'] as List? ?? [];

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.3),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Call Info
          _buildInfoRow('Call ID', call['call_id'] ?? 'N/A'),
          _buildInfoRow('Status', call['status'] ?? 'N/A'),
          _buildInfoRow('Duration', _formatDuration(call['duration'] ?? 0.0)),

          if (messages.isNotEmpty) ...[
            const SizedBox(height: 16),
            Text(
              'Conversation:',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 8),
            ...messages.map((msg) => _buildMessageBubble(msg)).toList(),
          ],
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
          Text(value),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(Map<String, dynamic> message) {
    final role = message['role'] ?? 'unknown';
    final content = message['content'] ?? '';
    final isUser = role == 'user';

    return Align(
      alignment: isUser ? Alignment.centerLeft : Alignment.centerRight,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: isUser
              ? Colors.grey[300]
              : Theme.of(context).colorScheme.primary,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              role.toUpperCase(),
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.bold,
                color: isUser ? Colors.black54 : Colors.white70,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              content,
              style: TextStyle(
                color: isUser ? Colors.black87 : Colors.white,
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatDuration(double seconds) {
    final duration = Duration(seconds: seconds.round());
    final minutes = duration.inMinutes;
    final secs = duration.inSeconds % 60;
    return '${minutes}m ${secs}s';
  }
}
