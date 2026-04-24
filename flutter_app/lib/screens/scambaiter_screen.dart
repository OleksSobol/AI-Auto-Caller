import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';

class ScambaiterScreen extends StatefulWidget {
  const ScambaiterScreen({super.key});

  @override
  State<ScambaiterScreen> createState() => _ScambaiterScreenState();
}

class _ScambaiterScreenState extends State<ScambaiterScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabs;
  late ApiService _api;

  // Campaign settings
  String _mode = 'ai';
  String _persona = 'confused_grandma';
  String _musicTrack = 'never_gonna_give_you_up';
  bool _repeat = true;
  int _repeatDelay = 30;
  final _numberController = TextEditingController();
  final _categoryController = TextEditingController();

  // State
  bool _campaignRunning = false;
  Map<String, dynamic> _stats = {};
  List<dynamic> _personas = [];
  List<dynamic> _musicTracks = [];
  List<dynamic> _scamNumbers = [];

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 3, vsync: this);
    _api = Provider.of<ApiService>(context, listen: false);
    _loadData();
  }

  Future<void> _loadData() async {
    await Future.wait([_loadPersonas(), _loadNumbers(), _pollStatus()]);
  }

  Future<void> _loadPersonas() async {
    try {
      final data = await _api.getScambaiterPersonas();
      setState(() {
        _personas = data['personas'] ?? [];
        _musicTracks = data['music_tracks'] ?? [];
      });
    } catch (_) {}
  }

  Future<void> _loadNumbers() async {
    try {
      final data = await _api.getScamNumbers();
      setState(() => _scamNumbers = data['numbers'] ?? []);
    } catch (_) {}
  }

  Future<void> _pollStatus() async {
    try {
      final status = await _api.getScamCampaignStatus();
      setState(() {
        _campaignRunning = status['running'] == true;
        if (_campaignRunning) _stats = status;
      });
    } catch (_) {}
  }

  Future<void> _startCampaign() async {
    final number = _numberController.text.trim();
    if (number.isEmpty) {
      _snack('Enter a scam phone number first', error: true);
      return;
    }
    try {
      await _api.startScamCampaign(
        number: number,
        mode: _mode,
        personaId: _persona,
        musicTrack: _musicTrack,
        repeat: _repeat,
        repeatDelay: _repeatDelay,
      );
      setState(() => _campaignRunning = true);
      _snack('Campaign started on $number');
    } catch (e) {
      _snack('Failed: $e', error: true);
    }
  }

  Future<void> _stopCampaign() async {
    try {
      final result = await _api.stopScamCampaign();
      setState(() {
        _campaignRunning = false;
        _stats = result['stats'] ?? {};
      });
      _snack('Campaign stopped');
    } catch (e) {
      _snack('Failed: $e', error: true);
    }
  }

  Future<void> _addNumber() async {
    final num = _numberController.text.trim();
    final cat = _categoryController.text.trim().isEmpty
        ? 'other'
        : _categoryController.text.trim();
    if (num.isEmpty) return;
    try {
      await _api.addScamNumber(num, cat);
      await _loadNumbers();
      _numberController.clear();
      _snack('Number added');
    } catch (e) {
      _snack('Failed: $e', error: true);
    }
  }

  Future<void> _deleteNumber(String number) async {
    try {
      await _api.deleteScamNumber(number);
      await _loadNumbers();
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
        title: const Text('Scambaiter'),
        bottom: TabBar(
          controller: _tabs,
          tabs: const [
            Tab(icon: Icon(Icons.phone_forwarded), text: 'Campaign'),
            Tab(icon: Icon(Icons.list), text: 'Numbers'),
            Tab(icon: Icon(Icons.bar_chart), text: 'Stats'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabs,
        children: [_campaignTab(), _numbersTab(), _statsTab()],
      ),
    );
  }

  // ------------------------------------------------------------------ //
  // Campaign tab                                                         //
  // ------------------------------------------------------------------ //

  Widget _campaignTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Status banner
          _statusBanner(),
          const SizedBox(height: 16),

          // Target number
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Target Number',
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _numberController,
                    keyboardType: TextInputType.phone,
                    decoration: const InputDecoration(
                      prefixIcon: Icon(Icons.phone),
                      hintText: '+1 (555) 123-4567',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),

          // Mode selection
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Mode', style: Theme.of(context).textTheme.titleMedium),
                  Row(
                    children: [
                      Expanded(
                        child: RadioListTile<String>(
                          title: const Text('AI Persona'),
                          subtitle: const Text('Talks back'),
                          value: 'ai',
                          groupValue: _mode,
                          onChanged: (v) => setState(() => _mode = v!),
                        ),
                      ),
                      Expanded(
                        child: RadioListTile<String>(
                          title: const Text('Music Loop'),
                          subtitle: const Text('Plays audio'),
                          value: 'music',
                          groupValue: _mode,
                          onChanged: (v) => setState(() => _mode = v!),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),

          // AI persona picker (shown only in AI mode)
          if (_mode == 'ai') _personaPicker(),

          // Music picker (shown only in music mode)
          if (_mode == 'music') _musicPicker(),

          // Repeat settings
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Auto-Redial',
                      style: Theme.of(context).textTheme.titleMedium),
                  SwitchListTile(
                    title: const Text('Repeat after call ends'),
                    subtitle:
                        const Text('Keeps calling back if they hang up'),
                    value: _repeat,
                    onChanged: (v) => setState(() => _repeat = v),
                  ),
                  if (_repeat) ...[
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Text('Delay between redials: '),
                        Expanded(
                          child: Slider(
                            value: _repeatDelay.toDouble(),
                            min: 5,
                            max: 120,
                            divisions: 23,
                            label: '${_repeatDelay}s',
                            onChanged: (v) =>
                                setState(() => _repeatDelay = v.round()),
                          ),
                        ),
                        Text('${_repeatDelay}s'),
                      ],
                    ),
                  ]
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),

          // Start / Stop
          SizedBox(
            width: double.infinity,
            child: _campaignRunning
                ? ElevatedButton.icon(
                    icon: const Icon(Icons.stop),
                    label: const Text('Stop Campaign'),
                    style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.red,
                        padding: const EdgeInsets.all(16)),
                    onPressed: _stopCampaign,
                  )
                : ElevatedButton.icon(
                    icon: const Icon(Icons.play_arrow),
                    label: const Text('Start Campaign'),
                    style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green,
                        padding: const EdgeInsets.all(16)),
                    onPressed: _startCampaign,
                  ),
          ),
        ],
      ),
    );
  }

  Widget _statusBanner() {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
      decoration: BoxDecoration(
        color: _campaignRunning ? Colors.green.shade100 : Colors.grey.shade200,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: _campaignRunning ? Colors.green : Colors.grey,
        ),
      ),
      child: Row(
        children: [
          Icon(
            _campaignRunning ? Icons.sensors : Icons.sensors_off,
            color: _campaignRunning ? Colors.green : Colors.grey,
          ),
          const SizedBox(width: 12),
          Text(
            _campaignRunning ? 'Campaign ACTIVE' : 'Campaign IDLE',
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: _campaignRunning ? Colors.green.shade800 : Colors.grey,
            ),
          ),
          if (_campaignRunning) ...[
            const Spacer(),
            Text(
              '${_stats['calls_made'] ?? 0} calls',
              style: TextStyle(color: Colors.green.shade800),
            ),
          ]
        ],
      ),
    );
  }

  Widget _personaPicker() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('AI Persona',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            if (_personas.isEmpty)
              const Text('Loading personas...')
            else
              ..._personas.map((p) {
                return RadioListTile<String>(
                  title: Text(p['name']),
                  subtitle: Text(p['description'],
                      maxLines: 2, overflow: TextOverflow.ellipsis),
                  value: p['id'],
                  groupValue: _persona,
                  onChanged: (v) => setState(() => _persona = v!),
                );
              }).toList(),
          ],
        ),
      ),
    );
  }

  Widget _musicPicker() {
    final tracks = {
      'never_gonna_give_you_up': '🎵 Never Gonna Give You Up (Rickroll)',
      'hold_music': '🎶 Corporate Hold Music',
      'custom': '🎼 Custom Audio File',
    };
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Audio Track',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            ...tracks.entries.map((e) {
              return RadioListTile<String>(
                title: Text(e.value),
                value: e.key,
                groupValue: _musicTrack,
                onChanged: (v) => setState(() => _musicTrack = v!),
              );
            }).toList(),
            const Padding(
              padding: EdgeInsets.only(top: 8),
              child: Text(
                '⚠️  Drop MP3 files into python_backend/audio/ for music mode',
                style: TextStyle(fontSize: 12, color: Colors.orange),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ------------------------------------------------------------------ //
  // Numbers tab                                                          //
  // ------------------------------------------------------------------ //

  Widget _numbersTab() {
    return Column(
      children: [
        // Add number form
        Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _numberController,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: 'Scam number',
                    hintText: '+15551234567',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: _categoryController,
                  decoration: const InputDecoration(
                    labelText: 'Category',
                    hintText: 'tech_support',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              ElevatedButton(
                onPressed: _addNumber,
                child: const Text('Add'),
              ),
            ],
          ),
        ),

        // Number list
        Expanded(
          child: _scamNumbers.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.no_sim, size: 64, color: Colors.grey[400]),
                      const SizedBox(height: 12),
                      const Text('No scam numbers yet'),
                      const SizedBox(height: 4),
                      const Text(
                        'Add known scam numbers above',
                        style: TextStyle(color: Colors.grey),
                      ),
                    ],
                  ),
                )
              : ListView.builder(
                  itemCount: _scamNumbers.length,
                  itemBuilder: (_, i) {
                    final n = _scamNumbers[i];
                    return ListTile(
                      leading: const Icon(Icons.warning_amber,
                          color: Colors.orange),
                      title: Text(n['number'] ?? ''),
                      subtitle: Text(
                          '${n['category'] ?? ''} • ${n['notes'] ?? ''}'),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            icon: const Icon(Icons.phone_forwarded,
                                color: Colors.green),
                            tooltip: 'Use in campaign',
                            onPressed: () {
                              _numberController.text = n['number'];
                              _tabs.animateTo(0);
                            },
                          ),
                          IconButton(
                            icon: const Icon(Icons.delete, color: Colors.red),
                            onPressed: () => _deleteNumber(n['number']),
                          ),
                        ],
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }

  // ------------------------------------------------------------------ //
  // Stats tab                                                            //
  // ------------------------------------------------------------------ //

  Widget _statsTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          _statCard('Calls Made', '${_stats['calls_made'] ?? 0}',
              Icons.call, Colors.blue),
          _statCard(
            'Time Wasted',
            '${_stats['total_time_wasted_minutes'] ?? 0} min',
            Icons.timer,
            Colors.orange,
          ),
          _statCard(
            'Current Target',
            _stats['current_number'] ?? '—',
            Icons.gps_fixed,
            Colors.red,
          ),
          _statCard(
            'Mode',
            _stats['mode'] ?? '—',
            Icons.settings,
            Colors.purple,
          ),
          _statCard(
            'Persona',
            _stats['persona'] ?? '—',
            Icons.person,
            Colors.teal,
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            icon: const Icon(Icons.refresh),
            label: const Text('Refresh Stats'),
            onPressed: _pollStatus,
          ),
        ],
      ),
    );
  }

  Widget _statCard(String label, String value, IconData icon, Color color) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: color.withOpacity(0.15),
          child: Icon(icon, color: color),
        ),
        title: Text(label),
        trailing: Text(
          value,
          style: TextStyle(
              fontWeight: FontWeight.bold, fontSize: 16, color: color),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _tabs.dispose();
    _numberController.dispose();
    _categoryController.dispose();
    super.dispose();
  }
}
