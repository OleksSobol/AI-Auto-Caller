import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/api_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late ApiService _apiService;

  @override
  void initState() {
    super.initState();
    _apiService = Provider.of<ApiService>(context, listen: false);
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  void _showSuccess(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.green),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: Consumer<AppState>(
        builder: (context, appState, child) {
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Auto-Answer Settings
              _buildSection('Auto-Answer', [
                SwitchListTile(
                  title: const Text('Enable Auto-Answer'),
                  subtitle: const Text('Automatically answer incoming calls'),
                  value: appState.autoAnswerEnabled,
                  onChanged: (value) async {
                    try {
                      await _apiService.toggleAutoAnswer(value);
                      appState.setAutoAnswer(value);
                      _showSuccess('Auto-answer ${value ? 'enabled' : 'disabled'}');
                    } catch (e) {
                      _showError('Failed to update: $e');
                    }
                  },
                ),
              ]),

              const SizedBox(height: 16),

              // TTS Settings
              _buildSection('Text-to-Speech', [
                ListTile(
                  title: const Text('TTS Engine'),
                  subtitle: Text(appState.ttsEngine.toUpperCase()),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => _showTTSEngineDialog(appState),
                ),
              ]),

              const SizedBox(height: 16),

              // AI Settings
              _buildSection('AI Configuration', [
                SwitchListTile(
                  title: const Text('Use AI Responses'),
                  subtitle: const Text('Enable dynamic AI-powered responses'),
                  value: appState.useAI,
                  onChanged: (value) async {
                    try {
                      await _apiService.updateSettings({'use_ai': value});
                      appState.setUseAI(value);
                      _showSuccess('AI ${value ? 'enabled' : 'disabled'}');
                    } catch (e) {
                      _showError('Failed to update: $e');
                    }
                  },
                ),
              ]),

              const SizedBox(height: 16),

              // Call Settings
              _buildSection('Call Settings', [
                ListTile(
                  title: const Text('Max Call Duration'),
                  subtitle: Text('${appState.maxCallDuration} seconds'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => _showDurationDialog(appState),
                ),
              ]),

              const SizedBox(height: 16),

              // About
              _buildSection('About', [
                ListTile(
                  title: const Text('Version'),
                  subtitle: const Text('1.0.0'),
                ),
                ListTile(
                  title: const Text('Backend URL'),
                  subtitle: Text(_apiService.baseUrl),
                ),
              ]),

              const SizedBox(height: 24),

              // Test Buttons
              _buildTestSection(),
            ],
          );
        },
      ),
    );
  }

  Widget _buildSection(String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 16, bottom: 8),
          child: Text(
            title,
            style: Theme.of(context).textTheme.titleMedium,
          ),
        ),
        Card(
          child: Column(children: children),
        ),
      ],
    );
  }

  Widget _buildTestSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 16, bottom: 8),
          child: Text(
            'Test & Debug',
            style: Theme.of(context).textTheme.titleMedium,
          ),
        ),
        Card(
          child: Column(
            children: [
              ListTile(
                leading: const Icon(Icons.volume_up),
                title: const Text('Test TTS'),
                subtitle: const Text('Play sample text-to-speech'),
                onTap: () async {
                  try {
                    await _apiService.generateTTS(
                      'Hello! This is a test of the text to speech system.',
                    );
                    _showSuccess('TTS test completed');
                  } catch (e) {
                    _showError('TTS test failed: $e');
                  }
                },
              ),
              ListTile(
                leading: const Icon(Icons.health_and_safety),
                title: const Text('Health Check'),
                subtitle: const Text('Check backend connection'),
                onTap: () async {
                  try {
                    final settings = await _apiService.getSettings();
                    _showSuccess('Backend is healthy');
                    print('Settings: $settings');
                  } catch (e) {
                    _showError('Backend connection failed: $e');
                  }
                },
              ),
            ],
          ),
        ),
      ],
    );
  }

  void _showTTSEngineDialog(AppState appState) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Select TTS Engine'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              RadioListTile<String>(
                title: const Text('gTTS (Free)'),
                subtitle: const Text('Google Text-to-Speech'),
                value: 'gtts',
                groupValue: appState.ttsEngine,
                onChanged: (value) {
                  Navigator.pop(context, value);
                },
              ),
              RadioListTile<String>(
                title: const Text('ElevenLabs (Premium)'),
                subtitle: const Text('High-quality voices'),
                value: 'elevenlabs',
                groupValue: appState.ttsEngine,
                onChanged: (value) {
                  Navigator.pop(context, value);
                },
              ),
              RadioListTile<String>(
                title: const Text('pyttsx3 (Offline)'),
                subtitle: const Text('No internet required'),
                value: 'pyttsx3',
                groupValue: appState.ttsEngine,
                onChanged: (value) {
                  Navigator.pop(context, value);
                },
              ),
            ],
          ),
        );
      },
    ).then((value) async {
      if (value != null) {
        try {
          await _apiService.updateSettings({'tts_engine': value});
          appState.setTtsEngine(value);
          _showSuccess('TTS engine updated to ${value.toUpperCase()}');
        } catch (e) {
          _showError('Failed to update TTS engine: $e');
        }
      }
    });
  }

  void _showDurationDialog(AppState appState) {
    final controller = TextEditingController(
      text: appState.maxCallDuration.toString(),
    );

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Max Call Duration'),
          content: TextField(
            controller: controller,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              labelText: 'Seconds',
              border: OutlineInputBorder(),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                final duration = int.tryParse(controller.text);
                if (duration != null && duration > 0) {
                  try {
                    await _apiService.updateSettings({
                      'max_call_duration': duration,
                    });
                    appState.setMaxCallDuration(duration);
                    Navigator.pop(context);
                    _showSuccess('Duration updated');
                  } catch (e) {
                    _showError('Failed to update: $e');
                  }
                }
              },
              child: const Text('Save'),
            ),
          ],
        );
      },
    );
  }
}
