# Add LLM Configuration

## Purpose

Create a reusable LLM Configuration.

---

## Trigger

User clicks:

Add Configuration

---

## Drawer

```text
┌──────────────────────────────────────────────────┐
│ Add LLM Configuration                            │
├──────────────────────────────────────────────────┤
│                                                  │
│ Name *                                           │
│ ┌──────────────────────────────────────────────┐ │
│ └──────────────────────────────────────────────┘ │
│                                                  │
│ Executor                                         │
│ OpenCode                                         │
│                                                  │
│ Provider                                         │
│ OpenAI                                           │
│                                                  │
│ Model *                                          │
│ ┌──────────────────────────────────────────────┐ │
│ └──────────────────────────────────────────────┘ │
│                                                  │
│ Model Version                                   │
│ ┌──────────────────────────────────────────────┐ │
│ └──────────────────────────────────────────────┘ │
│                                                  │
│ Enabled ☑                                       │
│                                                  │
├──────────────────────────────────────────────────┤
│                    Cancel        Create          │
└──────────────────────────────────────────────────┘
```

---

## Validation

Required

- Name
- Model

---

## Success

- Drawer closes.
- Configuration is added to the list.
- Success notification is displayed.

---

## Failure

Display validation or server errors without closing the drawer.
