# LLM Configurations

## Purpose

The LLM Configurations page manages reusable model configurations used by AI Tasks.

Executor and Provider are fixed by the system.

---

## Page Layout

```text
┌────────────────────────────────────────────────────────────────────────────────────┐
│ LLM Configurations                                        [Add Configuration]      │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│ Configuration List                                                                 │
│                                                                                    │
│ ┌────────────────────────────────────────────────────────────────────────────────┐ │
│ │ Production GPT-5                                                      [More]   │ │
│ │ Executor : OpenCode                                               Enabled      │ │
│ │ Provider : OpenAI                                                        │     │ │
│ │ Model    : GPT-5                                                         │     │ │
│ └────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                    │
│ ┌────────────────────────────────────────────────────────────────────────────────┐ │
│ │ GPT-5 Mini                                                         [More]      │ │
│ │ Executor : OpenCode                                              Disabled      │ │
│ │ Provider : OpenAI                                                        │     │ │
│ │ Model    : GPT-5 Mini                                                    │     │ │
│ └────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Available Actions

- View
- Edit
- Enable
- Disable
- Delete

---

## Empty State

```text
No LLM Configurations found.

Create your first configuration.

               [Add Configuration]
```

---

## Loading State

Display skeleton cards.

---

## Error State

```text
Unable to load configurations.

[Retry]
```

---

## Navigation

```text
Settings

└── AI

    └── LLM Configurations
```
