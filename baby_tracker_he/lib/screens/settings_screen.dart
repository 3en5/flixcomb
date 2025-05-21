import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/baby.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('הגדרות'),
      ),
      body: ListView(
        children: [
          ListTile(
            leading: const Icon(Icons.child_care),
            title: const Text('ערוך שם תינוק'),
            onTap: () {},
          ),
          ListTile(
            leading: const Icon(Icons.add),
            title: const Text('הוסף תינוק נוסף'),
            onTap: () async {
              final nameController = TextEditingController();
              final dateController = TextEditingController();
              DateTime? birthDate;
              bool saving = false;
              await showDialog(
                context: context,
                builder: (ctx) => StatefulBuilder(
                  builder: (ctx, setState) => AlertDialog(
                    title: const Text('הוסף תינוק'),
                    content: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        TextField(
                          controller: nameController,
                          decoration: const InputDecoration(labelText: 'שם'),
                          textDirection: TextDirection.rtl,
                        ),
                        TextField(
                          controller: dateController,
                          decoration: const InputDecoration(labelText: 'תאריך לידה (YYYY-MM-DD)'),
                          readOnly: true,
                          onTap: () async {
                            final picked = await showDatePicker(
                              context: context,
                              initialDate: DateTime.now(),
                              firstDate: DateTime(2015),
                              lastDate: DateTime.now(),
                            );
                            if (picked != null) {
                              birthDate = picked;
                              dateController.text = '${picked.year}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}';
                            }
                          },
                        ),
                      ],
                    ),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.pop(ctx),
                        child: const Text('ביטול'),
                      ),
                      ElevatedButton(
                        onPressed: saving ? null : () async {
                          if (nameController.text.isNotEmpty && birthDate != null) {
                            setState(() => saving = true);
                            final userId = Supabase.instance.client.auth.currentUser?.id;
                            try {
                              await Supabase.instance.client.from('babies').insert({
                                'user_id': userId,
                                'name': nameController.text.trim(),
                                'birth_date': birthDate!.toIso8601String().substring(0,10),
                              });
                              if (context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(content: Text('התינוק נוסף בהצלחה!')),
                                );
                              }
                              Navigator.pop(ctx);
                            } catch (e) {
                              if (context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text('שגיאה בהוספה: $e')),
                                );
                              }
                            } finally {
                              setState(() => saving = false);
                            }
                          }
                        },
                        child: saving
                            ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2))
                            : const Text('שמור'),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('התנתק'),
            onTap: () async {
              await Supabase.instance.client.auth.signOut();
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('התנתקת מהחשבון')), 
                );
              }
            },
          ),
        ],
      ),
    );
  }
} 