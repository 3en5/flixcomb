import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'screens/auth_screen.dart';
import 'screens/home_screen.dart';
import 'screens/timeline_screen.dart';
import 'screens/settings_screen.dart';
import 'dart:async';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Supabase.initialize(
    url: 'https://ngmajnafcprelspbaduv.supabase.co',
    anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5nbWFqbmFmY3ByZWxzcGJhZHV2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcxMTc4MTYsImV4cCI6MjA2MjY5MzgxNn0.V6bCR1b7l9OVKSSPkbYapPwskxg-9HpK7_l6Ish6ggE',
  );
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'מעקב תינוק',
      theme: ThemeData(
        // This is the theme of your application.
        //
        // TRY THIS: Try running your application with "flutter run". You'll see
        // the application has a purple toolbar. Then, without quitting the app,
        // try changing the seedColor in the colorScheme below to Colors.green
        // and then invoke "hot reload" (save your changes or press the "hot
        // reload" button in a Flutter-supported IDE, or press "r" if you used
        // the command line to start the app).
        //
        // Notice that the counter didn't reset back to zero; the application
        // state is not lost during the reload. To reset the state, use hot
        // restart instead.
        //
        // This works for code too, not just values: Most code changes can be
        // tested with just a hot reload.
        fontFamily: 'Rubik',
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.lightBlueAccent),
        useMaterial3: true,
      ),
      locale: const Locale('he', 'IL'),
      supportedLocales: const [Locale('he', 'IL')],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      builder: (context, child) {
        return Directionality(
          textDirection: TextDirection.rtl,
          child: child!,
        );
      },
      home: const RootRouter(),
    );
  }
}

class RootRouter extends StatefulWidget {
  const RootRouter({Key? key}) : super(key: key);
  @override
  State<RootRouter> createState() => _RootRouterState();
}

class _RootRouterState extends State<RootRouter> {
  late final StreamSubscription<AuthState> _authSub;

  @override
  void initState() {
    super.initState();
    _authSub = Supabase.instance.client.auth.onAuthStateChange.listen((data) {
      setState(() {});
    });
  }

  @override
  void dispose() {
    _authSub.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final session = Supabase.instance.client.auth.currentSession;
    if (session == null) {
      return const AuthScreen();
    }
    return const MainNav();
  }
}

class MainNav extends StatefulWidget {
  const MainNav({Key? key}) : super(key: key);
  @override
  State<MainNav> createState() => _MainNavState();
}

class _MainNavState extends State<MainNav> {
  int _selected = 0;
  final _screens = [const HomeScreen(), const TimelineScreen(), const SettingsScreen()];
  final _titles = ['סיכום יומי', 'ציר זמן', 'הגדרות'];
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_selected],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selected,
        onTap: (i) => setState(() => _selected = i),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'בית'),
          BottomNavigationBarItem(icon: Icon(Icons.timeline), label: 'ציר זמן'),
          BottomNavigationBarItem(icon: Icon(Icons.settings), label: 'הגדרות'),
        ],
      ),
    );
  }
}
