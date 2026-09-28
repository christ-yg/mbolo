import 'package:flutter/material.dart';
import 'api.dart';
import 'app.dart';
export 'app.dart';

void main() {
  const origin = String.fromEnvironment('MBOLO_API_ORIGIN');
  MboloApi? api;
  try {
    api = MboloApi(origin);
  } on FormatException {
    /* Fail closed. */
  }
  runApp(MboloApp(api: api));
}
