# Delete LLM Configuration

## Purpose

Deletes an existing LLM Configuration.

---

## Trigger

More

↓

Delete

---

## Confirmation Dialog

```text
Delete LLM Configuration?

This action cannot be undone.

[Cancel]        [Delete]
```

---

## Success

- Configuration is removed.
- List refreshes.
- Success notification is displayed.

---

## Failure

If the configuration is currently used by an AI Task:

```text
This configuration cannot be deleted because it is currently in use.
```
