class Baby {
  final String id;
  final String userId;
  final String name;
  final DateTime birthDate;

  Baby({required this.id, required this.userId, required this.name, required this.birthDate});

  factory Baby.fromMap(Map<String, dynamic> map) => Baby(
    id: map['id'] as String,
    userId: map['user_id'] as String,
    name: map['name'] as String,
    birthDate: DateTime.parse(map['birth_date'] as String),
  );

  Map<String, dynamic> toMap() => {
    'id': id,
    'user_id': userId,
    'name': name,
    'birth_date': birthDate.toIso8601String(),
  };
} 