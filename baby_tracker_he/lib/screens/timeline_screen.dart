import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/activity.dart';
import '../models/baby.dart';
import 'add_activity_screen.dart';

class TimelineScreen extends StatefulWidget {
  const TimelineScreen({Key? key}) : super(key: key);

  @override
  State<TimelineScreen> createState() => _TimelineScreenState();
}

class _TimelineScreenState extends State<TimelineScreen> {
  List<Activity> activities = [];
  Map<String, String> babyNames = {};
  bool loading = true;

  @override
  void initState() {
    super.initState();
    fetchData();
  }

  Future<void> fetchData() async {
    setState(() => loading = true);
    final now = DateTime.now();
    final startOfDay = DateTime(now.year, now.month, now.day);
    final endOfDay = startOfDay.add(const Duration(days: 1));
    final acts = await Supabase.instance.client
        .from('activities')
        .select()
        .gte('time', startOfDay.toIso8601String())
        .lt('time', endOfDay.toIso8601String())
        .order('time', ascending: false);
    final babies = await Supabase.instance.client
        .from('babies')
        .select();
    babyNames = {for (var b in babies) b['id']: b['name']};
    activities = (acts as List)
        .map((e) => Activity.fromMap(e as Map<String, dynamic>))
        .toList();
    setState(() => loading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ציר זמן יומי'),
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : activities.isEmpty
              ? const Center(child: Text('אין פעילויות להיום'))
              : RefreshIndicator(
                  onRefresh: fetchData,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: activities.length,
                    itemBuilder: (ctx, i) {
                      final a = activities[i];
                      final babyName = babyNames[a.babyId] ?? '';
                      final time = '${a.time.hour.toString().padLeft(2, '0')}:${a.time.minute.toString().padLeft(2, '0')}';
                      return ListTile(
                        leading: Icon(_iconForType(a.type), color: _colorForType(a.type)),
                        title: Text('${_hebrewType(a.type)}${babyName.isNotEmpty ? ' - $babyName' : ''}'),
                        subtitle: Text('$time${a.notes != null && a.notes!.isNotEmpty ? ' | ${a.notes}' : ''}${a.isOpenEnded ? ' (לא הסתיים)' : a.endTime != null ? ' - הסתיים ב-${a.endTime!.hour.toString().padLeft(2, '0')}:${a.endTime!.minute.toString().padLeft(2, '0')}' : ''}'),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            if (a.isOpenEnded)
                              IconButton(
                                icon: const Icon(Icons.flag),
                                tooltip: 'סיים פעילות',
                                onPressed: () async {
                                  int hours = 0;
                                  int minutes = 0;
                                  final res = await showDialog<List<int>>(
                                    context: context,
                                    builder: (ctx) {
                                      return AlertDialog(
                                        title: const Text('כמה זמן עבר מאז תחילת הפעילות?'),
                                        content: Row(
                                          mainAxisAlignment: MainAxisAlignment.center,
                                          children: [
                                            SizedBox(
                                              width: 60,
                                              child: TextField(
                                                keyboardType: TextInputType.number,
                                                decoration: const InputDecoration(labelText: 'שעות'),
                                                onChanged: (v) => hours = int.tryParse(v) ?? 0,
                                              ),
                                            ),
                                            const SizedBox(width: 16),
                                            SizedBox(
                                              width: 60,
                                              child: TextField(
                                                keyboardType: TextInputType.number,
                                                decoration: const InputDecoration(labelText: 'דקות'),
                                                onChanged: (v) => minutes = int.tryParse(v) ?? 0,
                                              ),
                                            ),
                                          ],
                                        ),
                                        actions: [
                                          TextButton(
                                            onPressed: () => Navigator.pop(ctx),
                                            child: const Text('ביטול'),
                                          ),
                                          ElevatedButton(
                                            onPressed: () => Navigator.pop(ctx, [hours, minutes]),
                                            child: const Text('סיים'),
                                          ),
                                        ],
                                      );
                                    },
                                  );
                                  if (res == null) return;
                                  final endDate = a.time.add(Duration(hours: res[0], minutes: res[1]));
                                  if (endDate.isBefore(a.time)) {
                                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('משך הזמן חייב להיות חיובי')));
                                    return;
                                  }
                                  final newDetails = Map<String, dynamic>.from(a.details ?? {});
                                  newDetails['end'] = endDate.toIso8601String();
                                  await Supabase.instance.client.from('activities').update({'details': newDetails}).eq('id', a.id);
                                  if (mounted) {
                                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('הפעילות סומנה כהסתיימה')));
                                  }
                                  fetchData();
                                },
                              ),
                            IconButton(
                              icon: const Icon(Icons.edit),
                              onPressed: () async {
                                await Navigator.of(context).push(
                                  MaterialPageRoute(
                                    builder: (_) => AddActivityScreen(activity: a),
                                  ),
                                );
                                fetchData();
                              },
                            ),
                          ],
                        ),
                        onLongPress: () async {
                          final confirm = await showDialog<bool>(
                            context: context,
                            builder: (ctx) => AlertDialog(
                              title: const Text('מחיקת פעילות'),
                              content: const Text('האם למחוק פעילות זו?'),
                              actions: [
                                TextButton(
                                  onPressed: () => Navigator.pop(ctx, false),
                                  child: const Text('ביטול'),
                                ),
                                ElevatedButton(
                                  onPressed: () => Navigator.pop(ctx, true),
                                  child: const Text('מחק'),
                                ),
                              ],
                            ),
                          );
                          if (confirm == true) {
                            try {
                              await Supabase.instance.client.from('activities').delete().eq('id', a.id);
                              if (mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(content: Text('הפעילות נמחקה בהצלחה!')),
                                );
                              }
                            } catch (e) {
                              if (mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text('שגיאה במחיקה: $e')),
                                );
                              }
                            }
                            fetchData();
                          }
                        },
                      );
                    },
                  ),
                ),
    );
  }

  IconData _iconForType(String type) {
    switch (type) {
      case 'feeding': return Icons.emoji_food_beverage;
      case 'sleep': return Icons.bedtime;
      case 'walk': return Icons.stroller;
      case 'mood': return Icons.emoji_emotions;
      default: return Icons.event;
    }
  }

  Color _colorForType(String type) {
    switch (type) {
      case 'feeding': return Colors.blue;
      case 'sleep': return Colors.purple;
      case 'walk': return Colors.green;
      case 'mood': return Colors.orange;
      default: return Colors.grey;
    }
  }

  String _hebrewType(String type) {
    switch (type) {
      case 'feeding': return 'האכלה';
      case 'sleep': return 'שינה';
      case 'walk': return 'טיול';
      case 'mood': return 'מצב רוח';
      default: return type;
    }
  }
} 