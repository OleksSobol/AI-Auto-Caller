import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

/// Handles FCM token registration with the backend.
/// Add firebase_messaging to pubspec.yaml and call initialize() in main()
/// once you have your google-services.json file configured.
class NotificationService {
  static final NotificationService _instance = NotificationService._();
  factory NotificationService() => _instance;
  NotificationService._();

  final _api = ApiService();

  Future<void> initialize() async {
    try {
      // If firebase_messaging is installed, uncomment:
      // final messaging = FirebaseMessaging.instance;
      // await messaging.requestPermission();
      // final token = await messaging.getToken();
      // if (token != null) await _registerToken(token);
      // messaging.onTokenRefresh.listen(_registerToken);
      // FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
      debugPrint('[Notifications] FCM not yet configured. '
          'Add google-services.json + firebase_messaging to enable.');
    } catch (e) {
      debugPrint('[Notifications] Init error: $e');
    }
  }

  Future<void> _registerToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString('fcm_token');
    if (saved == token) return;   // already registered
    await _api.registerFcmToken(token);
    await prefs.setString('fcm_token', token);
    debugPrint('[Notifications] Token registered');
  }

  // void _handleForegroundMessage(RemoteMessage message) {
  //   debugPrint('[Notifications] ${message.notification?.title}');
  // }
}
