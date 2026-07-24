import { useState, useEffect, useCallback } from "react";
import {
  TrendUp, Brain, BookOpen, Wrench, ArrowsClockwise, Target,
  TreeStructure, Plus, User, EyeSlash, DotsSixVertical, GitMerge,
  Eye, CaretDown, CaretRight, Link, Lightbulb, Trash,
} from "@phosphor-icons/react";
import { cn } from "@/lib/utils";
import { resolveSkillCategory, filterByCategory } from "@/lib/skills";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from "@dnd-kit/core";
import { SortableContext, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import GenerationProgressCard from "@/components/shared/GenerationProgressCard";
import SkillRoadmapDrawer from "./SkillRoadmapDrawer";
import SkillDetailDrawer from "./SkillDetailDrawer";

const API = "/api";

const CATEGORIES = [
  { id: "technical", label: "Technical", icon: <Wrench className="w-3 h-3" />, color: "text-blue-500" },
  { id: "engineering", label: "Engineering", icon: <Target className="w-3 h-3" />, color: "text-green-500" },
  { id: "professional", label: "Professional", icon: <User className="w-3 h-3" />, color: "text-purple-500" },
  { id: "domain", label: "Domain", icon: <BookOpen className="w-3 h-3" />, color: "text-yellow-500" },
  { id: "career", label: "Career", icon: <TrendUp className="w-3 h-3" />, color: "text-cyan-500" },
];

const CATEGORY_COLORS = {
  technical: "bg-blue-500/15 text-blue-500",
  engineering: "bg-green-500/15 text-green-500",
  professional: "bg-purple-500/15 text-purple-500",
  domain: "bg-yellow-500/15 text-yellow-500",
  career: "bg-cyan-500/15 text-cyan-500",
};

const SOURCE_COLORS = {
  user: "bg-purple-500/15 text-purple-500",
  service: "bg-blue-500/15 text-blue-500",
  job_posting: "bg-green-500/15 text-green-500",
  company_analysis: "bg-orange-500/15 text-orange-500",
  market_analysis: "bg-cyan-500/15 text-cyan-500",
};

// ── Sortable skill row (works in any section) ──────────────────────
function SortableSkillRow({ id, name, category, confidence, source, marketDemand, onClick, onHide, onRemove, mergeMode, extra, aliases = [], skillId }) {
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
        "flex items-center gap-2 p-1.5 rounded transition text-xs",
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
      <span className="font-semibold w-20 truncate">{name}</span>
      {category && (
        <Badge variant="secondary" className={cn("text-[0.4rem] h-2.5 shrink-0", CATEGORY_COLORS[category] || "bg-gray-500/15 text-gray-400")}>
          {category}
        </Badge>
      )}
      <Badge variant="secondary" className={cn("text-[0.35rem] h-2 shrink-0",
        source === "user" ? "bg-purple-500/15 text-purple-500" : "bg-blue-500/15 text-blue-500"
      )}>
        {source === "user" ? "Custom" : "AI"}
      </Badge>
      {marketDemand > 0 && (
        <>
          <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
            <div className="h-full bg-primary/60 rounded-full" style={{ width: `${marketDemand}%` }} />
          </div>
          <span className="w-6 text-right text-[0.5rem] text-muted-foreground">{marketDemand}%</span>
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

// ── Main component ─────────────────────────────────────────────────
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

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }));

  const fetchTechStack = useCallback(() => {
    fetch(`${API}/tech-stack`).then((r) => r.json()).then((list) => setTechStackSkills(Array.isArray(list) ? list : [])).catch(() => {});
  }, []);

  const fetchHidden = useCallback(() => {
    fetch(`${API}/tech-stack/hidden`).then((r) => r.json()).then((list) => setHiddenSkills(Array.isArray(list) ? list : [])).catch(() => {});
  }, []);

  useEffect(() => { fetchTechStack(); fetchHidden(); }, [fetchTechStack, fetchHidden, roadmapProgress]);

  // Build alias map from API data: primary_name -> [alias1, alias2, ...]
  const aliasMap = {};
  for (const s of techStackSkills) {
    if (s.aliases && s.aliases.length > 0) {
      aliasMap[s.name] = s.aliases;
    }
  }

  // Skill categorization — exclude hidden skills
  const analyzedSkillNames = new Set([...strengths, ...gaps, ...recommendations.map((r) => r.skill)].map((s) => s.skill || s));
  const customSkillNames = techStackSkills.filter((s) => s.source === "user").map((s) => s.name);
  const derivedSkillNames = techStackSkills.filter((s) => s.source !== "user" && !analyzedSkillNames.has(s.name)).map((s) => s.name);
  const allSkillNames = [...new Set([...customSkillNames, ...analyzedSkillNames, ...derivedSkillNames])];

  const categoryCounts = {};
  for (const s of techStackSkills) { const cat = s.category || "technical"; categoryCounts[cat] = (categoryCounts[cat] || 0) + 1; }

  const filteredSkills = allSkillNames.filter((name) => {
    const item = techStackSkills.find((s) => s.name === name);
    return item?.category === activeCategory;
  });

  const aiReport = { strengths, gaps, learningRecommendations: recommendations };

  const getSkillMeta = (name) => {
    const fromStack = techStackSkills.find((s) => s.name === name);
    if (fromStack) return fromStack;
    const category = resolveSkillCategory(name, techStackSkills, aiReport);
    return category ? { category } : {};
  };
  const getSkillId = (name) => techStackSkills.find((s) => s.name === name)?.id;

  // Filter strengths/gaps/recommendations by active category
  const filteredStrengths = filterByCategory(strengths, activeCategory, techStackSkills, aiReport);
  const filteredGaps = filterByCategory(gaps, activeCategory, techStackSkills, aiReport);
  const filteredRecs = filterByCategory(recommendations, activeCategory, techStackSkills, aiReport);

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

  // Global DnD handler — works across ALL sections
  const handleDragEnd = async (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    // Find source and target in techStackSkills
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

  // Collect all draggable IDs across all sections for global DnD
  const roadmapIds = filteredSkills.filter((s) => roadmapProgress[s]?.total > 0);
  const allDraggableIds = [...new Set([...roadmapIds, ...filteredStrengths.map((s) => s.skill), ...filteredGaps.map((g) => g.skill), ...filteredRecs.map((r) => r.skill)])];

  return (
    <div className="space-y-5">
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
          <strong className="text-foreground">Merge Mode</strong> — Drag any skill onto another across any section. Target keeps its name, source is absorbed.
        </div>
      )}

      {/* Category Navigation + Add Custom Skill toggle */}
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

      {/* ═══ Global DnD Context — wraps ALL sections ═══ */}
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>

        {/* ═══ Strengths — top, prominent ═══ */}
        <Card className="p-4 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendUp className="w-5 h-5 text-green-500" />
            <h4 className="font-extrabold text-sm">Strengths</h4>
            <Badge variant="secondary" className="text-[0.5rem] bg-green-500/15 text-green-500">{filteredStrengths.length}</Badge>
          </div>
          <SortableContext items={filteredStrengths.map((s) => s.skill)} strategy={verticalListSortingStrategy}>
            <div className="grid grid-cols-2 gap-1 max-h-[200px] overflow-y-auto">
              {filteredStrengths.length > 0 ? filteredStrengths.map((s) => {
                const meta = getSkillMeta(s.skill);
                return (
                  <SortableSkillRow key={s.skill} id={s.skill} name={s.skill}
                    category={s.category || meta.category} confidence={s.confidence || meta.confidence}
                    source={meta.source || "service"} marketDemand={s.market_demand}
                    onClick={(n) => setDetailSkill(n)} onHide={handleHideSkill} onRemove={handleRemoveSkill}
                    mergeMode={mergeMode} aliases={aliasMap[s.skill] || []} skillId={getSkillId(s.skill)} />
                );
              }) : <div className="text-xs text-muted-foreground col-span-2">No strengths in this category</div>}
            </div>
          </SortableContext>
        </Card>

        {/* ═══ Roadmaps + Gaps (two columns) ═══ */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          {/* Skill Roadmaps */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <TreeStructure className="w-5 h-5 text-emerald-500" />
              <h4 className="font-extrabold text-sm">Skill Roadmaps</h4>
              <Badge variant="secondary" className="text-[0.5rem] bg-emerald-500/15 text-emerald-500">{roadmapIds.length}</Badge>
            </div>
            {genJobs.length > 0 && genJobs.map((job) => (
              <div key={job.skill} className="cursor-pointer" onClick={() => setSelectedSkill(job.skill)}>
                <GenerationProgressCard title={job.skill} progress={{ running: true, ...job }} compact className="mb-2" />
              </div>
            ))}
            <SortableContext items={roadmapIds} strategy={verticalListSortingStrategy}>
              <div className="space-y-1 max-h-[300px] overflow-y-auto">
                {roadmapIds.map((skill) => {
                  const meta = getSkillMeta(skill);
                  const prog = roadmapProgress[skill];
                  return (
                    <SortableSkillRow key={skill} id={skill} name={skill}
                      category={meta.category} confidence={meta.confidence} source={meta.source}
                      onClick={(s) => setDetailSkill(s)} onHide={handleHideSkill} onRemove={handleRemoveSkill}
                      mergeMode={mergeMode} aliases={aliasMap[skill] || []} skillId={getSkillId(skill)}
                      extra={<>
                        <div className="flex-1"><Progress value={prog.pct} className="h-1.5" /></div>
                        <span className="text-[0.6rem] text-muted-foreground w-12 text-right shrink-0">{prog.completed}/{prog.total}</span>
                        <Badge variant="secondary" className={cn("text-[0.45rem] h-3 shrink-0",
                          prog.pct === 100 ? "bg-green-500/15 text-green-500" : prog.pct > 0 ? "bg-emerald-500/15 text-emerald-500" : "bg-gray-500/15 text-gray-400"
                        )}>{prog.pct}%</Badge>
                      </>}
                    />
                  );
                })}
              </div>
            </SortableContext>
          </Card>

          {/* AI-Detected + Custom without roadmap */}
          <div className="space-y-4">
            {derivedSkillNames.filter((s) => !roadmapProgress[s] || roadmapProgress[s].total === 0).length > 0 && (
              <Card className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Brain className="w-4 h-4 text-blue-500" />
                  <h4 className="font-extrabold text-sm">AI-Detected Skills</h4>
                </div>
                <SortableContext items={derivedSkillNames.filter((s) => (!roadmapProgress[s] || roadmapProgress[s].total === 0) && getSkillMeta(s).category === activeCategory)} strategy={verticalListSortingStrategy}>
                  <div className="space-y-1 max-h-[200px] overflow-y-auto">
                    {derivedSkillNames.filter((s) => (!roadmapProgress[s] || roadmapProgress[s].total === 0) && getSkillMeta(s).category === activeCategory).map((skill) => {
                      const meta = getSkillMeta(skill);
                      return (
                        <SortableSkillRow key={skill} id={skill} name={skill}
                          category={meta.category} confidence={meta.confidence} source={meta.source}
                          onClick={(s) => setDetailSkill(s)} onHide={handleHideSkill} onRemove={handleRemoveSkill}
                          mergeMode={mergeMode} aliases={aliasMap[skill] || []} skillId={getSkillId(skill)}
                          extra={<>
                            <span className="text-[0.6rem] text-muted-foreground flex-1">No roadmap</span>
                            <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); setSelectedSkill(skill); }}
                              className="h-5 text-[0.5rem] gap-0.5"><TreeStructure className="w-2.5 h-2.5" /> Generate</Button>
                          </>}
                        />
                      );
                    })}
                  </div>
                </SortableContext>
              </Card>
            )}

            {customSkillNames.filter((s) => !roadmapProgress[s] || roadmapProgress[s].total === 0).length > 0 && (
              <Card className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <User className="w-4 h-4 text-purple-500" />
                  <h4 className="font-extrabold text-sm">Custom Skills</h4>
                </div>
                <SortableContext items={customSkillNames.filter((s) => !roadmapProgress[s] || roadmapProgress[s].total === 0)} strategy={verticalListSortingStrategy}>
                  <div className="space-y-1 max-h-[150px] overflow-y-auto">
                    {customSkillNames.filter((s) => !roadmapProgress[s] || roadmapProgress[s].total === 0).map((skill) => {
                      const meta = getSkillMeta(skill);
                      return (
                        <SortableSkillRow key={skill} id={skill} name={skill}
                          category={meta.category} confidence={meta.confidence} source={meta.source}
                          onClick={(s) => setDetailSkill(s)} onHide={handleHideSkill} onRemove={handleRemoveSkill}
                          mergeMode={mergeMode} aliases={aliasMap[skill] || []} skillId={getSkillId(skill)}
                          extra={<>
                            <span className="text-[0.6rem] text-muted-foreground flex-1">No roadmap</span>
                            <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); setSelectedSkill(skill); }}
                              className="h-5 text-[0.5rem] gap-0.5"><TreeStructure className="w-2.5 h-2.5" /> Generate</Button>
                          </>}
                        />
                      );
                    })}
                  </div>
                </SortableContext>
              </Card>
            )}
          </div>
        </div>

        {/* ═══ Gaps + Recommendations (two columns) ═══ */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          {/* Gaps */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <BookOpen className="w-4 h-4 text-red-500" />
              <h4 className="font-extrabold text-sm">Skill Gaps</h4>
              <Badge variant="secondary" className="text-[0.5rem] bg-red-500/15 text-red-500">{filteredGaps.length}</Badge>
            </div>
            <SortableContext items={filteredGaps.map((g) => g.skill)} strategy={verticalListSortingStrategy}>
              <div className="space-y-1 max-h-[250px] overflow-y-auto">
                {filteredGaps.length > 0 ? filteredGaps.map((g) => {
                  const meta = getSkillMeta(g.skill);
                  return (
                    <SortableSkillRow key={g.skill} id={g.skill} name={g.skill}
                      category={g.category || meta.category} confidence={g.confidence || meta.confidence}
                      source={meta.source || "service"} marketDemand={g.market_demand}
                      onClick={(n) => setDetailSkill(n)} onHide={handleHideSkill} onRemove={handleRemoveSkill}
                      mergeMode={mergeMode} aliases={aliasMap[g.skill] || []} skillId={getSkillId(g.skill)} />
                  );
                }) : <div className="text-xs text-muted-foreground">No gaps in this category</div>}
              </div>
            </SortableContext>
          </Card>

          {/* Recommendations */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Brain className="w-4 h-4 text-primary" />
              <h4 className="font-extrabold text-sm">Recommendations</h4>
              <Badge variant="secondary" className="text-[0.5rem] bg-primary/15 text-primary">{filteredRecs.length}</Badge>
            </div>
            <div className="grid grid-cols-3 gap-2 max-h-[250px] overflow-y-auto">
              {filteredRecs.length > 0 ? filteredRecs.map((r) => (
                <div key={r.skill} className="p-2 rounded-lg border border-primary/20 bg-primary/5 cursor-pointer hover:border-primary/40 transition"
                  onClick={() => setDetailSkill(r.skill)}>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs truncate">{r.skill}</span>
                    <Badge variant="secondary" className={cn("text-[0.45rem] h-3 shrink-0", r.roi >= 8 ? "bg-green-500/15 text-green-500" : "bg-gray-500/15 text-gray-400")}>
                      ROI: {r.roi}/10
                    </Badge>
                  </div>
                  <div className="text-[0.55rem] text-muted-foreground mt-0.5 line-clamp-2">{r.reason}</div>
                  {r.category && <Badge variant="secondary" className={cn("text-[0.4rem] h-2.5 mt-1", CATEGORY_COLORS[r.category])}>{r.category}</Badge>}
                </div>
              )) : <div className="text-xs text-muted-foreground text-center py-4 col-span-3">No recommendations in this category</div>}
            </div>
          </Card>
        </div>

        {/* Hidden Skills — collapsed, at the end */}
        {hiddenSkills.length > 0 && (
          <Card className="p-4 mb-4">
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
      {/* ═══ End global DnD context ═══ */}

      {/* Drawers */}
      <SkillRoadmapDrawer skillName={selectedSkill} open={!!selectedSkill}
        onOpenChange={(open) => { if (!open) setSelectedSkill(null); }} onRefreshProgress={onRefreshProgress} />
      <SkillDetailDrawer skillName={detailSkill} open={!!detailSkill}
        onOpenChange={(open) => { if (!open) setDetailSkill(null); }} techStackSkills={techStackSkills}
        roadmapProgress={roadmapProgress} onHide={handleHideSkill} onGenerate={setSelectedSkill} />
    </div>
  );
}
