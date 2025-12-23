import 'package:flutter/foundation.dart';

class AppState extends ChangeNotifier {
  bool _autoAnswerEnabled = false;
  String _ttsEngine = 'gtts';
  bool _useAI = false;
  int _maxCallDuration = 300;
  List<Map<String, dynamic>> _activeCalls = [];
  List<Map<String, dynamic>> _callHistory = [];
  Map<String, dynamic> _responses = {};

  // Getters
  bool get autoAnswerEnabled => _autoAnswerEnabled;
  String get ttsEngine => _ttsEngine;
  bool get useAI => _useAI;
  int get maxCallDuration => _maxCallDuration;
  List<Map<String, dynamic>> get activeCalls => _activeCalls;
  List<Map<String, dynamic>> get callHistory => _callHistory;
  Map<String, dynamic> get responses => _responses;

  // Setters
  void setAutoAnswer(bool value) {
    _autoAnswerEnabled = value;
    notifyListeners();
  }

  void setTtsEngine(String engine) {
    _ttsEngine = engine;
    notifyListeners();
  }

  void setUseAI(bool value) {
    _useAI = value;
    notifyListeners();
  }

  void setMaxCallDuration(int duration) {
    _maxCallDuration = duration;
    notifyListeners();
  }

  void setActiveCalls(List<Map<String, dynamic>> calls) {
    _activeCalls = calls;
    notifyListeners();
  }

  void setCallHistory(List<Map<String, dynamic>> history) {
    _callHistory = history;
    notifyListeners();
  }

  void setResponses(Map<String, dynamic> responses) {
    _responses = responses;
    notifyListeners();
  }

  void addCall(Map<String, dynamic> call) {
    _activeCalls.add(call);
    notifyListeners();
  }

  void removeCall(String callId) {
    _activeCalls.removeWhere((call) => call['call_id'] == callId);
    notifyListeners();
  }

  void addToHistory(Map<String, dynamic> call) {
    _callHistory.insert(0, call);
    notifyListeners();
  }
}
