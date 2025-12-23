import 'package:phone_state/phone_state.dart';
import 'package:permission_handler/permission_handler.dart';
import 'dart:async';

class CallService {
  PhoneState? _phoneState;
  StreamSubscription<PhoneState>? _phoneStateSubscription;
  Function(String)? onIncomingCall;
  Function(String)? onCallEnded;

  // Initialize call monitoring
  Future<void> initialize() async {
    // Check permissions
    final hasPermission = await _checkPermissions();
    if (!hasPermission) {
      throw Exception('Phone permissions not granted');
    }

    // Listen to phone state changes
    _phoneStateSubscription = PhoneState.stream.listen(
      (phoneState) {
        _phoneState = phoneState;
        _handlePhoneStateChange(phoneState);
      },
      onError: (error) {
        print('Phone state error: $error');
      },
    );
  }

  Future<bool> _checkPermissions() async {
    // Request phone permission
    final phoneStatus = await Permission.phone.status;
    if (!phoneStatus.isGranted) {
      final result = await Permission.phone.request();
      return result.isGranted;
    }
    return true;
  }

  void _handlePhoneStateChange(PhoneState phoneState) {
    switch (phoneState.status) {
      case PhoneStateStatus.CALL_INCOMING:
        // Incoming call detected
        final phoneNumber = phoneState.number ?? 'Unknown';
        print('Incoming call from: $phoneNumber');
        if (onIncomingCall != null) {
          onIncomingCall!(phoneNumber);
        }
        break;

      case PhoneStateStatus.CALL_STARTED:
        // Call answered
        print('Call started');
        break;

      case PhoneStateStatus.CALL_ENDED:
        // Call ended
        print('Call ended');
        if (onCallEnded != null) {
          onCallEnded!(_phoneState?.number ?? 'Unknown');
        }
        break;

      default:
        break;
    }
  }

  // Register callback for incoming calls
  void registerIncomingCallCallback(Function(String) callback) {
    onIncomingCall = callback;
  }

  // Register callback for call ended
  void registerCallEndedCallback(Function(String) callback) {
    onCallEnded = callback;
  }

  // Get current phone state
  PhoneState? getCurrentState() {
    return _phoneState;
  }

  // Clean up
  void dispose() {
    _phoneStateSubscription?.cancel();
  }
}
