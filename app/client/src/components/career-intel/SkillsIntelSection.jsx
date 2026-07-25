import { useState, useEffect, useCallback, useMemo } from "react";
import {
  TrendUp, Brain, BookOpen, Wrench, ArrowsClockwise, Target,
  TreeStructure, Plus, User, EyeSlash, DotsSixVertical, GitMerge,
  Eye, CaretDown, CaretRight, FunnelSimple, SortAscending, Trash,
} from "@phosphor-icons/react";
import { cn } from "@/lib/utils";
import { resolveSkillCategory } from "@/lib/skills";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from "@dnd-kit/core";
import { SortableContext, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import GenerationProgressCard from "@/components/shared/GenerationProgressCard";
import SkillRoadmapDrawer from "./SkillRoadmapDrawer";
import SkillDetailDrawer from "./SkillDetailDrawer";

const API = "/api";

const CATEGORIES = [
  { id: "technical", label: "Technical", icon: <Wrench className="w-3 h-3" /> },
  { id: "engineering", label: "Engineering", icon: <Target className="w-3 h-3" /> },
  { id: "professional", label: "Professional", icon: <User className="w-3 h-3" /> },
  { id: "domain", label: "Domain", icon: <BookOpen className="w-3 h-3" /> },
  { id: "career", label: "Career", icon: <TrendUp className="w-3 h-3" /> },
];

const CATEGORY_COLORS = {
  technical: "bg-blue-500/15 text-blue-500",
  engineering: "bg-green-500/15 text-green-500",
  professional: "bg-purple-500/15 text-purple-500",
  domain: "bg-yellow-500/15 text-yellow-500",
  career: "bg-cyan-500/15 text-cyan-500",
};

const SORT_OPTIONS = [
  { id: "strength", label: "Strength" },
  { id: "roadmap", label: "Roadmap Progress" },
  { id: "name", label: "Name" },
  { id: "demand", label: "Market Demand" },
];

const ROLE_FILTERS = [
  { id: "all", label: "All Roles" },
  { id: "strength", label: "Strengths" },
  { id: "gap", label: "Gaps" },
  { id: "rec", label: "Recommendations" },
  { id: "none", label: "No Tag" },
];

const SOURCE_FILTERS = [
  { id: "all", label: "All Sources" },
  { id: "custom", label: "Custom" },
  { id: "ai", label: "AI-Detected" },
];

const ROADMAP_FILTERS = [
  { id: "all", label: "All Roadmaps" },
  { id: "yes", label: "Has Roadmap" },
  { id: "no", label: "No Roadmap" },
];

// ── Sortable skill row ────────────────────────────────────────
function SortableSkillRow({ id, name, category, confidence, source, marketDemand, tags, onClick, onHide, onRemove, mergeMode, extra, aliases = [], skillId }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 10 : 0,
  };

  return (
    <>
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        "flex items-center gap-1.5 p-1.5 rounded transition text-xs",
        isDragging ? "bg-primary/10 shadow-md" : "hover:bg-muted",
        mergeMode ? "cursor-grab" : "cursor-pointer",
      )}
      onClick={() => !mergeMode && onClick?.(name)}
    >
      {mergeMode && (
        <button {...attributes} {...listeners} className="shrink-0 cursor-grab active:cursor-grabbing">
          <DotsSixVertical className="w-3 h-3 text-muted-foreground" />
        </button>
      )}
      <span className="font-semibold w-16 truncate shrink-0">{name}</span>
      {category && (
        <Badge variant="secondary" className={cn("text-[0.4rem] h-2.5 shrink-0", CATEGORY_COLORS[category] || "bg-gray-500/15 text-gray-400")}>
          {category}
        </Badge>
      )}
      {/* Source + Role tags */}
      {tags.map((tag) => (
        <Badge key={tag.label} variant="secondary" className={cn("text-[0.35rem] h-2 shrink-0", tag.color)}>
          {tag.label}
        </Badge>
      ))}
      {marketDemand > 0 && (
        <>
          <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden min-w-[40px]">
            <div className="h-full bg-primary/60 rounded-full" style={{ width: `${marketDemand}%` }} />
          </div>
          <span className="w-6 text-right text-[0.5rem] text-muted-foreground shrink-0">{marketDemand}%</span>
        </>
      )}
      {confidence > 0 && (
        <div className="flex items-center gap-1 shrink-0">
          <div className="w-6 h-1 bg-muted rounded-full overflow-hidden">
            <div className="h-full bg-primary rounded-full" style={{ width: `${confidence * 100}%` }} />
          </div>
        </div>
      )}
      {extra}
      {!mergeMode && (
        <div className="flex items-center gap-0.5 shrink-0">
          {onHide && (
            <button
              onClick={(e) => { e.stopPropagation(); onHide(name); }}
              className="p-0.5 rounded hover:bg-yellow-500/10 text-muted-foreground hover:text-yellow-500 transition"
              title="Hide"
            >
              <EyeSlash className="w-2.5 h-2.5" />
            </button>
          )}
          {onRemove && (
            <button
              onClick={(e) => { e.stopPropagation(); onRemove(name, skillId); }}
              className="p-0.5 rounded hover:bg-red-500/10 text-muted-foreground hover:text-red-500 transition"
              title="Remove"
            >
              <Trash className="w-2.5 h-2.5" />
            </button>
          )}
        </div>
      )}
    </div>
    {aliases.length > 0 && (
      <div className="flex items-center gap-1 ml-6 pl-2 border-l-2 border-muted">
        <Badge variant="secondary" className="text-[0.35rem] h-2 bg-amber-500/15 text-amber-600 shrink-0">Variant</Badge>
        <span className="text-[0.5rem] text-muted-foreground truncate">
          {aliases.join(", ")}
        </span>
      </div>
    )}
    </>
  );
}

// ── Main component ─────────────────────────────────────────────
export default function SkillsIntelSection({
  data, refreshing, onRefresh, roadmapProgress, onRefreshProgress, genJobs = [],
}) {
  const skills = data?.skills || {};
  const strengths = skills.strengths || [];
  const gaps = skills.gaps || [];
  const recommendations = skills.learningRecommendations || [];

  const [selectedSkill, setSelectedSkill] = useState(null);
  const [detailSkill, setDetailSkill] = useState(null);
  const [customSkillInput, setCustomSkillInput] = useState("");
  const [techStackSkills, setTechStackSkills] = useState([]);
  const [hiddenSkills, setHiddenSkills] = useState([]);
  const [mergeMode, setMergeMode] = useState(false);
  const [activeCategory, setActiveCategory] = useState("technical");
  const [showHidden, setShowHidden] = useState(false);
  const [showAddSkill, setShowAddSkill] = useState(false);
  const [sortBy, setSortBy] = useState("strength");
  const [roleFilter, setRoleFilter] = useState("all");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [roadmapFilter, setRoadmapFilter] = useState("all");

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }));

  const fetchTechStack = useCallback(() => {
    fetch(`${API}/tech-stack`).then((r) => r.json()).then((list) => setTechStackSkills(Array.isArray(list) ? list : [])).catch(() => {});
  }, []);

  const fetchHidden = useCallback(() => {
    fetch(`${API}/tech-stack/hidden`).then((r) => r.json()).then((list) => setHiddenSkills(Array.isArray(list) ? list : [])).catch(() => {});
  }, []);

  useEffect(() => { fetchTechStack(); fetchHidden(); }, [fetchTechStack, fetchHidden, roadmapProgress]);

  // Build alias map
  const aliasMap = useMemo(() => {
    const map = {};
    for (const s of techStackSkills) {
      if (s.aliases && s.aliases.length > 0) map[s.name] = s.aliases;
    }
    return map;
  }, [techStackSkills]);

  const aiReport = useMemo(() => ({ strengths, gaps, learningRecommendations: recommendations }), [strengths, gaps, recommendations]);

  // Build lookup sets for AI tags
  const strengthSet = useMemo(() => new Set(strengths.map((s) => s.skill)), [strengths]);
  const gapSet = useMemo(() => new Set(gaps.map((g) => g.skill)), [gaps]);
  const recSet = useMemo(() => new Set(recommendations.map((r) => r.skill)), [recommendations]);

  // Category counts from tech_stack
  const categoryCounts = useMemo(() => {
    const counts = {};
    for (const s of techStackSkills) { const cat = s.category || "technical"; counts[cat] = (counts[cat] || 0) + 1; }
    return counts;
  }, [techStackSkills]);

  // ── Build unified skill list ──
  const unifiedSkills = useMemo(() => {
    const seen = new Set();
    const list = [];

    for (const stack of techStackSkills) {
      if (seen.has(stack.name)) continue;
      seen.add(stack.name);

      const inStrengths = strengthSet.has(stack.name);
      const inGaps = gapSet.has(stack.name);
      const inRecs = recSet.has(stack.name);
      const prog = roadmapProgress[stack.name];
      const isCustom = stack.source === "user";

      // Build tags
      const tags = [];
      if (isCustom) tags.push({ label: "Custom", color: "bg-purple-500/15 text-purple-500" });
      else tags.push({ label: "AI", color: "bg-blue-500/15 text-blue-500" });
      if (inStrengths) tags.push({ label: "Strength", color: "bg-green-500/15 text-green-500" });
      if (inGaps) tags.push({ label: "Gap", color: "bg-red-500/15 text-red-500" });
      if (inRecs) tags.push({ label: "Rec", color: "bg-primary/15 text-primary" });

      list.push({
        name: stack.name,
        category: stack.category || "technical",
        source: stack.source,
        confidence: stack.confidence || 0,
        marketDemand: stack.market_relevance || 0,
        level: stack.level || 0,
        skillId: stack.id,
        aliases: aliasMap[stack.name] || [],
        tags,
        inStrengths,
        inGaps,
        inRecs,
        isCustom,
        hasRoadmap: prog?.total > 0,
        roadmapPct: prog?.pct || 0,
        roadmapCompleted: prog?.completed || 0,
        roadmapTotal: prog?.total || 0,
        strengthOrder: inStrengths ? 0 : inGaps ? 1 : inRecs ? 2 : 3,
      });
    }
    return list;
  }, [techStackSkills, strengthSet, gapSet, recSet, roadmapProgress, aliasMap]);

  // ── Filter + Sort ──
  const displayedSkills = useMemo(() => {
    let result = unifiedSkills;

    // Category filter
    result = result.filter((s) => s.category === activeCategory);

    // Source filter
    if (sourceFilter === "custom") result = result.filter((s) => s.isCustom);
    else if (sourceFilter === "ai") result = result.filter((s) => !s.isCustom);

    // Role filter
    if (roleFilter === "strength") result = result.filter((s) => s.inStrengths);
    else if (roleFilter === "gap") result = result.filter((s) => s.inGaps);
    else if (roleFilter === "rec") result = result.filter((s) => s.inRecs);
    else if (roleFilter === "none") result = result.filter((s) => !s.inStrengths && !s.inGaps && !s.inRecs);

    // Roadmap filter
    if (roadmapFilter === "yes") result = result.filter((s) => s.hasRoadmap);
    else if (roadmapFilter === "no") result = result.filter((s) => !s.hasRoadmap);

    // Sort
    result = [...result].sort((a, b) => {
      switch (sortBy) {
        case "strength": return a.strengthOrder - b.strengthOrder;
        case "roadmap": return (b.hasRoadmap ? b.roadmapPct : -1) - (a.hasRoadmap ? a.roadmapPct : -1);
        case "name": return a.name.localeCompare(b.name);
        case "demand": return b.marketDemand - a.marketDemand;
        default: return a.strengthOrder - b.strengthOrder;
      }
    });

    return result;
  }, [unifiedSkills, activeCategory, sourceFilter, roleFilter, roadmapFilter, sortBy]);

  // ── Handlers ──
  const handleAddCustomSkill = async () => {
    const name = customSkillInput.trim();
    if (!name) return;
    try {
      await fetch(`${API}/tech-stack`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, level: 1, source: "user", source_type: "user_input", category: activeCategory }),
      });
      setCustomSkillInput(""); fetchTechStack(); if (onRefreshProgress) onRefreshProgress();
      toast.success(`"${name}" added to ${activeCategory}`);
    } catch {}
  };

  const handleHideSkill = async (skillName) => {
    const item = techStackSkills.find((s) => s.name === skillName);
    if (!item) return;
    try {
      await fetch(`${API}/tech-stack/${item.id}/hide`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ hidden: 1 }) });
      toast.success(`"${skillName}" hidden`); fetchTechStack(); fetchHidden();
    } catch { toast.error("Failed to hide skill"); }
  };

  const handleRemoveSkill = async (skillName, skillId) => {
    if (!skillId) return;
    const aliases = aliasMap[skillName] || [];
    const msg = aliases.length > 0
      ? `Remove "${skillName}" and its ${aliases.length} alias${aliases.length > 1 ? "es" : ""} (${aliases.join(", ")})?`
      : `Remove "${skillName}"?`;
    if (!window.confirm(msg)) return;
    try {
      const res = await fetch(`${API}/tech-stack/${skillId}`, { method: "DELETE" });
      const result = await res.json();
      if (res.ok) {
        toast.success(`"${skillName}" removed${result.aliases_deleted?.length ? ` with ${result.aliases_deleted.length} alias${result.aliases_deleted.length > 1 ? "es" : ""}` : ""}`);
        fetchTechStack(); fetchHidden(); if (onRefreshProgress) onRefreshProgress();
      } else {
        toast.error(result.error || "Failed to remove");
      }
    } catch { toast.error("Failed to remove skill"); }
  };

  const handleRestoreSkill = async (skillName) => {
    const item = hiddenSkills.find((s) => s.name === skillName);
    if (!item) return;
    try {
      await fetch(`${API}/tech-stack/${item.id}/restore`, { method: "PATCH" });
      toast.success(`"${skillName}" restored`); fetchTechStack(); fetchHidden();
    } catch { toast.error("Failed to restore skill"); }
  };

  const handleDragEnd = async (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const sourceItem = techStackSkills.find((s) => s.name === active.id);
    const targetItem = techStackSkills.find((s) => s.name === over.id);
    if (!sourceItem || !targetItem) return;
    if (!window.confirm(`Merge "${sourceItem.name}" into "${targetItem.name}"?`)) return;
    try {
      const res = await fetch(`${API}/tech-stack/merge`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_id: targetItem.id, source_ids: [sourceItem.id] }),
      });
      const result = await res.json();
      if (result.status === "merged") {
        const aliasCount = result.aliases?.length || 0;
        toast.success(
          aliasCount > 0
            ? `Merged "${sourceItem.name}" → "${targetItem.name}" (${aliasCount} alias${aliasCount > 1 ? "es" : ""})`
            : `Merged "${sourceItem.name}" → "${targetItem.name}"`
        );
        fetchTechStack(); fetchHidden(); if (onRefreshProgress) onRefreshProgress();
      }
    } catch { toast.error("Failed to merge skills"); }
  };

  // Build roadmap extra for a skill
  const getRoadmapExtra = (skill) => {
    if (skill.hasRoadmap) {
      return (
        <>
          <div className="flex-1 min-w-[60px]"><Progress value={skill.roadmapPct} className="h-1.5" /></div>
          <span className="text-[0.6rem] text-muted-foreground w-10 text-right shrink-0">{skill.roadmapCompleted}/{skill.roadmapTotal}</span>
          <Badge variant="secondary" className={cn("text-[0.45rem] h-3 shrink-0",
            skill.roadmapPct === 100 ? "bg-green-500/15 text-green-500" : skill.roadmapPct > 0 ? "bg-emerald-500/15 text-emerald-500" : "bg-gray-500/15 text-gray-400"
          )}>{skill.roadmapPct}%</Badge>
        </>
      );
    }
    return (
      <>
        <span className="text-[0.6rem] text-muted-foreground flex-1">No roadmap</span>
        <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); setSelectedSkill(skill.name); }}
          className="h-5 text-[0.5rem] gap-0.5"><TreeStructure className="w-2.5 h-2.5" /> Generate</Button>
      </>
    );
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-extrabold text-sm">Skills Intelligence</h3>
        <div className="flex items-center gap-2">
          <Button variant={mergeMode ? "default" : "ghost"} size="sm" onClick={() => setMergeMode(!mergeMode)}
            className={cn("gap-1 h-6 text-[0.55rem]", mergeMode && "bg-primary/20")}>
            <GitMerge className="w-3 h-3" /> {mergeMode ? "Exit Merge" : "Merge"}
          </Button>
          <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.skills} className="gap-1 h-6 text-[0.55rem]">
            <ArrowsClockwise className={cn("w-3 h-3", refreshing.skills && "animate-spin")} /> Refresh
          </Button>
        </div>
      </div>

      {mergeMode && (
        <div className="rounded-lg border border-dashed border-primary/40 bg-primary/5 p-2 text-[0.6rem] text-muted-foreground">
          <strong className="text-foreground">Merge Mode</strong> — Drag any skill onto another. Target keeps its name, source is absorbed.
        </div>
      )}

      {/* Category Tabs + Add Skill */}
      <div className="flex items-center gap-2">
        <Tabs value={activeCategory} onValueChange={setActiveCategory} className="flex-1">
          <TabsList className="bg-muted">
            {CATEGORIES.map((cat) => (
              <TabsTrigger key={cat.id} value={cat.id} className="gap-1.5 text-[0.6rem]">
                {cat.icon} {cat.label}
                {categoryCounts[cat.id] > 0 && (
                  <Badge variant="secondary" className="text-[0.4rem] h-3 ml-0.5">{categoryCounts[cat.id]}</Badge>
                )}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
        <div className="flex items-center gap-1.5 shrink-0">
          {showAddSkill && (
            <>
              <Input value={customSkillInput} onChange={(e) => setCustomSkillInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAddCustomSkill()}
                placeholder={`Skill name for ${activeCategory}...`} className="h-7 text-[0.65rem] w-56" autoFocus />
              <Button size="sm" variant="default" onClick={handleAddCustomSkill} disabled={!customSkillInput.trim()}
                className="h-7 gap-1 text-[0.6rem] shrink-0 bg-emerald-600 hover:bg-emerald-700">
                <Plus className="w-3 h-3" /> Add
              </Button>
            </>
          )}
          <Button size="sm" variant={showAddSkill ? "ghost" : "outline"} onClick={() => { setShowAddSkill(!showAddSkill); if (showAddSkill) setCustomSkillInput(""); }}
            className="h-7 gap-1 text-[0.6rem] shrink-0">
            <Plus className="w-3 h-3" /> {showAddSkill ? "Close" : "Add Skill"}
          </Button>
        </div>
      </div>

      {/* Sort + Filter bar */}
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex items-center gap-1">
          <SortAscending className="w-3 h-3 text-muted-foreground" />
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="h-6 text-[0.6rem] w-32"><SelectValue /></SelectTrigger>
            <SelectContent>
              {SORT_OPTIONS.map((opt) => <SelectItem key={opt.id} value={opt.id} className="text-[0.6rem]">{opt.label}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-1">
          <FunnelSimple className="w-3 h-3 text-muted-foreground" />
          <Select value={roleFilter} onValueChange={setRoleFilter}>
            <SelectTrigger className="h-6 text-[0.6rem] w-32"><SelectValue /></SelectTrigger>
            <SelectContent>
              {ROLE_FILTERS.map((opt) => <SelectItem key={opt.id} value={opt.id} className="text-[0.6rem]">{opt.label}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <Select value={sourceFilter} onValueChange={setSourceFilter}>
          <SelectTrigger className="h-6 text-[0.6rem] w-28"><SelectValue /></SelectTrigger>
          <SelectContent>
            {SOURCE_FILTERS.map((opt) => <SelectItem key={opt.id} value={opt.id} className="text-[0.6rem]">{opt.label}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={roadmapFilter} onValueChange={setRoadmapFilter}>
          <SelectTrigger className="h-6 text-[0.6rem] w-32"><SelectValue /></SelectTrigger>
          <SelectContent>
            {ROADMAP_FILTERS.map((opt) => <SelectItem key={opt.id} value={opt.id} className="text-[0.6rem]">{opt.label}</SelectItem>)}
          </SelectContent>
        </Select>
        <Badge variant="secondary" className="text-[0.5rem] h-4">{displayedSkills.length} skills</Badge>
      </div>

      {/* ═══ Global DnD Context ═══ */}
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>

        {/* ═══ Unified Skills Card ═══ */}
        <Card className="p-4">
          {genJobs.length > 0 && genJobs.map((job) => (
            <div key={job.skill} className="cursor-pointer mb-2" onClick={() => setSelectedSkill(job.skill)}>
              <GenerationProgressCard title={job.skill} progress={{ running: true, ...job }} compact />
            </div>
          ))}
          <SortableContext items={displayedSkills.map((s) => s.name)} strategy={verticalListSortingStrategy}>
            <div className="space-y-0.5 max-h-[500px] overflow-y-auto">
              {displayedSkills.length > 0 ? displayedSkills.map((skill) => (
                <SortableSkillRow
                  key={skill.name}
                  id={skill.name}
                  name={skill.name}
                  category={skill.category}
                  confidence={skill.confidence}
                  source={skill.source}
                  marketDemand={skill.marketDemand}
                  tags={skill.tags}
                  onClick={(n) => setDetailSkill(n)}
                  onHide={handleHideSkill}
                  onRemove={handleRemoveSkill}
                  mergeMode={mergeMode}
                  aliases={skill.aliases}
                  skillId={skill.skillId}
                  extra={getRoadmapExtra(skill)}
                />
              )) : (
                <div className="text-xs text-muted-foreground text-center py-8">
                  No skills match the current filters
                </div>
              )}
            </div>
          </SortableContext>
        </Card>

        {/* Hidden Skills — collapsed, at the end */}
        {hiddenSkills.length > 0 && (
          <Card className="p-4 mt-4">
            <button onClick={() => setShowHidden(!showHidden)} className="flex items-center gap-2 mb-2 w-full text-left">
              {showHidden ? <CaretDown className="w-4 h-4" /> : <CaretRight className="w-4 h-4" />}
              <EyeSlash className="w-4 h-4 text-gray-500" />
              <h4 className="font-extrabold text-sm">Hidden Skills</h4>
              <Badge variant="secondary" className="text-[0.5rem] bg-gray-500/15 text-gray-500">{hiddenSkills.length}</Badge>
            </button>
            {showHidden && (
              <SortableContext items={hiddenSkills.map((s) => s.name)} strategy={verticalListSortingStrategy}>
                <div className="space-y-1">
                  {hiddenSkills.map((skill) => (
                    <SortableSkillRow key={skill.name} id={skill.name} name={skill.name}
                      category={skill.category} mergeMode={mergeMode}
                      aliases={aliasMap[skill.name] || []} skillId={skill.id}
                      tags={skill.source === "user"
                        ? [{ label: "Custom", color: "bg-purple-500/15 text-purple-500" }]
                        : [{ label: "AI", color: "bg-blue-500/15 text-blue-500" }]}
                      onRemove={handleRemoveSkill}
                      extra={<>
                        <span className="text-[0.6rem] text-muted-foreground flex-1">Hidden</span>
                        <button onClick={(e) => { e.stopPropagation(); handleRestoreSkill(skill.name); }}
                          className="shrink-0 p-0.5 rounded hover:bg-green-500/10 text-muted-foreground hover:text-green-500 transition" title="Restore">
                          <Eye className="w-2.5 h-2.5" />
                        </button>
                      </>}
                    />
                  ))}
                </div>
              </SortableContext>
            )}
          </Card>
        )}

      </DndContext>

      {/* Drawers */}
      <SkillRoadmapDrawer skillName={selectedSkill} open={!!selectedSkill}
        onOpenChange={(open) => { if (!open) setSelectedSkill(null); }} onRefreshProgress={onRefreshProgress} />
      <SkillDetailDrawer skillName={detailSkill} open={!!detailSkill}
        onOpenChange={(open) => { if (!open) setDetailSkill(null); }} techStackSkills={techStackSkills}
        roadmapProgress={roadmapProgress} onHide={handleHideSkill} onGenerate={setSelectedSkill} />
    </div>
  );
}


