---
name: security-review
description: Security audit after features or on demand.
version: 1.0.0
tags: [security, audit, sast, code-review]
---

# Security Review

Адаптировано из https://github.com/anthropics/claude-code-security-review (MIT).

## Когда использовать

- **Автоматически**: после завершения feature/architecture-change, перед requesting-code-review
- **Вручную**: когда нужен security audit изменений

## Процесс

### Шаг 1: Получить diff

```bash
git diff origin/HEAD... 2>/dev/null || git diff HEAD~1 2>/dev/null || git diff --staged
```

Если diff пустой — сообщить и выйти.

### Шаг 2: Проанализировать

Прочитать изменённые файлы. Проанализировать diff на уязвимости.

### Шаг 3: Выдать находки в JSON

Формат: массив findings, каждый с полями: file, line, severity (HIGH/MEDIUM/LOW), category, description, exploit_scenario, recommendation, confidence (0.0-1.0).

### Шаг 4: Применить hard exclusion rules

Отфильтровать находки по правилам ниже. Исключённые — показать отдельно.

### Шаг 5: Итог

- HIGH > 0 → STOP, показать пользователю, не продолжать
- MEDIUM > 0 → показать и спросить
- Чисто → "Security review: чисто"

---

## Промпт аудитора

Ты — senior security engineer. Проведи security audit изменений в diff.

**CRITICAL:** только >80% уверенности; только SECURITY-последствия нового кода; не репорти theoretical issues.

**Категории:**

1. **Input Validation**: SQL/command/XXE/template/NoSQL injection, path traversal
2. **Auth/AuthZ**: auth bypass, privilege escalation, session flaws, JWT, IDOR
3. **Crypto & Secrets**: hardcoded keys/tokens, weak algorithms, insecure RNG
4. **Injection & RCE**: deserialization RCE, pickle/YAML injection, eval, XSS
5. **Data Exposure**: sensitive data logging, PII, API data leakage

**Методология:** Repository Context → Comparative Analysis → Vulnerability Assessment (data flow от user input к sensitive ops).

**Формат вывода — строго JSON:**
```json
{
  "findings": [{ "file": "...", "line": 42, "severity": "HIGH", "category": "sql_injection", "description": "...", "exploit_scenario": "...", "recommendation": "...", "confidence": 0.95 }],
  "analysis_summary": { "files_reviewed": 0, "high_severity": 0, "medium_severity": 0, "low_severity": 0, "review_completed": true }
}
```

**Severity:** HIGH (RCE/breach/bypass), MEDIUM (specific conditions, significant impact), LOW (don't report).

**Confidence:** 0.9+ certain, 0.8+ clear pattern, 0.7+ suspicious, below 0.7 — don't report.

---

## Hard Exclusion Rules

Автоматически исключать:

1. DOS / resource exhaustion
2. Rate limiting recommendations
3. Resource leaks (memory, file descriptors)
4. Open redirect
5. Memory safety не в C/C++ файлах
6. Regex injection / ReDoS
7. SSRF в .html файлах
8. Находки в .md файлах
9. Client-side auth checks в JS/TS
10. XSS в React/Angular без dangerouslySetInnerHTML
11. GitHub Actions без конкретного attack path
12. Log spoofing (unsanitized input в логах)
13. Outdated dependencies
14. Lack of hardening без конкретной уязвимости
15. Race conditions без практического сценария
16. UUID guessability
17. CLI/env vars как attack vector
18. Test files

**НЕ исключать:** logging plaintext secrets/passwords/tokens; hardcoded credentials в production коде.

---

## Интеграция

В feature-цикле: после simplify-code, перед requesting-code-review.
HIGH → стоп; MEDIUM → спросить; чисто → продолжать.
