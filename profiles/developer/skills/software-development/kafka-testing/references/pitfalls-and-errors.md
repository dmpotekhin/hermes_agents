# Reference: real compiler errors and fix patterns

## Map.of() type mismatch

```
ERROR: incompatible types: Map<String,String> cannot be converted to Map<String,Object>
```

**Root cause:** `Map.of("key", "val")` returns `Map<String,String>` but
`KafkaProducer` constructor and config maps expect `Map<String, Object>`.

**Fix:** Don't use `Map.of()`. Create a helper:

```java
public static Map<String, Object> props(String... keyValues) {
    Map<String, Object> map = new HashMap<>();
    for (int i = 0; i < keyValues.length; i += 2)
        map.put(keyValues[i], keyValues[i + 1]);
    return map;
}
```

## ProducerRecord generic inference

```
ERROR: incompatible types: ProducerRecord<Object,String> cannot be converted
       to ProducerRecord<String,String>
```

**Root cause:** `new ProducerRecord<>(topic, value)` — Java infers key type
from the value parameter alone. When key is omitted or null, the diamond
operator widens to `Object`.

**Fix:** Add explicit type parameters or provide a key:
```java
new ProducerRecord<String,String>(topic, null, value)
```

## Offset moves forward in session without commit

**Observation:** After `consumer.poll()` reads messages, the in-memory position
advances. Even without calling `commitSync()`, the next `poll()` returns
empty — the consumer has moved past the offset.

**Fix:** Use `consumer.seek(tp, offset)` to explicitly reposition before
the next poll.

**Important:** This differs from consumer CRASH behavior. When a consumer
is closed and a NEW consumer joins the same group, it reads from the last
*committed* offset (not the in-memory position). So crash-loop tests work
with new consumer instances but NOT with `seek()`-less polls in the same instance.

## EmbeddedKafka transaction timeout

```
ERROR: Timeout expired after 60000ms while awaiting InitProducerId
```

**Root cause:** `EmbeddedKafkaZKBroker` does not support the transaction
coordinator protocol. `producer.initTransactions()` hangs indefinitely.

**Fix:** Mark transactional tests with:
```java
@Test
@Disabled("Transactions not supported on EmbeddedKafka. Run with -Ptestcontainers")
void transactionalTest() { ... }
```

## Idempotent producer misconception

**Wrong expectation:** "10 sends with the same key → 1 message in topic."

**Reality:** Each `send()` call gets a unique sequence number. Idempotent
producer deduplicates by (producerId, sequenceNumber), NOT by message key.
Same key ≠ same sequence number. The broker stores all 10 messages.

**Correct mental model:** Idempotence protects against RETRY duplicates
(network failure → same send() retried → same sequence number → broker
drops duplicate). It does NOT deduplicate by business key.

For business-key dedup, use:
- Compacted topic (only latest value per key retained)
- Application-level idempotency key in message body
- Transactions with consumer-side dedup
