import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/api_service.dart';
import '../services/call_service.dart';
import 'responses_screen.dart';
import 'settings_screen.dart';
import 'call_history_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late CallService _callService;
  late ApiService _apiService;
  bool _isInitialized = false;

  @override
  void initState() {
    super.initState();
    _initializeServices();
  }

  Future<void> _initializeServices() async {
    _callService = Provider.of<CallService>(context, listen: false);
    _apiService = Provider.of<ApiService>(context, listen: false);

    try {
      // Initialize call service
      await _callService.initialize();

      // Register callbacks
      _callService.registerIncomingCallCallback(_handleIncomingCall);
      _callService.registerCallEndedCallback(_handleCallEnded);

      // Load settings
      await _loadSettings();

      setState(() {
        _isInitialized = true;
      });
    } catch (e) {
      print('Initialization error: $e');
      _showError('Failed to initialize: $e');
    }
  }

  Future<void> _loadSettings() async {
    try {
      final settings = await _apiService.getSettings();
      final appState = Provider.of<AppState>(context, listen: false);

      appState.setAutoAnswer(settings['auto_answer_enabled'] ?? false);
      appState.setTtsEngine(settings['tts_engine'] ?? 'gtts');
      appState.setUseAI(settings['use_ai'] ?? false);
      appState.setMaxCallDuration(settings['max_call_duration'] ?? 300);

      // Load responses
      final responses = await _apiService.getResponses();
      appState.setResponses(responses);
    } catch (e) {
      print('Error loading settings: $e');
    }
  }

  void _handleIncomingCall(String phoneNumber) async {
    final appState = Provider.of<AppState>(context, listen: false);

    if (appState.autoAnswerEnabled) {
      try {
        // Auto-answer the call
        final result = await _apiService.answerCall(phoneNumber);

        if (result['status'] == 'answered') {
          appState.addCall({
            'call_id': result['call_id'],
            'caller_number': phoneNumber,
            'start_time': DateTime.now().toIso8601String(),
          });

          _showNotification('Call auto-answered from $phoneNumber');
        }
      } catch (e) {
        _showError('Failed to answer call: $e');
      }
    }
  }

  void _handleCallEnded(String phoneNumber) async {
    final appState = Provider.of<AppState>(context, listen: false);

    // Find and remove active call
    final activeCalls = appState.activeCalls;
    for (var call in activeCalls) {
      if (call['caller_number'] == phoneNumber) {
        try {
          await _apiService.endCall(call['call_id']);
          appState.removeCall(call['call_id']);
          appState.addToHistory(call);
        } catch (e) {
          print('Error ending call: $e');
        }
        break;
      }
    }
  }

  void _showNotification(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Auto Caller'),
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const CallHistoryScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const SettingsScreen()),
              );
            },
          ),
        ],
      ),
      body: _isInitialized
          ? _buildMainContent()
          : const Center(child: CircularProgressIndicator()),
    );
  }

  Widget _buildMainContent() {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        return SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Auto-Answer Toggle
              _buildAutoAnswerCard(appState),
              const SizedBox(height: 16),

              // Status Card
              _buildStatusCard(appState),
              const SizedBox(height: 16),

              // Active Calls
              if (appState.activeCalls.isNotEmpty) ...[
                _buildActiveCallsCard(appState),
                const SizedBox(height: 16),
              ],

              // Quick Actions
              _buildQuickActions(),
            ],
          ),
        );
      },
    );
  }

  Widget _buildAutoAnswerCard(AppState appState) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(
              appState.autoAnswerEnabled ? Icons.phone_enabled : Icons.phone_disabled,
              size: 48,
              color: appState.autoAnswerEnabled ? Colors.green : Colors.grey,
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Auto-Answer',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  Text(
                    appState.autoAnswerEnabled ? 'Enabled' : 'Disabled',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ],
              ),
            ),
            Switch(
              value: appState.autoAnswerEnabled,
              onChanged: (value) async {
                try {
                  await _apiService.toggleAutoAnswer(value);
                  appState.setAutoAnswer(value);
                } catch (e) {
                  _showError('Failed to toggle auto-answer: $e');
                }
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusCard(AppState appState) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Status',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            _buildStatusRow('TTS Engine', appState.ttsEngine.toUpperCase()),
            _buildStatusRow('AI Enabled', appState.useAI ? 'Yes' : 'No'),
            _buildStatusRow(
              'Max Call Duration',
              '${appState.maxCallDuration} seconds',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _buildActiveCallsCard(AppState appState) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Active Calls (${appState.activeCalls.length})',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            ...appState.activeCalls.map((call) {
              return ListTile(
                leading: const Icon(Icons.phone_in_talk, color: Colors.green),
                title: Text(call['caller_number'] ?? 'Unknown'),
                subtitle: Text('Call ID: ${call['call_id']}'),
                trailing: IconButton(
                  icon: const Icon(Icons.call_end, color: Colors.red),
                  onPressed: () async {
                    try {
                      await _apiService.endCall(call['call_id']);
                      appState.removeCall(call['call_id']);
                    } catch (e) {
                      _showError('Failed to end call: $e');
                    }
                  },
                ),
              );
            }).toList(),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickActions() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Quick Actions',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 12),
        GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: 2,
          mainAxisSpacing: 12,
          crossAxisSpacing: 12,
          childAspectRatio: 1.5,
          children: [
            _buildActionCard(
              'Manage Responses',
              Icons.chat_bubble,
              () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const ResponsesScreen()),
                );
              },
            ),
            _buildActionCard(
              'View History',
              Icons.history,
              () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const CallHistoryScreen()),
                );
              },
            ),
            _buildActionCard(
              'Settings',
              Icons.settings,
              () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const SettingsScreen()),
                );
              },
            ),
            _buildActionCard(
              'Test TTS',
              Icons.volume_up,
              () async {
                try {
                  await _apiService.generateTTS('Hello, this is a test');
                  _showNotification('TTS test successful');
                } catch (e) {
                  _showError('TTS test failed: $e');
                }
              },
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildActionCard(String title, IconData icon, VoidCallback onTap) {
    return Card(
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 32),
              const SizedBox(height: 8),
              Text(
                title,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 12),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _callService.dispose();
    super.dispose();
  }
}
