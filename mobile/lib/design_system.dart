import 'package:flutter/material.dart';

/// Shared visual language for the native MBOLO experience.
///
/// Colors are defined explicitly instead of relying on generated Material
/// tones so light and dark modes remain predictable and WCAG-friendly.
abstract final class MboloColors {
  static const midnight = Color(0xFF0D080C);
  static const blackPlum = Color(0xFF160C13);
  static const deepGraphite = Color(0xFF211820);
  static const plumSurface = Color(0xFF251620);
  static const plumRaised = Color(0xFF2E1B28);
  static const ivory = Color(0xFFFFF8FB);
  static const white = Color(0xFFFFFFFF);
  static const ink = Color(0xFF21131C);
  static const mutedInk = Color(0xFF6D5864);
  static const powderedRose = Color(0xFFF0A7C1);
  static const romance = Color(0xFF9D315E);
  static const romanceBright = Color(0xFFF086AD);
  static const champagne = Color(0xFFECCB96);
  static const success = Color(0xFF68C99B);
}

abstract final class MboloSpace {
  static const xs = 4.0;
  static const sm = 8.0;
  static const md = 12.0;
  static const lg = 16.0;
  static const xl = 24.0;
  static const xxl = 32.0;
}

abstract final class MboloRadius {
  static const control = 16.0;
  static const card = 28.0;
  static const hero = 36.0;
}

abstract final class MboloMotion {
  static const fast = Duration(milliseconds: 160);
  static const standard = Duration(milliseconds: 240);
  static const emphasized = Duration(milliseconds: 340);
  static const spring = Curves.easeOutBack;
}

abstract final class MboloTheme {
  static final ThemeData light = _build(Brightness.light);
  static final ThemeData dark = _build(Brightness.dark);

  static ThemeData _build(Brightness brightness) {
    final isDark = brightness == Brightness.dark;
    final base = ThemeData(useMaterial3: true, brightness: brightness);
    final scheme = ColorScheme(
      brightness: brightness,
      primary: isDark ? MboloColors.romanceBright : MboloColors.romance,
      onPrimary: isDark ? MboloColors.blackPlum : MboloColors.white,
      primaryContainer: isDark
          ? const Color(0xFF4A2438)
          : const Color(0xFFFBE5ED),
      onPrimaryContainer: isDark
          ? const Color(0xFFFFD8E6)
          : const Color(0xFF501128),
      secondary: isDark ? MboloColors.champagne : const Color(0xFFA86F2A),
      onSecondary: isDark ? MboloColors.blackPlum : MboloColors.white,
      secondaryContainer: isDark
          ? const Color(0xFF3A2A1B)
          : const Color(0xFFFFEED3),
      onSecondaryContainer: isDark
          ? const Color(0xFFFFE3B6)
          : const Color(0xFF472A00),
      tertiary: MboloColors.success,
      onTertiary: MboloColors.blackPlum,
      tertiaryContainer: isDark
          ? const Color(0xFF153A2A)
          : const Color(0xFFDCF8EA),
      onTertiaryContainer: isDark
          ? const Color(0xFFB9F1D4)
          : const Color(0xFF0A3A25),
      error: isDark ? const Color(0xFFFFB4AB) : const Color(0xFFBA1A1A),
      onError: isDark ? const Color(0xFF690005) : MboloColors.white,
      errorContainer: isDark
          ? const Color(0xFF5E2025)
          : const Color(0xFFFFDAD6),
      onErrorContainer: isDark
          ? const Color(0xFFFFDAD6)
          : const Color(0xFF410002),
      surface: isDark ? MboloColors.plumSurface : MboloColors.white,
      onSurface: isDark ? MboloColors.ivory : MboloColors.ink,
      onSurfaceVariant: isDark
          ? const Color(0xFFD5BEC9)
          : MboloColors.mutedInk,
      outline: isDark ? const Color(0xFF9F7E8D) : const Color(0xFF826773),
      outlineVariant: isDark
          ? const Color(0xFF513B46)
          : const Color(0xFFE7D6DD),
      shadow: Colors.black,
      scrim: Colors.black,
      inverseSurface: isDark ? MboloColors.ivory : MboloColors.deepGraphite,
      onInverseSurface: isDark ? MboloColors.ink : MboloColors.ivory,
      inversePrimary: isDark ? MboloColors.romance : MboloColors.powderedRose,
      surfaceTint: Colors.transparent,
    );

    final textTheme = _textTheme(base.textTheme, scheme.onSurface);
    final controlShape = RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(MboloRadius.control),
    );
    final inputBorder = OutlineInputBorder(
      borderRadius: BorderRadius.circular(MboloRadius.control),
      borderSide: BorderSide(color: scheme.outlineVariant),
    );

    return base.copyWith(
      colorScheme: scheme,
      textTheme: textTheme,
      scaffoldBackgroundColor: isDark
          ? MboloColors.midnight
          : MboloColors.ivory,
      splashFactory: InkSparkle.splashFactory,
      visualDensity: VisualDensity.standard,
      pageTransitionsTheme: const PageTransitionsTheme(
        builders: {
          TargetPlatform.android: _MboloPageTransitionsBuilder(),
          TargetPlatform.iOS: _MboloPageTransitionsBuilder(),
        },
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: isDark ? MboloColors.midnight : MboloColors.ivory,
        foregroundColor: scheme.onSurface,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: textTheme.titleLarge,
      ),
      cardTheme: CardThemeData(
        color: isDark ? MboloColors.plumSurface : MboloColors.white,
        elevation: 0,
        margin: EdgeInsets.zero,
        clipBehavior: Clip.antiAlias,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(MboloRadius.card),
          side: BorderSide(color: scheme.outlineVariant.withValues(alpha: .7)),
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: isDark
            ? MboloColors.blackPlum
            : MboloColors.white,
        indicatorColor: scheme.primaryContainer,
        indicatorShape: const StadiumBorder(),
        height: 76,
        elevation: 0,
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          return textTheme.labelMedium?.copyWith(
            color: states.contains(WidgetState.selected)
                ? scheme.primary
                : scheme.onSurfaceVariant,
            fontWeight: states.contains(WidgetState.selected)
                ? FontWeight.w800
                : FontWeight.w600,
          );
        }),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(48, 54),
          textStyle: textTheme.labelLarge,
          shape: controlShape,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(48, 52),
          textStyle: textTheme.labelLarge,
          side: BorderSide(color: scheme.outlineVariant),
          shape: controlShape,
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          minimumSize: const Size(44, 44),
          textStyle: textTheme.labelLarge,
          shape: controlShape,
        ),
      ),
      iconButtonTheme: IconButtonThemeData(
        style: IconButton.styleFrom(minimumSize: const Size.square(48)),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: isDark
            ? MboloColors.plumRaised
            : const Color(0xFFFFEDF3),
        selectedColor: scheme.primaryContainer,
        side: BorderSide(color: scheme.outlineVariant),
        shape: const StadiumBorder(),
        labelStyle: textTheme.labelMedium,
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: isDark ? MboloColors.plumSurface : MboloColors.white,
        contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 17),
        labelStyle: textTheme.bodyMedium?.copyWith(color: scheme.onSurfaceVariant),
        hintStyle: textTheme.bodyMedium?.copyWith(
          color: scheme.onSurfaceVariant.withValues(alpha: .78),
        ),
        border: inputBorder,
        enabledBorder: inputBorder,
        focusedBorder: inputBorder.copyWith(
          borderSide: BorderSide(color: scheme.primary, width: 2),
        ),
        errorBorder: inputBorder.copyWith(
          borderSide: BorderSide(color: scheme.error),
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: isDark
            ? const Color(0xFF382333)
            : MboloColors.deepGraphite,
        contentTextStyle: textTheme.bodyMedium?.copyWith(color: MboloColors.ivory),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(MboloRadius.control),
        ),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: isDark ? MboloColors.plumSurface : MboloColors.white,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(MboloRadius.card),
        ),
      ),
      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: isDark ? MboloColors.plumSurface : MboloColors.white,
        surfaceTintColor: Colors.transparent,
        showDragHandle: true,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(
            top: Radius.circular(MboloRadius.card),
          ),
        ),
      ),
      dividerColor: scheme.outlineVariant,
    );
  }

  static TextTheme _textTheme(TextTheme base, Color color) {
    TextStyle style(
      TextStyle? source, {
      required FontWeight weight,
      required double height,
      required double spacing,
    }) {
      return (source ?? const TextStyle()).copyWith(
        color: color,
        fontWeight: weight,
        height: height,
        letterSpacing: spacing,
      );
    }

    return base.copyWith(
      displayLarge: style(base.displayLarge, weight: FontWeight.w800, height: 1.02, spacing: -1.8),
      displayMedium: style(base.displayMedium, weight: FontWeight.w800, height: 1.04, spacing: -1.4),
      displaySmall: style(base.displaySmall, weight: FontWeight.w800, height: 1.07, spacing: -1.05),
      headlineLarge: style(base.headlineLarge, weight: FontWeight.w800, height: 1.1, spacing: -.85),
      headlineMedium: style(base.headlineMedium, weight: FontWeight.w700, height: 1.12, spacing: -.65),
      headlineSmall: style(base.headlineSmall, weight: FontWeight.w700, height: 1.16, spacing: -.4),
      titleLarge: style(base.titleLarge, weight: FontWeight.w700, height: 1.2, spacing: -.25),
      titleMedium: style(base.titleMedium, weight: FontWeight.w700, height: 1.28, spacing: -.12),
      titleSmall: style(base.titleSmall, weight: FontWeight.w700, height: 1.28, spacing: -.05),
      bodyLarge: style(base.bodyLarge, weight: FontWeight.w400, height: 1.55, spacing: -.08),
      bodyMedium: style(base.bodyMedium, weight: FontWeight.w400, height: 1.5, spacing: -.04),
      bodySmall: style(base.bodySmall, weight: FontWeight.w400, height: 1.45, spacing: 0),
      labelLarge: style(base.labelLarge, weight: FontWeight.w700, height: 1.2, spacing: -.04),
      labelMedium: style(base.labelMedium, weight: FontWeight.w700, height: 1.2, spacing: 0),
      labelSmall: style(base.labelSmall, weight: FontWeight.w600, height: 1.2, spacing: .04),
    );
  }
}

class _MboloPageTransitionsBuilder extends PageTransitionsBuilder {
  const _MboloPageTransitionsBuilder();

  @override
  Widget buildTransitions<T>(
    PageRoute<T> route,
    BuildContext context,
    Animation<double> animation,
    Animation<double> secondaryAnimation,
    Widget child,
  ) {
    if (MediaQuery.maybeOf(context)?.disableAnimations ?? false) return child;
    final curved = CurvedAnimation(
      parent: animation,
      curve: Curves.easeOutCubic,
      reverseCurve: Curves.easeInCubic,
    );
    return FadeTransition(
      opacity: curved,
      child: SlideTransition(
        position: Tween<Offset>(
          begin: const Offset(0.025, 0.014),
          end: Offset.zero,
        ).animate(curved),
        child: ScaleTransition(
          scale: Tween<double>(begin: .994, end: 1).animate(curved),
          child: child,
        ),
      ),
    );
  }
}
