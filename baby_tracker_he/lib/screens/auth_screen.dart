import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({Key? key}) : super(key: key);

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _loading = false;
  String? _error;
  bool _showPassword = false;

  Future<void> _signIn() async {
    setState(() { _loading = true; _error = null; });
    try {
      final res = await Supabase.instance.client.auth.signInWithPassword(
        email: _emailController.text.trim(),
        password: _passwordController.text.trim(),
      );
      if (res.user == null) {
        setState(() { _error = 'שגיאה בכניסה. בדוק אימייל וסיסמה.'; });
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('התחברת בהצלחה!')),
          );
        }
      }
    } catch (e) {
      setState(() { _error = 'שגיאה: $e'; });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('שגיאה: $e')),
        );
      }
    } finally {
      setState(() { _loading = false; });
    }
  }

  Future<void> _signUp() async {
    setState(() { _loading = true; _error = null; });
    try {
      final res = await Supabase.instance.client.auth.signUp(
        email: _emailController.text.trim(),
        password: _passwordController.text.trim(),
      );
      if (res.user == null) {
        setState(() { _error = 'שגיאה בהרשמה. ייתכן שהאימייל כבר קיים.'; });
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('נרשמת בהצלחה!')), 
          );
        }
      }
    } catch (e) {
      setState(() { _error = 'שגיאה: $e'; });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('שגיאה: $e')),
        );
      }
    } finally {
      setState(() { _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text('ברוכים הבאים!', style: Theme.of(context).textTheme.headlineMedium, textAlign: TextAlign.center),
              const SizedBox(height: 32),
              TextField(
                controller: _emailController,
                textDirection: TextDirection.rtl,
                decoration: const InputDecoration(labelText: 'אימייל'),
                keyboardType: TextInputType.emailAddress,
                onSubmitted: (_) => _signIn(),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _passwordController,
                textDirection: TextDirection.rtl,
                decoration: InputDecoration(
                  labelText: 'סיסמה',
                  suffixIcon: IconButton(
                    icon: Icon(_showPassword ? Icons.visibility : Icons.visibility_off),
                    onPressed: () => setState(() => _showPassword = !_showPassword),
                  ),
                ),
                obscureText: !_showPassword,
                onSubmitted: (_) => _signIn(),
              ),
              const SizedBox(height: 24),
              if (_error != null) ...[
                Text(_error!, style: const TextStyle(color: Colors.red), textAlign: TextAlign.center),
                const SizedBox(height: 12),
              ],
              ElevatedButton(
                onPressed: _loading ? null : _signIn,
                child: _loading ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2)) : const Text('כניסה'),
                style: ElevatedButton.styleFrom(minimumSize: const Size.fromHeight(48)),
              ),
              TextButton(
                onPressed: _loading ? null : _signUp,
                child: const Text('אין לך חשבון? הרשמה'),
              ),
            ],
          ),
        ),
      ),
    );
  }
} 