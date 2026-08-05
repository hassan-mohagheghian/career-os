# Company Row

## Purpose

A single row in the virtualized Company List. Provides a compact overview of a
company's identity, AI evaluation, processing state, and available actions.

Rows are never expandable. Selecting a row opens the Company Detail drawer.

---

# Row Columns

| Column    | Description                               |
| --------- | ----------------------------------------- |
| Grade     | Overall grade badge (A++ … D)             |
| Name      | Company logo and name                     |
| Industry  | Industry classification                   |
| Location  | City, Country                             |
| Size      | Company size band                         |
| Jobs      | Number of linked, non-deleted jobs        |
| Scores    | Fit / Success / Overall score values      |
| Status    | Legacy processing state                   |
| Updated   | Relative update time                      |
| Actions   | Details, Reprocess, Edit, Delete          |

---

# Grade

```text
A++
```

Color matches the shared grade tokens (A++/A+ green, A lime, B blue, C orange,
D red). No grade renders `—`.

---

# Scores

```text
F 85   S 90   O 88
```

Null scores render `—`.

---

# Status

```text
Processed
Completed
Pending
Processing
Failed
```

Processing/Running render a pulsing dot.

---

# Actions

Icon buttons with tooltips. All actions stop propagation:

- Details — opens the detail drawer
- Reprocess — re-enqueues for processing
- Edit — opens the edit drawer
- Delete — deletes with confirmation

---

# Related Documents

- `docs/ux/features/companies/page.md`
