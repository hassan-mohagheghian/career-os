# Add Company

## Purpose

The Add Company drawer imports a new company into the legacy company processing
pipeline. It is the company variant of the shared **Create Entity drawer**
(also used by the Add Job drawer, see `docs/ux/features/jobs/add-job.md`).

The form follows this field order: **primary link → optional name → additional
links → optional notes**.

---

# Drawer Layout

```text
┌──────────────────────────────────────────────┐
│ + Add Company                                │
├──────────────────────────────────────────────┤
│                                              │
│ Primary Link *                               │
│ ┌───────────────────────────────┐            │
│ │ https://acme.example          │            │
│ └───────────────────────────────┘            │
│ [Website]  [LinkedIn]                        │
│                                              │
│ Company Name (Optional)                      │
│ ┌───────────────────────────────┐            │
│ │ Acme GmbH                    │            │
│ └───────────────────────────────┘            │
│                                              │
│ Additional Links                  [+ Add]    │
│ (link list)                                  │
│                                              │
│ Notes                             [+ Add]    │
│ (note list)                                  │
│                                              │
│   [        Add        ] [ Add & Process (x) ]│
│                                              │
└──────────────────────────────────────────────┘
```

---

# Behavior

## Primary Link

The primary link is the main source for the company and is required. The URL is
typed into the input; URLs missing a scheme are prefixed with `https://`.

A title can be selected from the preset chips **Website** and **LinkedIn**.
Clicking a chip toggles it on/off. Only one primary title can be active.

## Company Name

Optional. If provided, the name is persisted with the pending company and shown
in the Company Queue. If empty, the primary link URL is used as the display
name.

## Additional Links

The `+ Add` toggle reveals URL + title inputs. Quick preset titles: LinkedIn,
Website, Careers, GitHub. If Website or LinkedIn is already selected as the
primary title, that chip is disabled in the additional-link selector. URLs
missing a scheme are prefixed with `https://`.

## Notes

Optional free-text notes. Each note is typed into the textarea and added with
the `+` button. Notes whose content starts with `http` are treated as URLs
(rendered as links). Notes can be removed before submit.

## Submit

Two actions are offered in the footer:

| Action         | Behavior                                        | State        |
| -------------- | ----------------------------------------------- | ------------ |
| Add            | Adds the company to the list, no processing.    | Enabled      |
| Add & Process  | Adds the company and queues it for processing.  | Disabled for now |

`Add` posts `POST /api/pending-companies` with:

```json
{
  "name": "Acme GmbH",
  "notes": [{ "content": "..." }],
  "links": [{ "url": "https://acme.example", "title": "Website" }],
  "source": "web",
  "queue": false
}
```

The backend creates a `pending_companies` row with status `created` and
persists the name. With `queue: false` the entry is **not** enqueued — it can be
processed later from the Company Queue. When `queue: true`, the entry is enqueued
via `enqueue_company_sync`. The created record is returned.

## After Submit

- A success toast is shown.
- The pending-companies and companies queries are invalidated.
- The drawer closes.
- The entry appears in the Companies list / Company Queue.
- The Company Queue drawer is **not** opened automatically (unlike the Job
  Create & Queue flow).

## Validation

Submit is disabled while:

- There is no primary link URL.

---

# Related Documents

- `docs/ux/features/companies/page.md`
- `docs/ux/features/companies/company-queue.md`
- `docs/ux/flows/companies/browse-companies.md`
- `docs/ux/features/jobs/add-job.md` (job variant of the shared drawer)
