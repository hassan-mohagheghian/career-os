import { useState, useEffect, useCallback } from "react";
import {
  X, TrendUp, Brain, BookOpen, EyeSlash, GitMerge, TreeStructure,
  Link, Target, Lightbulb, Spinner, CaretDown, CaretRight, Check, PencilSimple, Tag,
  ArrowsClockwise, Plus,
} from "@phosphor-icons/react";
import { cn } from "@/shared/lib/utils";
import { toast } from "sonner";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import { Card } from "@/shared/ui/card";
import { Progress } from "@/shared/ui/progress";
import { Input } from "@/shared/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/shared/ui/tabs";
import { AppDrawer } from "@/shared/components/DrawerComponents";
import GenerationProgressCard from "@/shared/components/GenerationProgressCard";
import GenerationHistoryItem from "@/shared/components/GenerationHistoryItem";
import { useLocalHistory } from "@/shared/hooks";
import { useSocketIO, watchSkills, unwatchSkills } from "@/shared/hooks/useSocketIO";

const API = "/api";

const CATEGORY_COLORS = {
  technical: "bg-blue-500/15 text-blue-500",
  engineering: "bg-green-500/15 text-green-500",
  professional: "bg-purple-500/15 text-purple-500",
  domain: "bg-yellow-500/15 text-yellow-500",
  career: "bg-cyan-500/15 text-cyan-500",
};

const RELATION_LABELS = {
  related: { label: "Related", color: "bg-blue-500/15 text-blue-500" },
  similar: { label: "Similar", color: "bg-green-500/15 text-green-500" },
  parent: { label: "Parent", color: "bg-purple-500/15 text-purple-500" },
  child: { label: "Child", color: "bg-orange-500/15 text-orange-500" },
  alternative: { label: "Alternative", color: "bg-cyan-500/15 text-cyan-500" },
};

function RoadmapItem({ item, checked, onToggle, depth = 0 }) {
  const [expanded, setExpanded] = useState(depth < 2);
  const hasChildren = item.children && item.children.length > 0;
  const isComplete = checked[item.id] === 1;

  const handleToggle = () => {
    const newVal = isComplete ? 0 : 1;
    // Toggle all children too
    const childIds = [];
    const collectChildren = (node) => {
      if (node.children) {
        for (const child of node.children) {
          childIds.push(child.id);
          collectChildren(child);
        }
      }
    };
    collectChildren(item);
    onToggle(item.id, newVal, childIds);
  };

  return (
    <div className={cn("select-none", depth > 0 && "ml-3")}>
      <div className={cn("flex items-center gap-1.5 py-1 px-1 rounded hover:bg-muted/50 transition text-2xs",
        isComplete && "bg-green-500/5"
      )}>
        <button className="shrink-0 w-3 h-3 flex items-center justify-center" onClick={() => hasChildren && setExpanded(!expanded)}>
          {hasChildren ? (expanded ? <CaretDown className="w-2.5 h-2.5" /> : <CaretRight className="w-2.5 h-2.5" />) : <span className="w-2.5" />}
        </button>
        <button onClick={handleToggle} className={cn("shrink-0 w-3.5 h-3.5 rounded border flex items-center justify-center transition",
          isComplete ? "bg-green-500 border-green-500 text-white" : "border-border hover:border-primary"
        )}>
          {isComplete && <Check className="w-2 h-2" />}
        </button>
        <span className={cn("truncate", isComplete && "line-through text-muted-foreground")}>{item.title}</span>
      </div>
      {hasChildren && expanded && item.children.map((child) => (
        <RoadmapItem key={child.id} item={child} checked={checked} onToggle={onToggle} depth={depth + 1} />
      ))}
    </div>
  );
}

export default function SkillDetailDrawer({
  skillName, open, onOpenChange, techStackSkills = [],
  roadmapProgress = {}, onHide,
}) {
  const socket = useSocketIO();
  const [relationships, setRelationships] = useState([]);
  const [aliases, setVariantes] = useState([]);
  const [roadmapItems, setRoadmapItems] = useState([]);
  const [roadmapExpanded, setRoadmapExpanded] = useState(false);
  const [checked, setChecked] = useState({});
  const [loading, setLoading] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState("");
  const [tags, setTags] = useState([]);
  const [tagInput, setTagInput] = useState("");
  const [marketJobs, setMarketJobs] = useState<any[]>([]);
  const [genProgress, setGenProgress] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<"details" | "roadmap">("details");

  const { items: localHistory, singleRunning } = useLocalHistory({
    context: 'skill',
    skill_name: skillName,
    enabled: !!skillName && open,
  });

  const skill = techStackSkills.find((s) => s.name === skillName) || {};

  const handleRename = async () => {
    const newName = renameValue.trim();
    if (!newName || newName === skillName || !skill.id) return;
    try {
      const res = await fetch(`${API}/skills/${skill.id}/rename`, {
        method: "PATCH", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newName }),
      });
      const result = await res.json();
      if (res.ok) {
        toast.success(`Renamed "${skillName}" → "${newName}"`);
        setRenaming(false);
        setRenameValue("");
        onOpenChange?.(false);
      } else {
        toast.error(result.error || "Rename failed");
      }
    } catch { toast.error("Rename failed"); }
  };

  const handleSetLevel = async (level) => {
    if (!skill.id || skill.level === level) return;
    try {
      const res = await fetch(`${API}/skills/${skill.id}`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ level }),
      });
      if (res.ok) {
        toast.success(`Proficiency set to ${["Beginner", "Basic", "Intermediate", "Advanced", "Expert"][level - 1]}`);
        // Force re-render by triggering parent refresh
        onOpenChange?.(true);
      }
    } catch {}
  };

  const fetchRelationships = useCallback(async () => {
    if (!skillName || !open) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/skill-relationships/${encodeURIComponent(skillName)}`);
      const data = await res.json();
      setRelationships(Array.isArray(data) ? data : []);
    } catch { setRelationships([]); }
    setLoading(false);
  }, [skillName, open]);

  const fetchVariantes = useCallback(() => {
    if (!skillName || !open) return;
    // Aliases come from the API via techStackSkills
    const found = techStackSkills.find((s) => s.name === skillName);
    setVariantes(found?.aliases || []);
  }, [skillName, open, techStackSkills]);

  const fetchRoadmap = useCallback(async () => {
    if (!skillName || !open) return;
    try {
      const res = await fetch(`${API}/skill-roadmaps?skill=${encodeURIComponent(skillName)}`);
      const data = await res.json();
      const items = data.roadmap || [];
      setRoadmapItems(items);
      if (items.length > 0) setRoadmapExpanded(true);
    } catch { setRoadmapItems([]); }
  }, [skillName, open]);

  const fetchGenProgress = useCallback(async () => {
    if (!skillName) return null;
    try {
      const res = await fetch(`${API}/skill-roadmaps/progress?skill=${encodeURIComponent(skillName)}`);
      const data = await res.json();
      setGenProgress(data);
      return data;
    } catch { return null; }
  }, [skillName]);

  // SocketIO: real-time generation progress
  useEffect(() => {
    if (!skillName || !open) return;
    watchSkills();
    const handleUpdate = (data) => {
      if (data.skill !== skillName) return;
      setGenProgress((prev) => ({ ...prev, ...data }));
      if (data.status === "completed" || data.status === "failed" || data.status === "cancelled") {
        fetchRoadmap();
      }
    };
    socket.on("skill_roadmap:update", handleUpdate);
    return () => {
      unwatchSkills();
      socket.off("skill_roadmap:update", handleUpdate);
    };
  }, [skillName, open, socket, fetchRoadmap]);

  useEffect(() => {
    if (!open) {
      setGenProgress(null);
    } else {
      fetchGenProgress();
    }
  }, [fetchGenProgress, open]);

  // Load checked state from roadmapProgress
  useEffect(() => {
    if (skillName && open) {
      const prog = roadmapProgress[skillName];
      if (prog?.checked) {
        setChecked(prog.checked);
      } else {
        // Fetch checked state from API
        fetch(`${API}/skill-roadmap-progress?skill=${encodeURIComponent(skillName)}`)
          .then(r => r.json())
          .then(data => setChecked(data || {}))
          .catch(() => setChecked({}));
      }
    }
  }, [skillName, open, roadmapProgress]);

  const handleToggle = useCallback(async (itemId, newVal, childIds) => {
    // Optimistic update
    setChecked(prev => {
      const next = { ...prev, [itemId]: newVal };
      for (const cid of childIds) next[cid] = newVal;
      return next;
    });
    try {
      await fetch(`${API}/skill-roadmap-progress/${itemId}`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ completed: newVal }),
      });
      for (const cid of childIds) {
        await fetch(`${API}/skill-roadmap-progress/${cid}`, {
          method: "PUT", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ completed: newVal }),
        });
      }
    } catch {
      // Revert on error
      setChecked(prev => {
        const next = { ...prev, [itemId]: newVal ? 0 : 1 };
        for (const cid of childIds) next[cid] = newVal ? 0 : 1;
        return next;
      });
    }
  }, []);

  useEffect(() => { fetchRelationships(); fetchVariantes(); fetchRoadmap(); }, [fetchRelationships, fetchVariantes, fetchRoadmap]);

  // Fetch jobs that mention this skill in their stack
  useEffect(() => {
    if (!open || !skillName) return;
    fetch(`${API}/jobs?limit=50&sort_by=overall_score&sort_dir=desc`)
      .then(r => r.ok ? r.json() : { jobs: [] })
      .then(d => {
        const jobs = (d.jobs || []).filter((j: any) => {
          const stack = (j.stack || '').toLowerCase();
          return stack.includes(skillName.toLowerCase());
        });
        setMarketJobs(jobs.slice(0, 5));
      })
      .catch(() => setMarketJobs([]));
  }, [open, skillName]);

  // Load tags from skill data when drawer opens
  useEffect(() => {
    if (open && skill.tags) {
      setTags(Array.isArray(skill.tags) ? skill.tags : []);
    }
  }, [open, skillName, skill.tags]);

  const handleAddTag = async () => {
    const tag = tagInput.trim();
    if (!tag || tags.includes(tag) || !skill.id) return;
    const newTags = [...tags, tag];
    try {
      const res = await fetch(`${API}/skills/${skill.id}`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tags: newTags }),
      });
      if (res.ok) { setTags(newTags); setTagInput(""); }
    } catch {}
  };

  const handleRemoveTag = async (tag) => {
    if (!skill.id) return;
    const newTags = tags.filter((t) => t !== tag);
    try {
      const res = await fetch(`${API}/skills/${skill.id}`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tags: newTags }),
      });
      if (res.ok) setTags(newTags);
    } catch {}
  };

  if (!skillName) return null;

  const prog = roadmapProgress[skillName];
  const hasRoadmap = (prog && prog.total > 0) || roadmapItems.length > 0;
  const evidence = (() => { try { return JSON.parse(skill.evidence || "[]"); } catch { return []; } })();

  return (
    <AppDrawer open={open} onOpenChange={onOpenChange}>
        <div className="p-6 pb-3">
          <div className="flex items-center gap-2 text-base">
            {renaming ? (
              <div className="flex items-center gap-1.5 flex-1">
                <Input value={renameValue} onChange={(e) => setRenameValue(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") handleRename(); if (e.key === "Escape") setRenaming(false); }}
                  className="h-7 text-sm flex-1" autoFocus />
                <Button size="sm" variant="ghost" onClick={handleRename} className="h-7 text-2xs">Save</Button>
                <Button size="sm" variant="ghost" onClick={() => setRenaming(false)} className="h-7 text-2xs">Cancel</Button>
              </div>
            ) : (
              <>
                {skillName}
                {skill.category && (
                  <Badge variant="secondary" className={cn("text-2xs", CATEGORY_COLORS[skill.category] || "bg-gray-500/15 text-gray-400")}>
                    {skill.category}
                  </Badge>
                )}
                <Button size="ghost" variant="ghost" onClick={() => { setRenaming(true); setRenameValue(skillName); }}
                  className="h-5 w-5 p-0 text-muted-foreground hover:text-foreground">
                  <PencilSimple className="w-3 h-3" />
                </Button>
              </>
            )}
          </div>
          <div className="flex items-center gap-2 text-2xs text-muted-foreground">
            {skill.source && <Badge variant="secondary" className="text-2xs">{skill.source?.replace("_", " ")}</Badge>}
            {skill.confidence > 0 && (
              <span className="text-2xs text-muted-foreground">Confidence: {Math.round(skill.confidence * 100)}%</span>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="px-6 pb-2">
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)}>
            <TabsList className="bg-muted h-8">
              <TabsTrigger value="details" className="text-2xs h-6">Details</TabsTrigger>
              <TabsTrigger value="roadmap" className="text-2xs h-6 gap-1">
                <TreeStructure className="w-2.5 h-2.5" /> Roadmap
                {hasRoadmap && <Badge variant="secondary" className="text-3xs h-2 ml-0.5">{prog.pct}%</Badge>}
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        <div className="flex-1 overflow-y-auto px-6 pb-6 space-y-4">
          {/* ═══ Details Tab ═══ */}
          {activeTab === "details" && (
            <>
              {/* Market Demand */}
              {skill.market_relevance > 0 && (
                <Card className="p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendUp className="w-4 h-4 text-primary" />
                    <span className="text-xs font-bold">Market Demand</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Progress value={skill.market_relevance} className="h-2 flex-1" />
                    <span className="text-sm font-extrabold text-primary">{Math.round(skill.market_relevance)}%</span>
                  </div>
                </Card>
              )}

              {/* Evidence */}
              {evidence.length > 0 && (
                <Card className="p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Lightbulb className="w-4 h-4 text-yellow-500" />
                    <span className="text-xs font-bold">Why This Skill Matters</span>
                  </div>
                  <div className="space-y-1.5">
                    {evidence.map((e, i) => (
                      <div key={i} className="text-xs text-muted-foreground flex items-start gap-1.5">
                        <span className="text-yellow-500 shrink-0">•</span> {e}
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Job Market Evidence */}
              {marketJobs.length > 0 && (
                <Card className="p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Target className="w-4 h-4 text-blue-500" />
                    <span className="text-xs font-bold">Job Market</span>
                    <Badge variant="secondary" className="text-3xs h-2.5 bg-blue-500/15 text-blue-500">
                      {marketJobs.length} jobs
                    </Badge>
                  </div>
                  <div className="space-y-1.5">
                    {marketJobs.map((job) => (
                      <div key={job.num} className="flex items-center gap-2 text-2xs">
                        {job.score && (
                          <Badge variant="secondary" className={cn("text-3xs h-2 shrink-0",
                            job.score === 'A++' || job.score === 'A+' ? "bg-green-500/15 text-green-500" :
                            job.score === 'A' || job.score === 'B' ? "bg-blue-500/15 text-blue-500" :
                            "bg-muted text-muted-foreground"
                          )}>{job.score}</Badge>
                        )}
                        <span className="font-medium truncate">{job.role || 'Unknown Role'}</span>
                        <span className="text-muted-foreground truncate">{job.company}</span>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Proficiency Level */}
              <Card className="p-3">
                <div className="flex items-center gap-2 mb-2">
                  <Target className="w-4 h-4 text-green-500" />
                  <span className="text-xs font-bold">Proficiency Level</span>
                </div>
                <div className="flex gap-1.5">
                  {[1, 2, 3, 4, 5].map((lvl) => {
                    const labels = { 1: "Beginner", 2: "Basic", 3: "Intermediate", 4: "Advanced", 5: "Expert" };
                    const colors = {
                      1: "bg-orange-500/15 text-orange-500 border-orange-500/30",
                      2: "bg-yellow-500/15 text-yellow-500 border-yellow-500/30",
                      3: "bg-blue-500/15 text-blue-500 border-blue-500/30",
                      4: "bg-green-500/15 text-green-500 border-green-500/30",
                      5: "bg-emerald-500/15 text-emerald-500 border-emerald-500/30",
                    };
                    const isActive = skill.level === lvl;
                    return (
                      <button key={lvl} onClick={() => handleSetLevel(lvl)}
                        className={cn("px-2 py-1 rounded text-2xs font-semibold border transition",
                          isActive ? colors[lvl] : "bg-muted text-muted-foreground border-transparent hover:bg-muted/80"
                        )}>
                        {labels[lvl]}
                      </button>
                    );
                  })}
                </div>
              </Card>

              {/* Merged Variantes */}
              {aliases.length > 0 && (
                <Card className="p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <GitMerge className="w-4 h-4 text-amber-500" />
                    <span className="text-xs font-bold">Merged Skills</span>
                    <Badge variant="secondary" className="text-3xs h-2.5 bg-amber-500/15 text-amber-600">{aliases.length}</Badge>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {aliases.map((alias) => (
                      <Badge key={alias} variant="secondary" className="text-2xs h-4 bg-amber-500/10 text-amber-600 border border-amber-500/20">
                        {alias}
                      </Badge>
                    ))}
                  </div>
                  <div className="text-2xs text-muted-foreground mt-1.5">
                    These skills are variants of {skillName} — they were merged into this skill.
                  </div>
                </Card>
              )}

              {/* Tags */}
              <Card className="p-3">
                <div className="flex items-center gap-2 mb-2">
                  <Tag className="w-4 h-4 text-orange-500" />
                  <span className="text-xs font-bold">Tags</span>
                </div>
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="text-2xs h-4 bg-orange-500/10 text-orange-600 border border-orange-500/20 gap-1 pr-1">
                      {tag}
                      <button onClick={() => handleRemoveTag(tag)} className="ml-0.5 hover:text-red-500 transition">&times;</button>
                    </Badge>
                  ))}
                  {tags.length === 0 && <span className="text-2xs text-muted-foreground">No tags</span>}
                </div>
                <div className="flex gap-1">
                  <Input value={tagInput} onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleAddTag()}
                    placeholder="Add tag..." className="h-6 text-2xs flex-1" />
                  <Button size="sm" variant="outline" onClick={handleAddTag} disabled={!tagInput.trim()}
                    className="h-6 text-2xs px-2">Add</Button>
                </div>
              </Card>

              {/* Related Skills */}
              {relationships.length > 0 && (
                <Card className="p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Link className="w-4 h-4 text-cyan-500" />
                    <span className="text-xs font-bold">Related Skills</span>
                  </div>
                  <div className="space-y-1.5">
                    {relationships.map((rel) => {
                      const otherName = rel.skill_name === skillName ? rel.related_name : rel.skill_name;
                      const relInfo = RELATION_LABELS[rel.relation_type] || RELATION_LABELS.related;
                      return (
                        <div key={rel.id} className="flex items-center gap-2">
                          <Badge variant="secondary" className={cn("text-3xs h-2.5 shrink-0", relInfo.color)}>
                            {relInfo.label}
                          </Badge>
                          <span className="text-xs font-semibold">{otherName}</span>
                          {rel.confidence > 0 && (
                            <span className="text-2xs text-muted-foreground ml-auto">{Math.round(rel.confidence * 100)}%</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </Card>
              )}

              {/* Hide Skill */}
              <Button size="sm" variant="outline" onClick={() => { onHide?.(skillName); onOpenChange?.(false); }}
                className="gap-1 h-7 text-2xs text-red-500 hover:bg-red-500/10">
                <EyeSlash className="w-3 h-3" /> Hide Skill
              </Button>
            </>
          )}

          {/* ═══ Roadmap Tab ═══ */}
          {activeTab === "roadmap" && (
            <>
              {/* Generation Progress */}
              {genProgress && (genProgress.status === 'running' || genProgress.status === 'queued') && (
                <div className="space-y-2">
                  <GenerationProgressCard
                    title={skillName}
                    progress={{ running: true, ...genProgress }}
                    onCancel={async () => {
                      try {
                        await fetch(`${API}/skill-roadmaps/cancel?skill=${encodeURIComponent(skillName)}`, { method: "POST" });
                        setGenProgress((prev) => ({ ...prev, status: "cancelled", message: "Cancelled" }));
                      } catch {}
                    }}
                  />
                  {genProgress.session_id && (
                    <button
                      className="flex items-center gap-1.5 text-2xs bg-muted px-1.5 py-0.5 rounded font-mono hover:bg-muted/80 transition cursor-pointer w-fit"
                      onClick={() => {
                        navigator.clipboard.writeText(genProgress.session_id);
                        toast.success("Session ID copied");
                      }}
                      title={`Click to copy: ${genProgress.session_id}`}
                    >
                      <span className="text-muted-foreground">{genProgress.provider_name || 'ai'}</span>
                      <span className="text-foreground">({genProgress.session_id})</span>
                    </button>
                  )}
                </div>
              )}

              {/* Action buttons */}
              <div className="flex items-center gap-1.5">
                {hasRoadmap && !genProgress?.status?.match(/running|queued/) && (
                  <>
                    <Button size="sm" variant="outline" onClick={async () => {
                        try {
                          await fetch(`${API}/skill-roadmaps/generate`, {
                            method: "POST", headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ skill_name: skillName }),
                          });
                          setGenProgress({ status: "queued", step: 0, total_steps: 4, message: "Regenerating...", job_type: "generate" });
                          toast.success(`Regenerating roadmap for ${skillName}`);
                        } catch { toast.error("Failed to start"); }
                      }} className="gap-1 h-6 text-2xs">
                      <ArrowsClockwise className="w-2.5 h-2.5" /> Regenerate
                    </Button>
                    <Button size="sm" variant="outline" onClick={async () => {
                        try {
                          await fetch(`${API}/skill-roadmaps/extend`, {
                            method: "POST", headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ skill_name: skillName }),
                          });
                          setGenProgress({ status: "queued", step: 0, total_steps: 4, message: "Extending...", job_type: "extend" });
                          toast.success(`Extending roadmap for ${skillName}`);
                        } catch { toast.error("Failed to start"); }
                      }} className="gap-1 h-6 text-2xs">
                      <Plus className="w-2.5 h-2.5" /> Extend
                    </Button>
                    <Button size="sm" variant="outline" onClick={async () => {
                        try {
                          await fetch(`${API}/skill-roadmaps/finegrain`, {
                            method: "POST", headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ skill_name: skillName }),
                          });
                          setGenProgress({ status: "queued", step: 0, total_steps: 4, message: "Fine-graining...", job_type: "finegrain" });
                          toast.success(`Fine-graining roadmap for ${skillName}`);
                        } catch { toast.error("Failed to start"); }
                      }} className="gap-1 h-6 text-2xs">
                      <Target className="w-2.5 h-2.5" /> Finegrain
                    </Button>
                  </>
                )}
                {!hasRoadmap && !genProgress?.status?.match(/running|queued/) && (
                  <Button size="sm" onClick={async () => {
                      try {
                        await fetch(`${API}/skill-roadmaps/generate`, {
                          method: "POST", headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ skill_name: skillName }),
                        });
                        setGenProgress({ status: "queued", step: 0, total_steps: 4, message: "Queued...", job_type: "generate" });
                        toast.success(`Generating roadmap for ${skillName}`);
                      } catch { toast.error("Failed to start"); }
                    }} className="gap-1 h-6 text-2xs">
                    <TreeStructure className="w-2.5 h-2.5" /> Generate Roadmap
                  </Button>
                )}
              </div>

              {/* Generation history */}
              {localHistory.length > 0 && (
                <div className="space-y-0.5">
                  <span className="text-2xs text-muted-foreground font-medium">Recent generations</span>
                  {localHistory.slice(0, 5).map((item) => (
                    <GenerationHistoryItem key={`${item.source}-${item.id}`} item={item} compact />
                  ))}
                </div>
              )}

              {/* Roadmap progress bar */}
              {hasRoadmap && (
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-2xs text-muted-foreground">Progress</span>
                    <span className="text-2xs text-muted-foreground">{prog.completed}/{prog.total} ({prog.pct}%)</span>
                  </div>
                  <Progress value={prog.pct} className="h-1.5" />
                </div>
              )}

              {/* Roadmap tree */}
              {roadmapItems.length > 0 && (
                <div className="space-y-1 max-h-[300px] overflow-y-auto">
                  {roadmapItems.map((item) => (
                    <RoadmapItem key={item.id} item={item} checked={checked} onToggle={handleToggle} />
                  ))}
                </div>
              )}
              {roadmapItems.length === 0 && !genProgress?.status?.match(/running|queued/) && (
                <div className="text-2xs text-muted-foreground text-center py-4">
                  No roadmap yet. Click Generate to create one.
                </div>
              )}
            </>
          )}
        </div>
    </AppDrawer>
  );
}
