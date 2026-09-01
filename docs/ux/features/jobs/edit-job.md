# Edit Job Drawer

## Purpose

The Edit Job Drawer allows users to correct or complete a Job's core data after it has been imported or processed.

The drawer is opened from the **Edit** action on a **Job Row** in the Jobs page, or from the **Edit** button in the Job Details drawer header (same page-level edit state).

Changes are persisted to the `jobs` record and the affected row refreshes. Editing does not automatically start or stop processing, and is not blocked while an execution is active.

---

# Related Page

Opened from:

- `features/jobs/page.md`
- `features/jobs/job-row.md`

Uses:

- `design-system/drawer.md`

Related:

- `features/jobs/add-job.md`
- `flows/jobs/edit-job.md`

---

# Drawer

- Variant: `md`
- Placement: `right`

---

# Trigger

The **Edit** action in the Job Row's Actions column, or the **Edit** button in
the Job Details drawer header (top-right, next to the "Job Details" title).

Available for all processing statuses.

Clicking **Edit** opens the drawer pre-filled with the job's current values.

---

# User Goals

The user should be able to:

- View the job's current core data
- Update any of the editable fields
- Correct a job post URL
- Update or clear contextual attributes (salary, visa, work type, employment type)
- Edit the description
- Add, edit, and remove **notes**
- Add, edit, and remove **additional links**
- Add, edit, and remove **tags**
- Save changes and see them reflected in the row

---

# Layout

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ Edit Job                                                 [Close]            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│ Title (Optional)                                                           │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ Staff Software Engineer                                                │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│ Role (Optional)                                                            │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                        │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│ Company (Optional)                                                         │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ Acme GmbH                                                              │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│ Location (Optional)                                                        │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ Berlin                                                                 │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│ Job Post URL *                                                            │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ https://...                                                           │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│ Work Type                                                                  │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ On-site ▾                                                              │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│ Employment Type                                                            │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ Full-time ▾                                                            │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│ Visa (Optional)                                                             │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ Strong                                                                 │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│ Salary (Optional)                                                           │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ €90k - €110k                                                           │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│ Notes                                                                      │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ [note 1]  [×]                                                          │ │
│ │ [note 2]  [×]                                                          │ │
│ │ ┌──────────────────────────────────────────────┐ [+]                   │ │
│ │ │ Add a note...                               │ [ + ]                 │ │
│ │ └──────────────────────────────────────────────┘                       │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│ Additional Links                                                            │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ 🔗 https://company.com/careers  [×]                                    │ │
│ │ ┌────────────────────────────┐ ┌──────────────┐ [+]                   │ │
│ │ │ Link URL (https://...)     │ │ Title (opt.) │ [ + ]                 │ │
│ │ └────────────────────────────┘ └──────────────┘                       │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│ Description                                                                 │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ Work alongside a cross-functional team...                             │ │
│ │                                                                        │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│ Tags                                                                       │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ [python] [×]  [remote] [×]  [senior] [×]                              │ │
│ │ ┌──────────────────────────────────────────────┐ [+]                   │ │
│ │ │ Add a tag...                                 │ [ + ]                 │ │
│ │ └──────────────────────────────────────────────┘                       │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│────────────────────────────────────────────────────────────────────────────│
│                                                                             │
│                                                             [Cancel]  [Save]│
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

# Form Structure

```text
Edit Job

├── Title (Optional)
├── Role (Optional)
├── Company (Optional)
├── Location (Optional)
├── Job Post URL *
├── Work Type
├── Employment Type
├── Visa (Optional)
├── Salary (Optional)
├── Notes
├── Additional Links
├── Description
├── Tags
```

---

# Editable Fields

| Field           | Required | Type     |
| --------------- | -------- | -------- |
| Title           | No       | text     |
| Role            | No       | text     |
| Company         | No       | text     |
| Location        | No       | text     |
| Job Post URL    | **Yes**  | url      |
| Work Type       | No       | select   |
| Employment Type | No       | select   |
| Visa            | No       | text     |
| Salary          | No       | text     |
| Notes           | No       | note list |
| Additional Links| No       | link list |
| Description     | No       | textarea |
| Tags            | No       | tag list |

---

# Job Post URL

The primary source of the Job. This is the only required field.

Requirements

- Required
- Must be a valid URL
- Existing value is pre-filled
- Leaving it unchanged is allowed

---

# Work Type

Select from a fixed set.

Options

- On-site
- Remote
- Hybrid

---

# Employment Type

Select from a fixed set.

Options

- Full-time
- Part-time
- Contract
- Internship
- Temporary

---

# Notes

Existing notes are pre-filled as a list. Each note is rendered with an optional title.

Users can add a note, or remove an existing one with the **×** button.

```text
Notes
[note 1]  [×]
[note 2]  [×]
┌────────────────────────────────┐  [+]
│ Add a note...                │
└────────────────────────────────┘
```

- Adding a note appends it to the list.
- Removing a note deletes it from the list.
- Changes are only persisted on **Save**.

---

# Additional Links

Existing links are pre-filled as a list of URLs with optional titles.

Users can add a link (URL + optional title), or remove an existing one with the **×** button.

```text
Additional Links
🔗 https://company.com/careers  [×]
┌───────────────────────────┐ ┌──────────────┐  [+]
│ Link URL (https://...)    │ │ Title (opt.) │
└───────────────────────────┘ └──────────────┘
```

- Every link URL must start with `http://` or `https://`.
- Adding a link appends it; the **＋** button is disabled until a valid URL is entered.
- Removing is immediate in the form.
- Changes are only persisted on **Save**.

---

# Description

Optional textarea for the job description.

---

# Tags

Existing tags are pre-filled as a list of removable badges.

Users can add a tag (free-form string), or remove an existing one with the
**×** button. Pressing Enter in the input also adds the tag.

```text
Tags
[python] [×]  [remote] [×]
┌────────────────────────────────┐  [+]
│ Add a tag...                   │
└────────────────────────────────┘
```

- Tags are free-form strings (no predefined set).
- Duplicate tags are prevented.
- Adding a tag appends it to the list.
- Removing a tag deletes it from the list.
- Changes are only persisted on **Save**.

---

# Validation

## Job Post URL

- Required
- Must be a valid URL

## Other fields

- Optional
- Blank values clear the field unless it is the URL

---

# Actions

| Action | Description                          |
| ------ | ------------------------------------ |
| Save   | Persist changes and close the Drawer |
| Cancel | Close the Drawer without saving      |
| Close  | Close the Drawer (same as Cancel)    |

---

# States

## Loading

The drawer fetches the job detail before showing the form.

A loading indicator is displayed.

---

## Default (Prefill)

The form is populated with the job's current values.

---

## Editing

The user is entering information.

---

## Submitting

- The Dropdown is disabled.
- A loading indicator is shown on the Save button.

---

## Success

- Changes are persisted.
- The Drawer closes.
- The affected Job Row refreshes with the new values.

---

## Error

- Validation errors are displayed.
- Previously entered values are preserved.
- The Drawer remains open.

---

# User Flow

```text
Open Jobs Page

↓

Click Edit on a Job Row

↓

Edit Job Drawer opens, pre-filled

↓

Update fields

↓

Save

↓

Changes Persisted

↓

Row refreshed with new values

↓

Drawer closes
```

---

# Responsive Behavior

## Desktop

- Medium Drawer (`md`)

## Tablet

- Medium Drawer (`md`)

## Mobile

- Full-screen Drawer

---

# Accessibility

- Keyboard navigation
- Focus trap
- Escape closes the Drawer
- Screen-reader labels
- Required field announced
- Validation messages associated with their inputs

---

# Related Documents

- `pages/jobs.md`
- `job-row.md`
- `add-job.md`
- `design-system/drawer.md`
- `flows/jobs/edit-job.md`
