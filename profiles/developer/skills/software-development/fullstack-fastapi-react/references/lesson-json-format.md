# Lesson JSON Template

Lessons are stored as JSON files in `backend/lessons/`. Each file defines one course with a list of tasks.

## Full Example

```json
{
  "id": "lesson_python_basics",
  "title": "Основы Python",
  "description": "Узнай, как компьютер выполняет команды!",
  "tasks": [
    {
      "id": "py_task_1",
      "type": "choice",
      "question": "Что делает функция print()?",
      "options": ["Выключает компьютер", "Выводит текст на экран", "Считает числа"],
      "correct_answer": 1,
      "hint": "Print переводится как «печатать».",
      "points": 5
    },
    {
      "id": "py_task_2",
      "type": "number",
      "question": "Сколько будет 2 + 2 * 3?",
      "correct_answer": "8",
      "hint": "Сначала умножение: 2 * 3 = 6, потом 2 + 6 = 8.",
      "points": 5
    },
    {
      "id": "py_task_3",
      "type": "text",
      "question": "Как называется символ присваивания в Python?",
      "correct_answer": "=",
      "hint": "Это не двойное равно.",
      "points": 5
    },
    {
      "id": "py_task_4",
      "type": "code",
      "question": "Напиши код, который выводит 'Привет, мир!'",
      "correct_answer": "print('Привет, мир!')",
      "expected_output": "Привет, мир!",
      "hint": "Используй print() и кавычки.",
      "points": 10
    }
  ]
}
```

## Task Types

| type | Проверка | answer (от фронтенда) | Обязательные поля |
|------|----------|----------------------|-------------------|
| `choice` | индекс совпадает с `correct_answer` | `"0"`, `"1"`, ... | `options`, `correct_answer` (int) |
| `number` | точное совпадение числа (float tolerance 0.001) | `"42"` | `correct_answer` (string) |
| `text` | сравнение строк (trim + lowercase) | `"hello"` | `correct_answer` (string) |
| `code` | subprocess execution → stdout vs `expected_output` | `"print(1+1)"` | `correct_answer`, `expected_output` |

## API Safety

`GET /api/lessons/{id}` must NEVER return `correct_answer` or `expected_output`.
The backend strips these fields before serialization using a separate Pydantic model (`TaskPublic` without answer fields).
