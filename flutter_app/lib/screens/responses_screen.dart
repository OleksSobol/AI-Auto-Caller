import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/api_service.dart';

class ResponsesScreen extends StatefulWidget {
  const ResponsesScreen({super.key});

  @override
  State<ResponsesScreen> createState() => _ResponsesScreenState();
}

class _ResponsesScreenState extends State<ResponsesScreen> {
  late ApiService _apiService;
  final _formKey = GlobalKey<FormState>();
  final _responseController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _apiService = Provider.of<ApiService>(context, listen: false);
    _loadResponses();
  }

  Future<void> _loadResponses() async {
    try {
      final responses = await _apiService.getResponses();
      Provider.of<AppState>(context, listen: false).setResponses(responses);
    } catch (e) {
      _showError('Failed to load responses: $e');
    }
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
        title: const Text('Manage Responses'),
      ),
      body: Consumer<AppState>(
        builder: (context, appState, child) {
          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Predefined Responses
                _buildSection('Predefined Responses', [
                  _buildResponseTile(
                    'Greeting',
                    appState.responses['greeting'] ?? '',
                    'greeting',
                  ),
                  _buildResponseTile(
                    'Unavailable',
                    appState.responses['unavailable'] ?? '',
                    'unavailable',
                  ),
                  _buildResponseTile(
                    'Business Hours',
                    appState.responses['business_hours'] ?? '',
                    'business_hours',
                  ),
                  _buildResponseTile(
                    'Goodbye',
                    appState.responses['goodbye'] ?? '',
                    'goodbye',
                  ),
                ]),

                const SizedBox(height: 24),

                // Context-Based Responses
                _buildSection('Context Responses', [
                  if (appState.responses['context_responses'] != null)
                    ...appState.responses['context_responses'].entries.map((entry) {
                      return _buildResponseTile(
                        entry.key,
                        entry.value,
                        'context_responses.${entry.key}',
                      );
                    }).toList(),
                ]),

                const SizedBox(height: 24),

                // Custom Responses
                _buildCustomResponses(appState),
              ],
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showAddResponseDialog,
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildSection(String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 12),
        ...children,
      ],
    );
  }

  Widget _buildResponseTile(String title, String response, String category) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        title: Text(title),
        subtitle: Text(
          response,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
        trailing: IconButton(
          icon: const Icon(Icons.edit),
          onPressed: () => _showEditDialog(title, response, category),
        ),
      ),
    );
  }

  Widget _buildCustomResponses(AppState appState) {
    final customResponses = appState.responses['custom_responses'];

    if (customResponses == null || customResponses.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text(
            'No custom responses yet. Tap + to add one.',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Custom Responses',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 12),
        ...List.generate(customResponses.length, (index) {
          return Card(
            margin: const EdgeInsets.only(bottom: 8),
            child: ListTile(
              title: Text(customResponses[index]),
              trailing: IconButton(
                icon: const Icon(Icons.delete, color: Colors.red),
                onPressed: () => _deleteCustomResponse(index),
              ),
            ),
          );
        }),
      ],
    );
  }

  void _showEditDialog(String title, String currentText, String category) {
    final controller = TextEditingController(text: currentText);

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text('Edit $title'),
          content: TextField(
            controller: controller,
            maxLines: 3,
            decoration: const InputDecoration(
              hintText: 'Enter response text',
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
                final newText = controller.text.trim();
                if (newText.isNotEmpty) {
                  try {
                    await _apiService.updateResponse(category, newText);
                    await _loadResponses();
                    Navigator.pop(context);
                    _showSuccess('Response updated');
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

  void _showAddResponseDialog() {
    _responseController.clear();

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Add Custom Response'),
          content: Form(
            key: _formKey,
            child: TextFormField(
              controller: _responseController,
              maxLines: 3,
              decoration: const InputDecoration(
                hintText: 'Enter response text',
                border: OutlineInputBorder(),
              ),
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Please enter a response';
                }
                return null;
              },
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                if (_formKey.currentState!.validate()) {
                  try {
                    await _apiService.addResponse(_responseController.text.trim());
                    await _loadResponses();
                    Navigator.pop(context);
                    _showSuccess('Response added');
                  } catch (e) {
                    _showError('Failed to add response: $e');
                  }
                }
              },
              child: const Text('Add'),
            ),
          ],
        );
      },
    );
  }

  void _deleteCustomResponse(int index) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Delete Response'),
          content: const Text('Are you sure you want to delete this response?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () {
                // TODO: Implement delete API endpoint
                Navigator.pop(context);
                _showSuccess('Response deleted');
              },
              style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
              child: const Text('Delete'),
            ),
          ],
        );
      },
    );
  }

  @override
  void dispose() {
    _responseController.dispose();
    super.dispose();
  }
}
