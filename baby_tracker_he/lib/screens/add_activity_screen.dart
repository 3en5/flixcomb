import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/baby.dart';
import '../models/activity.dart';

class AddActivityScreen extends StatefulWidget {
  final Activity? activity;
  const AddActivityScreen({Key? key, this.activity}) : super(key: key);

  @override
  State<AddActivityScreen> createState() => _AddActivityScreenState();
}

class _AddActivityScreenState extends State<AddActivityScreen> {
  String? _type;
  DateTime _time = DateTime.now();
  DateTime _date = DateTime.now();
  final _notesController = TextEditingController();
  final _amountController = TextEditingController();
  List<Baby> babies = [];
  Baby? selectedBaby;
  bool loading = true;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    fetchBabies();
    if (widget.activity != null) {
      _type = widget.activity!.type;
      _time = widget.activity!.time;
      _date = widget.activity!.time;
      _notesController.text = widget.activity!.notes ?? '';
      if (widget.activity!.type == 'feeding' && widget.activity!.details != null && widget.activity!.details!['amount'] != null) {
        _amountController.text = widget.activity!.details!['amount'].toString();
      }
    }
  }

  Future<void> fetchBabies() async {
    final res = await Supabase.instance.client
        .from('babies')
        .select()
        .order('birth_date');
    babies = (res as List)
        .map((e) => Baby.fromMap(e as Map<String, dynamic>))
        .toList();
    if (babies.isNotEmpty) {
      if (widget.activity != null) {
        selectedBaby = babies.firstWhere((b) => b.id == widget.activity!.babyId, orElse: () => babies.first);
      } else {
        selectedBaby = babies.first;
      }
    }
    setState(() => loading = false);
  }

  Future<void> saveActivity() async {
    if (_type == null || selectedBaby == null) return;
    final activityDateTime = DateTime(_date.year, _date.month, _date.day, _time.hour, _time.minute);
    Map<String, dynamic>? details;
    if (_type == 'feeding' && _amountController.text.isNotEmpty) {
      details = {'amount': _amountController.text};
    }
    try {
      if (widget.activity == null) {
        await Supabase.instance.client.from('activities').insert({
          'baby_id': selectedBaby!.id,
          'type': _type,
          'time': activityDateTime.toIso8601String(),
          'notes': _notesController.text.trim(),
          'details': details,
        });
      } else {
        await Supabase.instance.client.from('activities').update({
          'baby_id': selectedBaby!.id,
          'type': _type,
          'time': activityDateTime.toIso8601String(),
          'notes': _notesController.text.trim(),
          'details': details,
        }).eq('id', widget.activity!.id);
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(widget.activity == null ? 'הפעילות נשמרה בהצלחה!' : 'הפעילות עודכנה בהצלחה!')),
        );
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('שגיאה בשמירה: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (loading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    return Scaffold(
      appBar: AppBar(title: Text(widget.activity == null ? 'הוסף פעילות' : 'ערוך פעילות')), 
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (babies.length > 1)
              DropdownButtonFormField<Baby>(
                value: selectedBaby,
                items: babies.map((b) => DropdownMenuItem(value: b, child: Text(b.name))).toList(),
                onChanged: (b) => setState(() => selectedBaby = b),
                decoration: const InputDecoration(labelText: 'בחר תינוק'),
              ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _type,
              items: const [
                DropdownMenuItem(value: 'feeding', child: Text('האכלה')),
                DropdownMenuItem(value: 'sleep', child: Text('שינה')),
                DropdownMenuItem(value: 'walk', child: Text('טיול')),
                DropdownMenuItem(value: 'mood', child: Text('מצב רוח')),
              ],
              onChanged: (v) => setState(() => _type = v),
              decoration: const InputDecoration(labelText: 'סוג פעילות'),
            ),
            if (_type == 'feeding') ...[
              const SizedBox(height: 16),
              TextField(
                controller: _amountController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'כמות (מ"ל/גרם)'),
                textDirection: TextDirection.rtl,
              ),
            ],
            const SizedBox(height: 16),
            Row(
              children: [
                const Text('תאריך:'),
                const SizedBox(width: 8),
                TextButton(
                  onPressed: () async {
                    final picked = await showDatePicker(
                      context: context,
                      initialDate: _date,
                      firstDate: DateTime(2015),
                      lastDate: DateTime.now().add(const Duration(days: 365)),
                    );
                    if (picked != null) {
                      setState(() {
                        _date = picked;
                      });
                    }
                  },
                  child: Text('${_date.day.toString().padLeft(2, '0')}.${_date.month.toString().padLeft(2, '0')}.${_date.year}'),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                const Text('שעה:'),
                const SizedBox(width: 8),
                TextButton(
                  onPressed: () async {
                    final t = await showTimePicker(
                      context: context,
                      initialTime: TimeOfDay.fromDateTime(_time),
                    );
                    if (t != null) {
                      setState(() {
                        _time = DateTime(_time.year, _time.month, _time.day, t.hour, t.minute);
                      });
                    }
                  },
                  child: Text('${_time.hour.toString().padLeft(2, '0')}:${_time.minute.toString().padLeft(2, '0')}'),
                ),
              ],
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _notesController,
              textDirection: TextDirection.rtl,
              decoration: const InputDecoration(labelText: 'הערות (לא חובה)'),
            ),
            const Spacer(),
            ElevatedButton(
              onPressed: _saving ? null : saveActivity,
              child: _saving
                  ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2))
                  : Text(widget.activity == null ? 'שמור' : 'עדכן'),
            ),
          ],
        ),
      ),
    );
  }
} 