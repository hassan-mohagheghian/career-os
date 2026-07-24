import { useState, useEffect, useCallback } from "react";
import {
  TrendUp, Brain, BookOpen, Wrench, ArrowsClockwise, Target,
  TreeStructure, Plus, User, EyeSlash, DotsSixVertical, GitMerge,
  Eye, CaretDown, CaretRight, Link,
} from "@phosphor-icons/react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from "@dnd-kit/core";
import { SortableContext, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import GenerationProgressCard from "@/components/shared/GenerationProgressCard";
import SkillRoadmapDrawer from "./SkillRoadmapDrawer";
import SkillDetailDrawer from "./SkillDetailDrawer";

const API = "/api";

const CATEGORIES = [
  { id: "all", label: "All", icon: <Wrench className="w-3 h-3" /> },
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
function SortableSkillRow({ id, name, category, confidence, source, marketDemand, onClick, onHide, mergeMode, extra }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 10 : 0,
  };

  return (
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
      {!mergeMode && onHide && (
        <button
          onClick={(e) => { e.stopPropagation(); onHide(name); }}
          className="shrink-0 p-0.5 rounded hover:bg-red-500/10 text-muted-foreground hover:text-red-500 transition"
          title="Hide"
        >
          <EyeSlash className="w-2.5 h-2.5" />
        </button>
      )}
    </div>
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
  const [activeCategory, setActiveCategory] = useState("all");
  const [showHidden, setShowHidden] = useState(false);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }));

  const fetchTechStack = useCallback(() => {
    fetch(`${API}/tech-stack`).then((r) => r.json()).then((list) => setTechStackSkills(Array.isArray(list) ? list : [])).catch(() => {});
  }, []);

  const fetchHidden = useCallback(() => {
    fetch(`${API}/tech-stack/hidden`).then((r) => r.json()).then((list) => setHiddenSkills(Array.isArray(list) ? list : [])).catch(() => {});
  }, []);

  useEffect(() => { fetchTechStack(); fetchHidden(); }, [fetchTechStack, fetchHidden, roadmapProgress]);

  // Skill categorization
  const analyzedSkillNames = new Set([...strengths, ...gaps, ...recommendations.map((r) => r.skill)].map((s) => s.skill || s));
  const customSkillNames = techStackSkills.filter((s) => s.source === "user").map((s) => s.name);
  const derivedSkillNames = techStackSkills.filter((s) => s.source !== "user" && !analyzedSkillNames.has(s.name)).map((s) => s.name);
  const allSkillNames = [...new Set([...customSkillNames, ...analyzedSkillNames, ...derivedSkillNames])];

  const categoryCounts = {};
  for (const s of techStackSkills) { const cat = s.category || "technical"; categoryCounts[cat] = (categoryCounts[cat] || 0) + 1; }

  const filteredSkills = activeCategory === "all" ? allSkillNames : activeCategory === "custom" ? customSkillNames : activeCategory === "hidden" ? [] : allSkillNames.filter((name) => {
    const item = techStackSkills.find((s) => s.name === name);
    return item?.category === activeCategory;
  });

  const getSkillMeta = (name) => techStackSkills.find((s) => s.name === name) || {};

  // Filter strengths/gaps/recommendations by active category
  const filteredStrengths = activeCategory === "all" || activeCategory === "strengths" ? strengths : strengths.filter((s) => { const meta = getSkillMeta(s.skill); return meta.category === activeCategory; });
  const filteredGaps = activeCategory === "all" || activeCategory === "gaps" ? gaps : gaps.filter((g) => { const meta = getSkillMeta(g.skill); return meta.category === activeCategory; });
  const filteredRecs = activeCategory === "all" || activeCategory === "recommendations" ? recommendations : recommendations.filter((r) => { const meta = getSkillMeta(r.skill); return meta.category === activeCategory; });

  const handleAddCustomSkill = async () => {
    const name = customSkillInput.trim();
    if (!name) return;
    try {
      await fetch(`${API}/tech-stack`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, level: 1, source: "user", source_type: "user_input" }),
      });
      setCustomSkillInput(""); fetchTechStack(); if (onRefreshProgress) onRefreshProgress(); setSelectedSkill(name);
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
        toast.success(`Merged "${sourceItem.name}" → "${targetItem.name}"`);
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

      {/* Overview Stats — clickable to filter */}
      <div className="grid grid-cols-5 gap-2">
        {[
          { n: customSkillNames.length, l: "Custom", c: "text-purple-500", icon: <User className="w-4 h-4" />, filter: "custom" },
          { n: strengths.length, l: "Strengths", c: "text-green-500", icon: <TrendUp className="w-4 h-4" />, filter: "strengths" },
          { n: gaps.length, l: "Gaps", c: "text-red-500", icon: <BookOpen className="w-4 h-4" />, filter: "gaps" },
          { n: recommendations.length, l: "Recommendations", c: "text-blue-500", icon: <Brain className="w-4 h-4" />, filter: "recommendations" },
          { n: hiddenSkills.length, l: "Hidden", c: "text-gray-500", icon: <EyeSlash className="w-4 h-4" />, filter: "hidden" },
        ].map((s, i) => (
          <Card key={i} className="p-2 text-center transition hover:border-primary cursor-pointer"
            onClick={() => setActiveCategory(s.filter === activeCategory ? "all" : s.filter)}>
            <div className={cn("mb-0.5", s.c)}>{s.icon}</div>
            <div className={cn("text-lg font-extrabold", s.c)}>{s.n}</div>
            <div className="text-[0.5rem] uppercase tracking-wider text-muted-foreground">{s.l}</div>
          </Card>
        ))}
      </div>

      {/* Category Navigation */}
      <div className="flex gap-1 flex-wrap">
        {CATEGORIES.map((cat) => (
          <Button key={cat.id} variant={activeCategory === cat.id ? "default" : "ghost"} size="sm"
            onClick={() => setActiveCategory(cat.id)}
            className={cn("h-6 text-[0.55rem] gap-1", activeCategory === cat.id && "bg-primary/20")}>
            {cat.icon} {cat.label}
            {cat.id !== "all" && categoryCounts[cat.id] > 0 && (
              <Badge variant="secondary" className="text-[0.4rem] h-3 ml-0.5">{categoryCounts[cat.id]}</Badge>
            )}
          </Button>
        ))}
      </div>

      {/* ═══ Global DnD Context — wraps ALL sections ═══ */}
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>

        {/* ═══ Top row: Roadmaps + AI-Detected (two columns) ═══ */}
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
                      onClick={(s) => setDetailSkill(s)} onHide={handleHideSkill} mergeMode={mergeMode}
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
            <div className="flex items-center gap-2 pt-2 border-t mt-2">
              <Input value={customSkillInput} onChange={(e) => setCustomSkillInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAddCustomSkill()}
                placeholder="Add custom skill..." className="h-7 text-xs flex-1" />
              <Button size="sm" variant="outline" onClick={handleAddCustomSkill} disabled={!customSkillInput.trim()} className="h-7 gap-1 text-[0.6rem]">
                <Plus className="w-3 h-3" /> Add
              </Button>
            </div>
          </Card>

          {/* AI-Detected + Custom without roadmap */}
          <div className="space-y-4">
            {derivedSkillNames.filter((s) => !roadmapProgress[s] || roadmapProgress[s].total === 0).length > 0 && (
              <Card className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Brain className="w-4 h-4 text-blue-500" />
                  <h4 className="font-extrabold text-sm">AI-Detected Skills</h4>
                </div>
                <SortableContext items={derivedSkillNames.filter((s) => !roadmapProgress[s] || roadmapProgress[s].total === 0)} strategy={verticalListSortingStrategy}>
                  <div className="space-y-1 max-h-[200px] overflow-y-auto">
                    {derivedSkillNames.filter((s) => !roadmapProgress[s] || roadmapProgress[s].total === 0).map((skill) => {
                      const meta = getSkillMeta(skill);
                      return (
                        <SortableSkillRow key={skill} id={skill} name={skill}
                          category={meta.category} confidence={meta.confidence} source={meta.source}
                          onClick={(s) => setDetailSkill(s)} onHide={handleHideSkill} mergeMode={mergeMode}
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
                          onClick={(s) => setDetailSkill(s)} onHide={handleHideSkill} mergeMode={mergeMode}
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

        {/* Hidden Skills */}
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

        {/* ═══ Strengths / Gaps / Recommendations — two-columnar, filtered by category ═══ */}
        <div className="grid grid-cols-2 gap-4">
          {/* Strengths */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendUp className="w-4 h-4 text-green-500" />
              <h4 className="font-extrabold text-sm">Strengths</h4>
              <Badge variant="secondary" className="text-[0.5rem] bg-green-500/15 text-green-500">{filteredStrengths.length}</Badge>
            </div>
            <SortableContext items={filteredStrengths.map((s) => s.skill)} strategy={verticalListSortingStrategy}>
              <div className="space-y-1 max-h-[300px] overflow-y-auto">
                {filteredStrengths.length > 0 ? filteredStrengths.map((s) => {
                  const meta = getSkillMeta(s.skill);
                  return (
                    <SortableSkillRow key={s.skill} id={s.skill} name={s.skill}
                      category={s.category || meta.category} confidence={s.confidence || meta.confidence}
                      marketDemand={s.market_demand} onClick={(n) => setDetailSkill(n)}
                      onHide={handleHideSkill} mergeMode={mergeMode} />
                  );
                }) : <div className="text-xs text-muted-foreground">No strengths in this category</div>}
              </div>
            </SortableContext>
          </Card>

          {/* Gaps */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <BookOpen className="w-4 h-4 text-red-500" />
              <h4 className="font-extrabold text-sm">Skill Gaps</h4>
              <Badge variant="secondary" className="text-[0.5rem] bg-red-500/15 text-red-500">{filteredGaps.length}</Badge>
            </div>
            <SortableContext items={filteredGaps.map((g) => g.skill)} strategy={verticalListSortingStrategy}>
              <div className="space-y-1 max-h-[300px] overflow-y-auto">
                {filteredGaps.length > 0 ? filteredGaps.map((g) => {
                  const meta = getSkillMeta(g.skill);
                  return (
                    <SortableSkillRow key={g.skill} id={g.skill} name={g.skill}
                      category={g.category || meta.category} confidence={g.confidence || meta.confidence}
                      marketDemand={g.market_demand} onClick={(n) => setDetailSkill(n)}
                      onHide={handleHideSkill} mergeMode={mergeMode} />
                  );
                }) : <div className="text-xs text-muted-foreground">No gaps in this category</div>}
              </div>
            </SortableContext>
          </Card>

          {/* Recommendations — spans full width below */}
          <Card className="p-4 col-span-2">
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
