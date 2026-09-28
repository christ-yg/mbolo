import 'package:flutter/material.dart';
import 'app.dart';
import 'demo_api.dart';

void main() {
  runApp(MboloApp(api: DemoApi(), demo: true));
}
