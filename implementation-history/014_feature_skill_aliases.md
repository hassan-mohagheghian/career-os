Implement skill normalization with a two-table design.

Initially, every extracted or custom item is stored as a Skill.

When two skills are detected as duplicates or equivalent (for example:
"PostgreSQL" and "Postgres"), they need to be merged.

The merge behavior:

- The selected primary skill remains in the `skills` table as the canonical skill.
- The skill that is moved/merged becomes an alias record.
- The alias keeps its original name but is linked to the canonical skill.
- Do not delete the moved skill data; preserve it as an alias.

Database design:

Table: skills

Fields:
- id
- name
- normalized_name
- description (optional)
- category (optional)
- created_at
- updated_at


Table: skill_aliases

Fields:
- id
- skill_id (foreign key to skills.id)
- alias_name
- normalized_name
- created_at


Example:

Before merge:

skills:
1 | PostgreSQL
2 | Postgres


After merge:

skills:
1 | PostgreSQL


skill_aliases:
1 | skill_id=1 | Postgres


Rules:

- The canonical skill is always stored in the `skills` table.
- Alias records are only created after a merge operation.
- A skill can have multiple aliases.
- A canonical skill can be displayed with its aliases in UI.
- The UI should show:
    PostgreSQL
    [2 aliases]

  Expanded:
    Also known as:
    Postgres, PGSQL

- When matching jobs, resumes, or extracted skills:
    aliases should resolve to the canonical skill.

Example:
"Postgres experience required"
should match:
Canonical skill = PostgreSQL
