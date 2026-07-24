import { useState, useEffect, useCallback } from "react";
import {
  TrendUp,
  Brain,
  BookOpen,
  ChartLineUp,
  Wrench,
  ArrowsClockwise,
  Target,
  TreeStructure,
  Plus,
  User,
  Spinner,
  EyeSlash,
  DotsSixVertical,
  GitMerge,
  X,
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

const API = "/api";

// ── Sortable skill item for merge DnD ──────────────────────────────

function SortableSkillItem({ id, skill, isCustom, isAnalyzed, roadmapProgress, onClick, onHide, mergeMode }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 10 : 0,
  };
  const prog = roadmapProgress[skill];
  const hasRoadmap = prog && prog.total > 0;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        "flex items-center gap-2 p-2 rounded transition",
        isDragging ? "bg-primary/10 shadow-md" : "hover:bg-muted/50",
        mergeMode ? "cursor-grab" : "cursor-pointer",
      )}
      onClick={() => !mergeMode && onClick?.(skill)}
    >
      {mergeMode && (
        <button {...attributes} {...listeners} className="shrink-0 cursor-grab active:cursor-grabbing">
          <DotsSixVertical className="w-3 h-3 text-muted-foreground" />
        </button>
      )}
      <span className="text-xs font-semibold w-24 truncate">{skill}</span>
      {isCustom ? (
        <Badge variant="secondary" className="text-[0.4rem] h-3.5 bg-purple-500/15 text-purple-500 shrink-0 gap-0.5">
          <User className="w-2.5 h-2.5" /> Custom
        </Badge>
      ) : isAnalyzed ? (
        <Badge variant="secondary" className="text-[0.4rem] h-3.5 bg-green-500/15 text-green-500 shrink-0">
          AI-analyzed
        </Badge>
      ) : (
        <Badge variant="secondary" className="text-[0.4rem] h-3.5 bg-blue-500/15 text-blue-500 shrink-0">
          AI-detected
        </Badge>
      )}
      {hasRoadmap && (
        <>
          <div className="flex-1">
            <Progress value={prog.pct} className="h-1.5" />
          </div>
          <span className="text-[0.6rem] text-muted-foreground w-12 text-right shrink-0">
            {prog.completed}/{prog.total}
          </span>
          <Badge
            variant="secondary"
            className={cn(
              "text-[0.45rem] h-3 shrink-0",
              prog.pct === 100 ? "bg-green-500/15 text-green-500" :
              prog.pct > 0 ? "bg-emerald-500/15 text-emerald-500" :
              "bg-gray-500/15 text-gray-400",
            )}
          >
            {prog.pct}%
          </Badge>
        </>
      )}
      {!hasRoadmap && <span className="text-[0.6rem] text-muted-foreground flex-1">No roadmap yet</span>}
      {!mergeMode && (
        <button
          onClick={(e) => { e.stopPropagation(); onHide?.(skill); }}
          className="shrink-0 p-1 rounded hover:bg-red-500/10 text-muted-foreground hover:text-red-500 transition"
          title="Hide skill"
        >
          <EyeSlash className="w-3 h-3" />
        </button>
      )}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────

function SkillRow({ skill, type, onClick, roadmapProgress, onHide }) {
  const levelColors = {
    expert: "bg-green-500/15 text-green-500",
    advanced: "bg-blue-500/15 text-blue-500",
    intermediate: "bg-yellow-500/15 text-yellow-500",
    beginner: "bg-orange-500/15 text-orange-500",
    none: "bg-red-500/15 text-red-500",
  };
  const prog = roadmapProgress?.[skill.skill];
  const hasProgress = prog && prog.total > 0;
  return (
    <div
      className="flex items-center gap-2 p-2 rounded hover:bg-muted transition text-xs cursor-pointer"
      onClick={() => onClick?.(skill.skill)}
    >
      <span className="font-semibold w-24 truncate">{skill.skill}</span>
      <div className="flex-1 space-y-1">
        <div className="h-[3px] rounded-full bg-muted">
          <div className="h-full rounded-full bg-primary" style={{ width: `${skill.demandPercentage || 0}%` }} />
        </div>
        {hasProgress && (
          <div className="h-[3px] rounded-full bg-muted">
            <div
              className={cn("h-full rounded-full transition-all", prog.pct === 100 ? "bg-green-500" : prog.pct > 0 ? "bg-emerald-400" : "bg-muted")}
              style={{ width: `${prog.pct}%` }}
            />
          </div>
        )}
      </div>
      <div className="flex items-center gap-1.5 shrink-0">
        <span className="w-8 text-right text-[0.55rem] text-muted-foreground">{skill.demandPercentage || 0}%</span>
        {hasProgress ? (
          <Badge variant="secondary" className={cn("text-[0.45rem] h-3", prog.pct === 100 ? "bg-green-500/15 text-green-500" : prog.pct > 0 ? "bg-emerald-500/15 text-emerald-500" : "bg-gray-500/15 text-gray-400")}>
            {prog.pct}%
          </Badge>
        ) : (
          <Badge variant="secondary" className={cn("text-[0.45rem] h-3 shrink-0", levelColors[skill.candidateLevel || skill.currentLevel] || "bg-gray-500/15 text-gray-400")}>
            {skill.candidateLevel || skill.currentLevel}
          </Badge>
        )}
      </div>
    </div>
  );
}

function RecommendationCard({ rec, onClick, roadmapProgress }) {
  const prog = roadmapProgress?.[rec.skill];
  const hasProgress = prog && prog.total > 0;
  return (
    <div className="p-2 rounded-lg border border-primary/20 bg-primary/5 space-y-1 cursor-pointer hover:border-primary/40 transition" onClick={() => onClick?.(rec.skill)}>
      <div className="flex items-center justify-between">
        <span className="font-bold text-xs">{rec.skill}</span>
        <div className="flex items-center gap-1">
          {hasProgress && (
            <Badge variant="secondary" className={cn("text-[0.45rem] h-3.5", prog.pct === 100 ? "bg-green-500/15 text-green-500" : prog.pct > 0 ? "bg-emerald-500/15 text-emerald-500" : "bg-gray-500/15 text-gray-400")}>
              {prog.done}/{prog.total}
            </Badge>
          )}
          <Badge variant="secondary" className={cn("text-[0.45rem] h-3.5", rec.roi >= 8 ? "bg-green-500/15 text-green-500" : rec.roi >= 6 ? "bg-yellow-500/15 text-yellow-500" : "bg-gray-500/15 text-gray-400")}>
            ROI: {rec.roi}/10
          </Badge>
        </div>
      </div>
      <div className="text-[0.55rem] text-muted-foreground">{rec.reason}</div>
      <div className="flex items-center gap-2 text-[0.5rem] text-muted-foreground">
        <span>Demand: {rec.demandPercentage}%</span>
        <span>·</span>
        <span>Effort: {rec.learningEffort}</span>
      </div>
      {hasProgress && prog.pct > 0 && <Progress value={prog.pct} className="h-1 mt-1" />}
    </div>
  );
}

export default function SkillsIntelSection({
  data,
  refreshing,
  onRefresh,
  roadmapProgress,
  onRefreshProgress,
  genJobs = [],
}) {
  const skills = data?.skills || {};
  const strengths = skills.strengths || [];
  const gaps = skills.gaps || [];
  const recommendations = skills.learningRecommendations || [];
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [customSkillInput, setCustomSkillInput] = useState("");
  const [techStackSkills, setTechStackSkills] = useState([]);
  const [mergeMode, setMergeMode] = useState(false);
  const [mergeTarget, setMergeTarget] = useState(null);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }));

  const fetchTechStack = useCallback(() => {
    fetch(`${API}/tech-stack`)
      .then((r) => r.json())
      .then((list) => setTechStackSkills(Array.isArray(list) ? list : []))
      .catch(() => {});
  }, []);

  useEffect(() => { fetchTechStack(); }, [fetchTechStack, roadmapProgress]);

  // Skills already shown in Strengths/Gaps/Recommendations — avoid repeating
  const analyzedSkillNames = new Set(
    [...strengths, ...gaps, ...recommendations.map((r) => r.skill)].map((s) => s.skill || s),
  );

  // Custom skills = user-added only (source=user)
  const customSkillNames = techStackSkills.filter((s) => s.source === "user").map((s) => s.name);

  // Derived skills = from tech_stack but NOT user-added and NOT already in analyzed sections
  const derivedSkillNames = techStackSkills.filter((s) => s.source !== "user" && !analyzedSkillNames.has(s.name)).map((s) => s.name);

  // All skills = custom + analyzed + derived (no duplicates)
  const allSkillNames = [...new Set([...customSkillNames, ...analyzedSkillNames, ...derivedSkillNames])];

  const handleAddCustomSkill = async () => {
    const name = customSkillInput.trim();
    if (!name) return;
    try {
      await fetch(`${API}/tech-stack`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, level: 1, source: "user" }),
      });
      setCustomSkillInput("");
      fetchTechStack();
      if (onRefreshProgress) onRefreshProgress();
      setSelectedSkill(name);
    } catch {}
  };

  // ── Hide skill ────────────────────────────────────────────────
  const handleHideSkill = async (skillName) => {
    const item = techStackSkills.find((s) => s.name === skillName);
    if (!item) return;
    try {
      await fetch(`${API}/tech-stack/${item.id}/hide`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hidden: 1 }),
      });
      toast.success(`"${skillName}" hidden`);
      fetchTechStack();
    } catch {
      toast.error("Failed to hide skill");
    }
  };

  // ── Merge skills via DnD ─────────────────────────────────────
  const handleDragEnd = async (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const sourceItem = techStackSkills.find((s) => s.name === active.id);
    const targetItem = techStackSkills.find((s) => s.name === over.id);
    if (!sourceItem || !targetItem) return;

    // Confirm merge
    const confirmed = window.confirm(`Merge "${sourceItem.name}" into "${targetItem.name}"?\n\n"${targetItem.name}" will keep its name. "${sourceItem.name}" will be removed.`);
    if (!confirmed) return;

    try {
      const res = await fetch(`${API}/tech-stack/merge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_id: targetItem.id, source_ids: [sourceItem.id] }),
      });
      const result = await res.json();
      if (result.status === "merged") {
        toast.success(`Merged "${sourceItem.name}" → "${targetItem.name}"`);
        fetchTechStack();
        if (onRefreshProgress) onRefreshProgress();
      }
    } catch {
      toast.error("Failed to merge skills");
    }
    setMergeTarget(null);
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="font-extrabold text-sm">Skills Intelligence</h3>
        <div className="flex items-center gap-2">
          <Button
            variant={mergeMode ? "default" : "ghost"}
            size="sm"
            onClick={() => { setMergeMode(!mergeMode); setMergeTarget(null); }}
            className={cn("gap-1 h-6 text-[0.55rem]", mergeMode && "bg-primary/20")}
          >
            <GitMerge className="w-3 h-3" /> {mergeMode ? "Exit Merge" : "Merge Skills"}
          </Button>
          <Button variant="ghost" size="sm" onClick={onRefresh} disabled={refreshing.skills} className="gap-1 h-6 text-[0.55rem]">
            <ArrowsClockwise className={cn("w-3 h-3", refreshing.skills && "animate-spin")} /> Refresh
          </Button>
        </div>
      </div>

      {mergeMode && (
        <div className="rounded-lg border border-dashed border-primary/40 bg-primary/5 p-3 text-[0.65rem] text-muted-foreground">
          <strong className="text-foreground">Merge Mode</strong> — Drag a skill onto another to merge them.
          The skill you drop <em>onto</em> keeps its name. The dragged skill is absorbed and removed.
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-5 gap-3">
        {[
          { n: customSkillNames.length, l: "Custom", c: "text-purple-500", icon: <User className="w-5 h-5" /> },
          { n: strengths.length, l: "Strengths", c: "text-green-500", icon: <TrendUp className="w-5 h-5" /> },
          { n: gaps.length, l: "Gaps", c: "text-red-500", icon: <BookOpen className="w-5 h-5" /> },
          { n: recommendations.length, l: "Recommendations", c: "text-blue-500", icon: <Brain className="w-5 h-5" /> },
          { n: derivedSkillNames.length, l: "AI-Detected", c: "text-yellow-500", icon: <Wrench className="w-5 h-5" /> },
        ].map((s, i) => (
          <Card key={i} className="p-3 text-center transition hover:border-primary">
            <div className={cn("mb-1", s.c)}>{s.icon}</div>
            <div className={cn("text-xl font-extrabold", s.c)}>{s.n}</div>
            <div className="text-[0.6rem] uppercase tracking-wider text-muted-foreground">{s.l}</div>
          </Card>
        ))}
      </div>

      {/* Skill Roadmaps section — with DnD for merge */}
      <Card className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <TreeStructure className="w-5 h-5 text-emerald-500" />
          <h4 className="font-extrabold text-sm">Skill Roadmaps</h4>
          <Badge variant="secondary" className="text-[0.5rem] bg-emerald-500/15 text-emerald-500">
            {allSkillNames.filter((s) => roadmapProgress[s]?.total > 0).length}
          </Badge>
        </div>

        {genJobs.length > 0 && genJobs.map((job) => (
          <div key={job.skill} className="cursor-pointer" onClick={() => setSelectedSkill(job.skill)}>
            <GenerationProgressCard title={job.skill} progress={{ running: true, ...job }} compact className="mb-2" />
          </div>
        ))}

        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={allSkillNames.filter((s) => roadmapProgress[s]?.total > 0)} strategy={verticalListSortingStrategy}>
            <div className="space-y-2">
              {allSkillNames.map((skill) => {
                const prog = roadmapProgress[skill];
                const hasRoadmap = prog && prog.total > 0;
                if (!hasRoadmap) return null;
                const isCustom = customSkillNames.includes(skill);
                const isAnalyzed = analyzedSkillNames.has(skill);
                return (
                  <SortableSkillItem
                    key={skill}
                    id={skill}
                    skill={skill}
                    isCustom={isCustom}
                    isAnalyzed={isAnalyzed}
                    roadmapProgress={roadmapProgress}
                    onClick={setSelectedSkill}
                    onHide={handleHideSkill}
                    mergeMode={mergeMode}
                  />
                );
              })}
            </div>
          </SortableContext>
        </DndContext>

        {/* Add custom skill */}
        <div className="flex items-center gap-2 pt-2 border-t mt-2">
          <Input value={customSkillInput} onChange={(e) => setCustomSkillInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleAddCustomSkill()} placeholder="Add custom skill..." className="h-7 text-xs flex-1" />
          <Button size="sm" variant="outline" onClick={handleAddCustomSkill} disabled={!customSkillInput.trim()} className="h-7 gap-1 text-[0.6rem]">
            <Plus className="w-3 h-3" /> Add
          </Button>
        </div>
      </Card>

      {/* Custom Skills — user-added, no roadmap yet */}
      {customSkillNames.filter((s) => !roadmapProgress[s] || roadmapProgress[s].total === 0).length > 0 && (
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <User className="w-5 h-5 text-purple-500" />
            <h4 className="font-extrabold text-sm">Custom Skills</h4>
            <Badge variant="secondary" className="text-[0.5rem] bg-purple-500/15 text-purple-500">
              {customSkillNames.filter((s) => !roadmapProgress[s] || roadmapProgress[s].total === 0).length}
            </Badge>
          </div>
          <div className="space-y-2">
            {customSkillNames
              .filter((s) => !roadmapProgress[s] || roadmapProgress[s].total === 0)
              .map((skill) => (
                <div key={skill} className="flex items-center gap-2 p-2 rounded hover:bg-muted/50 transition cursor-pointer" onClick={() => setSelectedSkill(skill)}>
                  <span className="text-xs font-semibold w-24 truncate">{skill}</span>
                  <Badge variant="secondary" className="text-[0.4rem] h-3.5 bg-purple-500/15 text-purple-500 shrink-0 gap-0.5">
                    <User className="w-2.5 h-2.5" /> Custom
                  </Badge>
                  <span className="text-[0.6rem] text-muted-foreground flex-1">No roadmap yet</span>
                  <button onClick={(e) => { e.stopPropagation(); handleHideSkill(skill); }} className="shrink-0 p-1 rounded hover:bg-red-500/10 text-muted-foreground hover:text-red-500 transition" title="Hide skill">
                    <EyeSlash className="w-3 h-3" />
                  </button>
                  <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); setSelectedSkill(skill); }} className="h-5 text-[0.5rem] gap-0.5">
                    <TreeStructure className="w-2.5 h-2.5" /> Generate
                  </Button>
                </div>
              ))}
          </div>
        </Card>
      )}

      {/* AI-Detected Skills */}
      {derivedSkillNames.filter((s) => !roadmapProgress[s] || roadmapProgress[s].total === 0).length > 0 && (
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Brain className="w-5 h-5 text-blue-500" />
            <h4 className="font-extrabold text-sm">AI-Detected Skills</h4>
            <Badge variant="secondary" className="text-[0.5rem] bg-blue-500/15 text-blue-500">
              {derivedSkillNames.filter((s) => !roadmapProgress[s] || roadmapProgress[s].total === 0).length}
            </Badge>
          </div>
          <div className="text-[0.6rem] text-muted-foreground mb-2">Detected from job postings — not yet in Strengths, Gaps, or Recommendations</div>
          <div className="space-y-2">
            {derivedSkillNames
              .filter((s) => !roadmapProgress[s] || roadmapProgress[s].total === 0)
              .map((skill) => (
                <div key={skill} className="flex items-center gap-2 p-2 rounded hover:bg-muted/50 transition cursor-pointer" onClick={() => setSelectedSkill(skill)}>
                  <span className="text-xs font-semibold w-24 truncate">{skill}</span>
                  <Badge variant="secondary" className="text-[0.4rem] h-3.5 bg-blue-500/15 text-blue-500 shrink-0">AI-detected</Badge>
                  <span className="text-[0.6rem] text-muted-foreground flex-1">No roadmap yet</span>
                  <button onClick={(e) => { e.stopPropagation(); handleHideSkill(skill); }} className="shrink-0 p-1 rounded hover:bg-red-500/10 text-muted-foreground hover:text-red-500 transition" title="Hide skill">
                    <EyeSlash className="w-3 h-3" />
                  </button>
                  <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); setSelectedSkill(skill); }} className="h-5 text-[0.5rem] gap-0.5">
                    <TreeStructure className="w-2.5 h-2.5" /> Generate
                  </Button>
                </div>
              ))}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-[1fr_320px] gap-4">
        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <TrendUp className="w-5 h-5 text-green-500" />
              <h4 className="font-extrabold text-sm">Strengths</h4>
              <Badge variant="secondary" className="text-[0.5rem] bg-green-500/15 text-green-500">{strengths.length}</Badge>
            </div>
            <div className="space-y-1">
              {strengths.length > 0 ? strengths.map((s, i) => <SkillRow key={i} skill={s} type="strength" onClick={setSelectedSkill} roadmapProgress={roadmapProgress} onHide={handleHideSkill} />) : <div className="text-xs text-muted-foreground">No strengths identified yet</div>}
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <BookOpen className="w-5 h-5 text-red-500" />
              <h4 className="font-extrabold text-sm">Skill Gaps</h4>
              <Badge variant="secondary" className="text-[0.5rem] bg-red-500/15 text-red-500">{gaps.length}</Badge>
            </div>
            <div className="space-y-1">
              {gaps.length > 0 ? gaps.map((g, i) => <SkillRow key={i} skill={g} type="gap" onClick={setSelectedSkill} roadmapProgress={roadmapProgress} onHide={handleHideSkill} />) : <div className="text-xs text-muted-foreground">No major gaps identified</div>}
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Brain className="w-5 h-5 text-primary" />
              <h4 className="font-extrabold text-sm">Learning Recommendations</h4>
            </div>
            <div className="space-y-2">
              {recommendations.length > 0 ? recommendations.map((r, i) => <RecommendationCard key={i} rec={r} onClick={setSelectedSkill} roadmapProgress={roadmapProgress} />) : <div className="text-xs text-muted-foreground text-center py-4">No recommendations yet</div>}
            </div>
          </Card>
        </div>
      </div>

      <SkillRoadmapDrawer skillName={selectedSkill} open={!!selectedSkill} onOpenChange={(open) => { if (!open) setSelectedSkill(null); }} onRefreshProgress={onRefreshProgress} />
    </div>
  );
}
