import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';

class AppColors {
  // Brand Palette
  static const Color primary = Color(0xFF2563EB);
  static const Color primaryDark = Color(0xFF1D4ED8);
  static const Color primaryLight = Color(0xFFEFF6FF);
  
  static const Color background = Color(0xFFF8FAFC);
  static const Color cardBg = Colors.white;
  static const Color darkBg = Color(0xFF0F172A);
  static const Color darkCard = Color(0xFF1E293B);

  // Text Colors
  static const Color textMain = Color(0xFF0F172A);
  static const Color textMuted = Color(0xFF64748B);
  static const Color textLight = Color(0xFF94A3B8);

  // Compliance Status Colors
  static const Color passGreen = Color(0xFF16A34A);
  static const Color passBg = Color(0xFFDCFCE7);
  static const Color passBorder = Color(0xFF86EFAC);

  static const Color failRed = Color(0xFFDC2626);
  static const Color failBg = Color(0xFFFEE2E2);
  static const Color failBorder = Color(0xFFFCA5A5);

  static const Color uncertainAmber = Color(0xFFD97706);
  static const Color uncertainBg = Color(0xFFFEF3C7);
  static const Color uncertainBorder = Color(0xFFFCD34D);

  static const Color naSlate = Color(0xFF475569);
  static const Color naBg = Color(0xFFF1F5F9);
  static const Color naBorder = Color(0xFFCBD5E1);

  // Borders
  static const Color border = Color(0xFFE2E8F0);
}

class AppConstants {
  static const String appName = 'APEX LabelSure';
  static const String appTagline = 'Legal Metrology Compliance Inspector';
  
  // Default Backend URL
  // 192.168.0.219 is PC LAN IP for physical Android phone, 127.0.0.1 for web and desktop
  static String get defaultBaseUrl => kIsWeb ? 'http://127.0.0.1:8000' : 'http://192.168.0.219:8000';
  static const String desktopBaseUrl = 'http://127.0.0.1:8000';
  static const String lanBaseUrl = 'http://192.168.0.219:8000';
  static const String emulatorBaseUrl = 'http://10.0.2.2:8000';
}
