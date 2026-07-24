/**
 * Domain: Skill category resolution.
 *
 * A skill's category is determined by looking up its metadata from the
 * tech_stack table first. When the skill only exists in the AI-generated
 * report (strengths / gaps / recommendations) but not in tech_stack, we
 * fall back to the category the AI assigned.
 */

/**
 * Resolve the category for a skill name.
 *
 * @param {string} name - Skill name to look up.
 * @param {Array} techStackSkills - Rows from the tech_stack table.
 * @param {Object} aiReport - { strengths: [], gaps: [], learningRecommendations: [] }
 * @returns {string|undefined} Category string or undefined if unknown.
 */
export function resolveSkillCategory(name, techStackSkills, aiReport = {}) {
  const fromStack = techStackSkills.find((s) => s.name === name);
  if (fromStack?.category) return fromStack.category;

  const { strengths = [], gaps = [], learningRecommendations: recs = [] } = aiReport;

  const fromStrengths = strengths.find((s) => s.skill === name);
  if (fromStrengths?.category) return fromStrengths.category;

  const fromGaps = gaps.find((g) => g.skill === name);
  if (fromGaps?.category) return fromGaps.category;

  const fromRecs = recs.find((r) => r.skill === name);
  if (fromRecs?.category) return fromRecs.category;

  return undefined;
}

/**
 * Filter a list of skill items (strengths, gaps, or recs) by active category,
 * using resolveSkillCategory as the single source of truth.
 *
 * @param {Array} items - Array of { skill, category?, ... }
 * @param {string} activeCategory - The tab/category to filter by.
 * @param {Array} techStackSkills - tech_stack rows.
 * @param {Object} aiReport - AI report data.
 * @returns {Array} Filtered items.
 */
export function filterByCategory(items, activeCategory, techStackSkills, aiReport) {
  return items.filter((item) => {
    const cat = resolveSkillCategory(item.skill, techStackSkills, aiReport);
    return cat === activeCategory;
  });
}
