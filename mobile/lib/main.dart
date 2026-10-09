import 'package:flutter/material.dart';
import 'api.dart';
import 'app.dart';
import 'session_store.dart';
export 'app.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  const origin = String.fromEnvironment('MBOLO_API_ORIGIN');
  MboloApi? api;
  try {
    api = MboloApi(
      origin,
      sessionStore: EncryptedSessionStore(),
    );
  } on FormatException {
    /* Fail closed. */
  }
  runApp(MboloApp(api: api));
}
