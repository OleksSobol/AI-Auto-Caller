import 'package:flutter/material.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:intl/intl.dart';
import '../services/api_service.dart';

class RecordingsScreen extends StatefulWidget {
  const RecordingsScreen({super.key});

  @override
  State<RecordingsScreen> createState() => _RecordingsScreenState();
}

class _RecordingsScreenState extends State<RecordingsScreen> {
  final _api = ApiService();
  final _player = AudioPlayer();
  List<dynamic> _recordings = [];
  bool _loading = true;
  String? _playingId;

  @override
  void initState() {
    super.initState();
    _load();
    _player.onPlayerComplete.listen((_) {
      setState(() => _playingId = null);
    });
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final data = await _api.getRecordings();
      setState(() => _recordings = data['recordings'] ?? []);
    } catch (e) {
      _snack('Failed to load recordings: $e', error: true);
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _play(Map<String, dynamic> rec) async {
    final id = rec['recording_id'];
    if (_playingId == id) {
      await _player.stop();
      setState(() => _playingId = null);
      return;
    }
    final url = '${_api.baseUrl}/api/recordings/$id/audio';
    await _player.play(UrlSource(url));
    setState(() => _playingId = id);
  }

  Future<void> _delete(String recordingId) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Delete Recording'),
        content: const Text('This cannot be undone.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirm != true) return;
    try {
      await _api.deleteRecording(recordingId);
      await _load();
    } catch (e) {
      _snack('Failed: $e', error: true);
    }
  }

  void _snack(String msg, {bool error = false}) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: error ? Colors.red : null,
    ));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Recordings'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _recordings.isEmpty
              ? _empty()
              : ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: _recordings.length,
                  itemBuilder: (_, i) => _tile(_recordings[i]),
                ),
    );
  }

  Widget _empty() => Center(
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Icon(Icons.mic_off, size: 64, color: Colors.grey[400]),
          const SizedBox(height: 12),
          const Text('No recordings yet'),
          const SizedBox(height: 4),
          Text('Answered calls are recorded automatically',
              style: TextStyle(color: Colors.grey[600])),
        ]),
      );

  Widget _tile(Map<String, dynamic> rec) {
    final id = rec['recording_id'] ?? '';
    final caller = rec['caller_number'] ?? 'Unknown';
    final direction = rec['direction'] ?? 'inbound';
    final secs = rec['duration_seconds'] ?? 0;
    final mins = secs ~/ 60;
    final s = secs % 60;
    final hasFile = rec['file_path'] != null;
    final isPlaying = _playingId == id;

    String timeStr = '';
    if (rec['start_time'] != null) {
      try {
        timeStr = DateFormat('MMM d, hh:mm a')
            .format(DateTime.parse(rec['start_time']));
      } catch (_) {}
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: direction == 'inbound'
              ? Colors.blue.shade100
              : Colors.orange.shade100,
          child: Icon(
            direction == 'inbound' ? Icons.call_received : Icons.call_made,
            color: direction == 'inbound' ? Colors.blue : Colors.orange,
          ),
        ),
        title: Text(caller, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text('$timeStr  •  ${mins}m ${s}s'),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (hasFile)
              IconButton(
                icon: Icon(isPlaying ? Icons.stop : Icons.play_arrow,
                    color: Theme.of(context).colorScheme.primary),
                onPressed: () => _play(rec),
              ),
            IconButton(
              icon: const Icon(Icons.delete_outline, color: Colors.red),
              onPressed: () => _delete(id),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }
}
