class Activity {
  final String id;
  final String babyId;
  final String type;
  final DateTime time;
  final Map<String, dynamic>? details;
  final String? notes;
  final DateTime createdAt;

  Activity({
    required this.id,
    required this.babyId,
    required this.type,
    required this.time,
    this.details,
    this.notes,
    required this.createdAt,
  });

  factory Activity.fromMap(Map<String, dynamic> map) => Activity(
    id: map['id'] as String,
    babyId: map['baby_id'] as String,
    type: map['type'] as String,
    time: DateTime.parse(map['time'] as String),
    details: map['details'] as Map<String, dynamic>?,
    notes: map['notes'] as String?,
    createdAt: DateTime.parse(map['created_at'] as String),
  );

  Map<String, dynamic> toMap() => {
    'id': id,
    'baby_id': babyId,
    'type': type,
    'time': time.toIso8601String(),
    'details': details,
    'notes': notes,
    'created_at': createdAt.toIso8601String(),
  };

  bool get isOpenEnded => (type == 'sleep' || type == 'walk') && (details == null || details!['end'] == null);
  DateTime? get endTime => details != null && details!['end'] != null ? DateTime.tryParse(details!['end'].toString()) : null;
} 