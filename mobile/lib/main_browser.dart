import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import 'api.dart';
import 'app.dart';

/// Connected browser entry point. Serve beside /api/v1/ on the same HTTPS origin.
/// No configurable remote origin: Django cookies remain managed by the browser.
void main() {
  WidgetsFlutterBinding.ensureInitialized();
  MboloApi? api;
  if (kIsWeb) {
    try {
      api = MboloApi(Uri.base.origin, browserSession: true);
    } on FormatException {
      // Fail closed when the page is not served through HTTPS.
    }
  }
  runApp(MboloApp(api: api));
}
