import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/baby.dart';
import 'add_activity_screen.dart';
import '../models/activity.dart';
import 'package:intl/intl.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<Baby> babies = [];
  List<Activity> activities = [];
  bool loading = true;

  @override
  void initState() {
    super.initState();
    fetchBabies();
    fetchTodayActivities();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    fetchBabies();
  }

  Future<void> fetchBabies() async {
    setState(() => loading = true);
    final res = await Supabase.instance.client
        .from('babies')
        .select()
        .order('birth_date');
    babies = (res as List)
        .map((e) => Baby.fromMap(e as Map<String, dynamic>))
        .toList();
    setState(() => loading = false);
  }

  Future<void> fetchTodayActivities() async {
    final now = DateTime.now();
    final start = DateTime(now.year, now.month, now.day);
    final end = start.add(const Duration(days: 1));
    final res = await Supabase.instance.client
        .from('activities')
        .select()
        .gte('time', start.toIso8601String())
        .lt('time', end.toIso8601String())
        .order('time');
    activities = (res as List)
        .map((e) => Activity.fromMap(e as Map<String, dynamic>))
        .toList();
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('סיכום יומי'),
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : babies.isEmpty
              ? Center(
                  child: ElevatedButton(
                    onPressed: () {
                      // TODO: מעבר למסך הוספת תינוק
                    },
                    child: const Text('הוסף תינוק ראשון'),
                  ),
                )
              : RefreshIndicator(
                  onRefresh: () async {
                    await fetchBabies();
                    await fetchTodayActivities();
                  },
                  child: ListView(
                    padding: const EdgeInsets.all(24),
                    children: [
                      const Text('התינוקות שלך:', style: TextStyle(fontSize: 20)),
                      ...babies.map((b) => ListTile(
                            title: Text(b.name),
                            subtitle: Text('נולד/ה: ${b.birthDate.day.toString().padLeft(2, '0')}.${b.birthDate.month.toString().padLeft(2, '0')}.${b.birthDate.year}'),
                          )),
                      const SizedBox(height: 24),
                      _buildSummary(),
                      const SizedBox(height: 24),
                      ElevatedButton(
                        onPressed: () {
                          Navigator.of(context).push(
                            MaterialPageRoute(builder: (_) => const AddActivityScreen()),
                          );
                        },
                        child: const Text('הוסף פעילות'),
                      ),
                    ],
                  ),
                ),
    );
  }

  Widget _buildSummary() {
    if (activities.isEmpty) {
      return const Text('אין פעילויות להיום');
    }
    // אוכל
    int totalFood = 0;
    for (final a in activities.where((a) => a.type == 'feeding')) {
      final amount = a.details != null && a.details!['amount'] != null ? int.tryParse(a.details!['amount'].toString()) ?? 0 : 0;
      totalFood += amount;
    }
    // שינה
    int totalSleepMinutes = 0;
    int naps = 0;
    for (final a in activities.where((a) => a.type == 'sleep')) {
      if (a.endTime != null) {
        totalSleepMinutes += a.endTime!.difference(a.time).inMinutes;
        naps++;
      } else {
        // שינה פתוחה - עד עכשיו
        totalSleepMinutes += DateTime.now().difference(a.time).inMinutes;
      }
    }
    // טיול
    int totalWalkMinutes = 0;
    int walks = 0;
    for (final a in activities.where((a) => a.type == 'walk')) {
      if (a.endTime != null) {
        totalWalkMinutes += a.endTime!.difference(a.time).inMinutes;
        walks++;
      } else {
        totalWalkMinutes += DateTime.now().difference(a.time).inMinutes;
      }
    }
    // פעילות צפויה הבאה (פשוט: סוג הפעילות האחרון)
    String nextType = '';
    if (activities.isNotEmpty) {
      final last = activities.last;
      if (last.type == 'feeding') nextType = 'שינה';
      else if (last.type == 'sleep') nextType = 'האכלה';
      else nextType = 'פעילות';
    }
    // התראות על פעילויות פתוחות
    final openActivities = activities.where((a) => a.isOpenEnded).toList();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('סה"כ אוכל היום: $totalFood מ"ל', style: const TextStyle(fontSize: 18)),
        Text('סה"כ שינה: ${totalSleepMinutes ~/ 60} שעות ו-${totalSleepMinutes % 60} דקות', style: const TextStyle(fontSize: 18)),
        Text('מספר תנומות: $naps', style: const TextStyle(fontSize: 18)),
        Text('סה"כ טיול: ${totalWalkMinutes ~/ 60} שעות ו-${totalWalkMinutes % 60} דקות', style: const TextStyle(fontSize: 18)),
        Text('מספר טיולים: $walks', style: const TextStyle(fontSize: 18)),
        Text('הפעילות הצפויה הבאה: $nextType', style: const TextStyle(fontSize: 18, color: Colors.blue)),
        if (openActivities.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text('שים לב: יש פעילויות פתוחות שדורשות סיום!', style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
          ...openActivities.map((a) => Text('${a.type == 'sleep' ? 'שינה' : a.type == 'walk' ? 'טיול' : a.type} התחילה ב-${a.time.hour.toString().padLeft(2, '0')}:${a.time.minute.toString().padLeft(2, '0')}')),
        ],
      ],
    );
  }
} 