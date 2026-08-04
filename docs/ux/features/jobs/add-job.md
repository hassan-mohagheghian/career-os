# Add Job Drawer

## Purpose

The Add Job Drawer allows users to create a new Job by providing the primary job posting URL, optional job information, additional reference links, and optional notes.

The drawer is opened from the **Jobs** page without leaving the current workspace.

A newly created Job can either:

- Be added to the Jobs list only.
- Be added to the Jobs list and immediately placed into the Processing Queue.

---

# Related Page

Opened from:

- `pages/jobs.md`

Uses:

- `design-system/drawer.md`

---

# Drawer

- Sheet (right side), width `400px` desktop / `480px` larger screens — same reference layout as Job Details and Edit Job drawers
- Placement: `right`

---

# User Goals

The user should be able to:

- Import a new Job
- Provide the primary Job Post URL
- Optionally specify the Job Title
- Attach additional reference links
- Attach raw notes
- Choose whether processing should start immediately

---

# Layout

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ Add Job                                                          [Close]   │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│ Job Post URL *                                                             │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ https://...                                                           │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│ Job Title (Optional)                                                      │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ Senior Backend Engineer                                                │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│────────────────────────────────────────────────────────────────────────────│
│                                                                            │
│ Additional Links                                                           │
│                                                                            │
│ No additional links                                                        │
│                                                                            │
│                           [+ Add Link]                                     │
│                                                                            │
│────────────────────────────────────────────────────────────────────────────│
│                                                                            │
│ Notes                                                                      │
│                                                                            │
│ No notes                                                                   │
│                                                                            │
│                           [+ Add Note]                                     │
│                                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                           [Cancel]                                         │
│             [Create Job]        [Create & Queue]                           │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

# Form Structure

```text
Add Job

├── Job Post URL *
├── Job Title (Optional)
├── Additional Links
└── Notes
```

---

# Job Post URL

The Job Post URL is the primary source of the Job.

This is the only required field.

Requirements

- Required
- Must be a valid URL

Examples

- LinkedIn Job
- Company Careers Page
- Greenhouse
- Lever
- Workday
- Ashby

---

# Job Title

Optional.

If left empty, the processing pipeline should automatically extract the title from the Job Post URL.

Examples

- Senior Backend Engineer
- Python Developer
- Staff Software Engineer

---

# Additional Links

Additional Links provide extra sources that may help processing.

This section starts empty.

```text
No additional links

                     [+ Add Link]
```

Selecting **Add Link** creates one new link item.

---

# Additional Link Item

```text
Title (Optional)

┌──────────────────────────────────────────────────────────┐
│ LinkedIn Profile                                         │
└──────────────────────────────────────────────────────────┘

URL *

┌──────────────────────────────────────────────────────────┐
│ https://...                                              │
└──────────────────────────────────────────────────────────┘

                                                [Remove]
```

Fields

| Field | Required |
| ----- | -------- |
| Title | No       |
| URL   | Yes      |

Example titles

- LinkedIn
- Company Website
- Recruiter Message
- Glassdoor
- Indeed
- Salary Page
- Engineering Blog

Rules

- URL is required.
- Title is optional.
- Empty items are not allowed.
- Remove unused items.

---

# Notes

Notes provide raw copied text that may help processing if the original pages become unavailable.

This section starts empty.

```text
No notes

                     [+ Add Note]
```

Selecting **Add Note** creates one new note item.

---

# Note Item

```text
Title (Optional)

┌──────────────────────────────────────────────────────────┐
│ Requirements                                              │
└──────────────────────────────────────────────────────────┘

Content *

┌──────────────────────────────────────────────────────────┐
│ Raw copied text...                                       │
│                                                          │
│                                                          │
└──────────────────────────────────────────────────────────┘

                                                [Remove]
```

Fields

| Field   | Required |
| ------- | -------- |
| Title   | No       |
| Content | Yes      |

Example titles

- Requirements
- Benefits
- Salary
- Company Description
- Personal Notes

Rules

- Content is required.
- Title is optional.
- Empty note items are not allowed.
- Remove unused items.

---

# Validation

## Job Post URL

- Required
- Must be a valid URL

---

## Job Title

- Optional

---

## Additional Links

- URL is required
- Title is optional

---

## Notes

- Content is required
- Title is optional

---

# Actions

| Action         | Description                                                     |
| -------------- | --------------------------------------------------------------- |
| Create Job     | Create a Job and add it to the Jobs list                        |
| Create & Queue | Create a Job and immediately place it into the Processing Queue |
| Cancel         | Close the Drawer                                                |
| Add Link       | Append a new Additional Link                                    |
| Remove Link    | Remove one Additional Link                                      |
| Add Note       | Append a new Note                                               |
| Remove Note    | Remove one Note                                                 |

---

# States

## Default

Empty form.

---

## Editing

The user is entering information.

---

## Submitting

The form becomes read-only.

A loading indicator is displayed.

---

## Success (Create Job)

- Drawer closes.
- Job appears in the Jobs list.
- Status = **Imported**

---

## Success (Create & Queue)

- Drawer closes.
- Job appears in the Jobs list.
- Status = **Queued**
- Job is added to the Processing Queue.
- The Processing Queue drawer opens so the live workflow progress is visible immediately (instant processing workflow).
- The job's status transitions Queued → Running → Completed/Failed as the LangGraph job-processing workflow executes, streamed over SSE.

---

## Error

- Validation errors are displayed.
- Previously entered values are preserved.

---

# User Flow

## Create Job

```text
Open Drawer

↓

Enter Job Post URL

↓

(Optional)

Enter Job Title

↓

(Optional)

Add Additional Links

↓

(Optional)

Add Notes

↓

Create Job

↓

Job Created

↓

Status = Imported
```

---

## Create & Queue

```text
Open Drawer

↓

Enter Job Post URL

↓

(Optional)

Enter Job Title

↓

(Optional)

Add Additional Links

↓

(Optional)

Add Notes

↓

Create & Queue

↓

Job Created

↓

Status = Queued

↓

Added to Processing Queue

↓

Processing Queue drawer opens

↓

Instant workflow runs (fetch → extract → analyze → score → persist)

↓

Live progress streamed over SSE
```

---

# Responsive Behavior

## Desktop

- Right Sheet (`400px`)

## Tablet

- Right Sheet (`400px`)

## Mobile

- Right Sheet (`480px`)
- Full-height sheet

---

# Accessibility

- Keyboard navigation
- Focus trap
- Escape closes Drawer
- Screen-reader labels
- Required fields announced
- Validation messages associated with their inputs

---

# Related Documents

- `pages/jobs.md`
- `design-system/drawer.md`
