---
name: kafka-testing
description: Java Kafka integration testing — EmbeddedKafka, Testcontainers, common patterns,
  pitfalls, and the trainer project at ~/trainer/kafka-test-trainer/. Load when the user needs
  to write, debug, or practice Kafka tests in Java (Spring Kafka, plain client, or Streams).
---

# Kafka Testing (Java)

Load this skill when the user:
- Writes or debugs Kafka integration tests in Java
- Wants to practice Kafka testing patterns
- Hits Kafka-related test failures and needs root-cause patterns

## Reference project

A working, self-contained trainer lives at:
`/Users/dmitrypotekhin/trainer/kafka-test-trainer/`

**GitHub:** `https://github.com/dmpotekhin/-Kafka-testing-sandbox`

It has 6 exercise packages with 12 tests covering producer/consumer, async, error handling,
idempotence, batching, and MockConsumer. All tests pass on EmbeddedKafka (no Docker needed).

The README has a dark-themed hero SVG at `assets/readme/hero.svg` showing the test runner
output. The project structure is designed for beauty — use `beautify-github-readme` skill
when the user wants visual polish for a project README.

**No Spring Boot.** The trainer uses raw Kafka client API (`KafkaProducer`, `KafkaConsumer`,
`AdminClient`) via `KafkaTestUtils` helpers. This is intentional — learn the protocol first,
then layer Spring Kafka (`@KafkaListener`, `KafkaTemplate`) on top.

Run: `cd /Users/dmitrypotekhin/trainer/kafka-test-trainer && mvn test`

## Dependency stack (Maven)

```xml
<!-- Spring Kafka Test (EmbeddedKafka — no Docker) -->
<dependency>
    <groupId>org.springframework.kafka</groupId>
    <artifactId>spring-kafka-test</artifactId>
    <scope>test</scope>
</dependency>

<!-- Testcontainers (optional, needs Docker) -->
<dependency>
    <groupId>org.testcontainers</groupId>
    <artifactId>kafka</artifactId>
    <scope>test</scope>
</dependency>

<!-- Awaitility — async assertions, never Thread.sleep -->
<dependency>
    <groupId>org.awaitility</groupId>
    <artifactId>awaitility</artifactId>
    <scope>test</scope>
</dependency>

<!-- AssertJ — fluent assertions -->
<dependency>
    <groupId>org.assertj</groupId>
    <artifactId>assertj-core</artifactId>
    <scope>test</scope>
</dependency>
```

## Core testing patterns

### 1. Isolate tests with unique topic names

Never share topics across tests. Use `@BeforeEach` + UUID suffix:

```java
@BeforeEach
void setUp() {
    String suffix = UUID.randomUUID().toString().substring(0, 6);
    topic = "orders-" + suffix;
    KafkaTestUtils.createTopic(topic, 1, (short) 1);
}
```

### 2. Use `consumer.assign()` for poison-pill / crash-loop tests

`subscribe()` goes through the group coordinator — rebalancing adds latency and
can mask the behavior you're testing. For deterministic re-read tests, use `assign()`:

```java
consumer.assign(List.of(new TopicPartition(topic, 0)));
consumer.seekToBeginning(List.of(tp));
```

### 3. Use `consumer.seek()` to simulate retry

Offset moves forward in the consumer session even WITHOUT `commitSync()`.
To re-read a bad message, explicitly `seek()` back:

```java
consumer.seek(tp, badOffset);
```

### 4. Use Awaitility, never Thread.sleep

```java
await()
    .atMost(Duration.ofSeconds(15))
    .pollInterval(Duration.ofMillis(200))
    .untilAsserted(() -> assertThat(receivedMessages).hasSize(expectedCount));
```

### 5. MockConsumer for pure unit tests

When testing message parsing/transformation logic, skip the broker entirely:

```java
MockConsumer<String, String> mock = new MockConsumer<>(OffsetResetStrategy.EARLIEST);
mock.assign(Collections.singletonList(tp));
mock.addRecord(new ConsumerRecord<>("orders", 0, 0L, "key", "{\"orderId\":1}"));
```

## Pitfalls

| Pitfall | Fix |
|---------|-----|
| `Map.of("key", "val")` → `Map<String,String>` rejected by `newProducer(Map<String,Object>)` | Use helper `KafkaTestUtils.props("k1","v1","k2","v2")` returning `Map<String,Object>` |
| `new ProducerRecord<>(topic, value)` → key type inferred as `Object` | Explicit: `new ProducerRecord<String,String>(topic, null, value)` |
| Consumer offset moves forward in-session even without commit | Use `consumer.seek(tp, offset)` to go back |
| EmbeddedKafka doesn't support transactions (`initTransactions()` hangs) | Mark with `@Disabled("Requires -Ptestcontainers")` |
| Idempotent producer ≠ same-key dedup | Idempotence prevents retry-duplicates by (producerId, seqNo), NOT same-business-key dedup. For that use compacted topics or application-level dedup. |
| Multiple tests writing to same topic — cross-contamination | Unique topic per test (UUID suffix) |

## Common test scenarios (→ trainer project)

| Scenario | Package |
|----------|---------|
| Smoke test: produce → consume | `_01_basics` |
| Async consumer + Awaitility | `_02_async` |
| Poison pill → DLQ via seek() | `_03_errors` |
| Idempotent producer boundaries | `_04_idempotent` |
| Batching + compression perf | `_05_batching` |
| MockConsumer unit tests | `_06_mock_consumer` |

## Support files

- `references/pitfalls-and-errors.md` — real compiler errors with root-cause analysis
