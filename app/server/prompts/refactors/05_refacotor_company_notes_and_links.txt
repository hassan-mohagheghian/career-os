
Improve the company notes and links management system.

The goal is to create a cleaner and more structured input system for company information before processing. Users should be able to provide company context through free-form notes and dedicated links, and the processing pipeline should use both sources.

---

# Backend Changes

## 1. Refactor Company Notes Structure

Currently, company information is stored as notes where users can write text and include links.

Refactor this into a more structured model:

A company can have:

1. Company Notes
2. Company Links


---

# Company Notes

Notes are free-form user inputs.

Users can write:

- Company information
- Personal research
- Observations
- Interview notes
- Culture information
- Product information
- Any relevant context


Requirements:

- Support multiple notes per company.
- Each note should have:
  - id
  - content
  - created_at
  - updated_at


Notes may still contain URLs inside the text.

Do not restrict users from adding links inside notes.

---

# Company Links

Create a dedicated link entity.

Each link should have:

- id
- company_id
- url
- title (optional)
- description (optional)
- status
- created_at
- updated_at


The purpose of links:

- Store official company pages
- Careers pages
- Blog posts
- Documentation
- News articles
- LinkedIn/company profiles
- Any useful external sources


---

# Processing Integration

During company processing:

Use both:

1. Company Notes
2. Company Links


Processing workflow:

Company Notes
        +
Company Links
        |
        v
Extract information from links
        |
        v
Combine with user notes
        |
        v
Generate company intelligence


For every company link:

- Try to fetch the content.
- Extract useful text.
- Store extracted information separately from the original URL.
- Use extracted content during company analysis.

Do not modify the original user input.

Keep:

Original data:
- Notes
- URLs

Separated from:

Processed data:
- Extracted content
- AI-generated company intelligence


---

# Frontend Changes

Improve the company creation and editing experience.

## Company Input Section

Create a cleaner UI with two sections:

---

## Section 1: Notes

Features:

- Add new note
- Edit note
- Delete note
- Multiple notes support


The note editor should:

- Use a larger textarea/editor
- Provide enough space for long text
- Be visually optimized for editing
- Support multiline content


Example:

Company Notes

[ + Add Note ]

--------------------------------
|                                |
|  Large editable text area      |
|                                |
--------------------------------

Actions:
Edit | Save | Delete


---

## Section 2: Links

Add a dedicated links manager.

Features:

- Add link
- Edit link
- Delete link


Each link item should show:

- URL
- Optional title
- Processing status


Example:

Company Links

[ + Add Link ]

--------------------------------
https://company.com/careers

Status:
Pending / Processed / Failed

Actions:
Edit | Delete
--------------------------------


---

# Consistent UX

Notes and Links should have the same interaction pattern:

- Add
- Edit
- Delete
- Save
- Cancel


Keep the UI consistent with the existing Jobs page style.

---

# Company Drawer Improvements

Inside the company drawer:

Show original inputs separately:

## Original Notes

Display all user notes.

Allow:
- Edit
- Delete
- Add new notes


## Original Links

Display all company links.

Allow:
- Edit
- Delete
- Add new links


Provide:

"Reprocess Company"

button.

When clicked:

- Re-run link extraction.
- Re-run company intelligence processing.
- Recalculate company scores.

---

# Requirements

- Keep backward compatibility with existing company notes.
- Existing companies should not lose their data.
- Existing notes containing URLs should continue working.
- Separate user input from AI-generated information.
- Design the structure for future expansion:
  - More source types
  - Documents
  - PDFs
  - Social profiles
  - Research materials

The final system should provide a clean knowledge collection workflow before company intelligence processing.
