import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // Change this to your backend URL
  final String baseUrl = 'http://localhost:8000';

  // Answer incoming call
  Future<Map<String, dynamic>> answerCall(String callerNumber, {String? callId}) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/answer-call'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'caller_number': callerNumber,
          if (callId != null) 'call_id': callId,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to answer call: ${response.body}');
      }
    } catch (e) {
      throw Exception('Error answering call: $e');
    }
  }

  // Process user speech
  Future<Map<String, dynamic>> processSpeech(String callId, String text) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/process-speech'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'call_id': callId,
          'text': text,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to process speech: ${response.body}');
      }
    } catch (e) {
      throw Exception('Error processing speech: $e');
    }
  }

  // End call
  Future<Map<String, dynamic>> endCall(String callId) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/end-call/$callId'),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to end call: ${response.body}');
      }
    } catch (e) {
      throw Exception('Error ending call: $e');
    }
  }

  // Get active calls
  Future<List<Map<String, dynamic>>> getActiveCalls() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/active-calls'),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return List<Map<String, dynamic>>.from(data['active_calls']);
      } else {
        throw Exception('Failed to get active calls');
      }
    } catch (e) {
      throw Exception('Error getting active calls: $e');
    }
  }

  // Get call history
  Future<List<Map<String, dynamic>>> getCallHistory({int limit = 10}) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/call-history?limit=$limit'),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return List<Map<String, dynamic>>.from(data['history']);
      } else {
        throw Exception('Failed to get call history');
      }
    } catch (e) {
      throw Exception('Error getting call history: $e');
    }
  }

  // Get responses
  Future<Map<String, dynamic>> getResponses() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/responses'),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to get responses');
      }
    } catch (e) {
      throw Exception('Error getting responses: $e');
    }
  }

  // Add custom response
  Future<void> addResponse(String responseText) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/responses?response_text=$responseText'),
      );

      if (response.statusCode != 200) {
        throw Exception('Failed to add response');
      }
    } catch (e) {
      throw Exception('Error adding response: $e');
    }
  }

  // Update response
  Future<void> updateResponse(String category, String text) async {
    try {
      final response = await http.put(
        Uri.parse('$baseUrl/api/responses'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'category': category,
          'text': text,
        }),
      );

      if (response.statusCode != 200) {
        throw Exception('Failed to update response');
      }
    } catch (e) {
      throw Exception('Error updating response: $e');
    }
  }

  // Update settings
  Future<void> updateSettings(Map<String, dynamic> settings) async {
    try {
      final response = await http.put(
        Uri.parse('$baseUrl/api/settings'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(settings),
      );

      if (response.statusCode != 200) {
        throw Exception('Failed to update settings');
      }
    } catch (e) {
      throw Exception('Error updating settings: $e');
    }
  }

  // Toggle auto-answer
  Future<void> toggleAutoAnswer(bool enabled) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/settings/auto-answer?enabled=$enabled'),
      );

      if (response.statusCode != 200) {
        throw Exception('Failed to toggle auto-answer');
      }
    } catch (e) {
      throw Exception('Error toggling auto-answer: $e');
    }
  }

  // Get settings
  Future<Map<String, dynamic>> getSettings() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/settings'),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to get settings');
      }
    } catch (e) {
      throw Exception('Error getting settings: $e');
    }
  }

  // Generate TTS
  Future<String> generateTTS(String text, {String engine = 'gtts'}) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/tts'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'text': text,
          'engine': engine,
        }),
      );

      if (response.statusCode == 200) {
        return '$baseUrl/api/tts';
      } else {
        throw Exception('Failed to generate TTS');
      }
    } catch (e) {
      throw Exception('Error generating TTS: $e');
    }
  }

  // ------------------------------------------------------------------ //
  // Scambaiter API                                                       //
  // ------------------------------------------------------------------ //

  Future<Map<String, dynamic>> getScambaiterPersonas() async {
    final r = await http.get(Uri.parse('$baseUrl/api/scambaiter/personas'));
    if (r.statusCode == 200) return jsonDecode(r.body);
    throw Exception('Failed to load personas');
  }

  Future<Map<String, dynamic>> getScamNumbers() async {
    final r = await http.get(Uri.parse('$baseUrl/api/scambaiter/numbers'));
    if (r.statusCode == 200) return jsonDecode(r.body);
    throw Exception('Failed to load scam numbers');
  }

  Future<void> addScamNumber(String number, String category) async {
    final r = await http.post(
      Uri.parse('$baseUrl/api/scambaiter/numbers'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'number': number, 'category': category, 'notes': ''}),
    );
    if (r.statusCode != 200) throw Exception('Failed to add number');
  }

  Future<void> deleteScamNumber(String number) async {
    final encoded = Uri.encodeComponent(number);
    final r = await http.delete(
        Uri.parse('$baseUrl/api/scambaiter/numbers/$encoded'));
    if (r.statusCode != 200) throw Exception('Failed to delete number');
  }

  Future<Map<String, dynamic>> startScamCampaign({
    required String number,
    required String mode,
    required String personaId,
    required String musicTrack,
    required bool repeat,
    required int repeatDelay,
  }) async {
    final r = await http.post(
      Uri.parse('$baseUrl/api/scambaiter/start'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'number': number,
        'mode': mode,
        'persona_id': personaId,
        'music_track': musicTrack,
        'repeat': repeat,
        'repeat_delay': repeatDelay,
      }),
    );
    if (r.statusCode == 200) return jsonDecode(r.body);
    throw Exception('Failed to start campaign: ${r.body}');
  }

  Future<Map<String, dynamic>> stopScamCampaign() async {
    final r = await http.post(Uri.parse('$baseUrl/api/scambaiter/stop'));
    if (r.statusCode == 200) return jsonDecode(r.body);
    throw Exception('Failed to stop campaign');
  }

  Future<Map<String, dynamic>> getScamCampaignStatus() async {
    final r = await http.get(Uri.parse('$baseUrl/api/scambaiter/status'));
    if (r.statusCode == 200) return jsonDecode(r.body);
    throw Exception('Failed to get status');
  }
}
