import { useState, useEffect, useCallback } from "react";
import {
  X, TrendUp, Brain, BookOpen, EyeSlash, GitMerge, TreeStructure,
  Link, Target, Lightbulb, Spinner, CaretDown, CaretRight, Check, PencilSimple,
} from "@phosphor-icons/react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import {
  Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription,
} from "@/components/ui/sheet";

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
      <div className={cn("flex items-center gap-1.5 py-1 px-1 rounded hover:bg-muted/50 transition text-[0.6rem]",
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
  roadmapProgress = {}, onHide, onGenerate,
}) {
  const [relationships, setRelationships] = useState([]);
  const [aliases, setVariantes] = useState([]);
  const [roadmapItems, setRoadmapItems] = useState([]);
  const [roadmapExpanded, setRoadmapExpanded] = useState(false);
  const [checked, setChecked] = useState({});
  const [loading, setLoading] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState("");

  const skill = techStackSkills.find((s) => s.name === skillName) || {};

  const handleRename = async () => {
    const newName = renameValue.trim();
    if (!newName || newName === skillName || !skill.id) return;
    try {
      const res = await fetch(`${API}/tech-stack/${skill.id}/rename`, {
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
      setRoadmapItems(data.roadmap || []);
    } catch { setRoadmapItems([]); }
  }, [skillName, open]);

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

  if (!skillName) return null;

  const prog = roadmapProgress[skillName];
  const hasRoadmap = prog && prog.total > 0;
  const evidence = (() => { try { return JSON.parse(skill.evidence || "[]"); } catch { return []; } })();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[400px] sm:w-[450px] p-0 flex flex-col">
        <SheetHeader className="p-6 pb-3">
          <SheetTitle className="flex items-center gap-2 text-base">
            {renaming ? (
              <div className="flex items-center gap-1.5 flex-1">
                <Input value={renameValue} onChange={(e) => setRenameValue(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") handleRename(); if (e.key === "Escape") setRenaming(false); }}
                  className="h-7 text-sm flex-1" autoFocus />
                <Button size="sm" variant="ghost" onClick={handleRename} className="h-7 text-[0.6rem]">Save</Button>
                <Button size="sm" variant="ghost" onClick={() => setRenaming(false)} className="h-7 text-[0.6rem]">Cancel</Button>
              </div>
            ) : (
              <>
                {skillName}
                {skill.category && (
                  <Badge variant="secondary" className={cn("text-[0.5rem]", CATEGORY_COLORS[skill.category] || "bg-gray-500/15 text-gray-400")}>
                    {skill.category}
                  </Badge>
                )}
                <Button size="ghost" variant="ghost" onClick={() => { setRenaming(true); setRenameValue(skillName); }}
                  className="h-5 w-5 p-0 text-muted-foreground hover:text-foreground">
                  <PencilSimple className="w-3 h-3" />
                </Button>
              </>
            )}
          </SheetTitle>
          <SheetDescription className="flex items-center gap-2">
            {skill.source && <Badge variant="secondary" className="text-[0.5rem]">{skill.source?.replace("_", " ")}</Badge>}
            {skill.confidence > 0 && (
              <span className="text-[0.55rem] text-muted-foreground">Confidence: {Math.round(skill.confidence * 100)}%</span>
            )}
          </SheetDescription>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto px-6 pb-6 space-y-4">
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
                  <div key={i} className="text-[0.65rem] text-muted-foreground flex items-start gap-1.5">
                    <span className="text-yellow-500 shrink-0">•</span> {e}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Proficiency Level */}
          {skill.level && (
            <Card className="p-3">
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-4 h-4 text-green-500" />
                <span className="text-xs font-bold">Proficiency Level</span>
              </div>
              <Badge variant="secondary" className={cn("text-[0.55rem]",
                skill.level >= 4 ? "bg-green-500/15 text-green-500" :
                skill.level >= 3 ? "bg-blue-500/15 text-blue-500" :
                skill.level >= 2 ? "bg-yellow-500/15 text-yellow-500" : "bg-orange-500/15 text-orange-500"
              )}>
                {skill.level >= 4 ? "Expert" : skill.level >= 3 ? "Advanced" : skill.level >= 2 ? "Intermediate" : "Beginner"}
              </Badge>
            </Card>
          )}

          {/* Merged Variantes */}
          {aliases.length > 0 && (
            <Card className="p-3">
              <div className="flex items-center gap-2 mb-2">
                <GitMerge className="w-4 h-4 text-amber-500" />
                <span className="text-xs font-bold">Merged Skills</span>
                <Badge variant="secondary" className="text-[0.4rem] h-2.5 bg-amber-500/15 text-amber-600">{aliases.length}</Badge>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {aliases.map((alias) => (
                  <Badge key={alias} variant="secondary" className="text-[0.5rem] h-4 bg-amber-500/10 text-amber-600 border border-amber-500/20">
                    {alias}
                  </Badge>
                ))}
              </div>
              <div className="text-[0.5rem] text-muted-foreground mt-1.5">
                These skills are variants of {skillName} — they were merged into this skill.
              </div>
            </Card>
          )}

          {/* Learning Roadmap — collapsible with items */}
          {hasRoadmap && (
            <Card className="p-3">
              <button onClick={() => setRoadmapExpanded(!roadmapExpanded)}
                className="flex items-center gap-2 mb-2 w-full text-left">
                {roadmapExpanded ? <CaretDown className="w-3 h-3" /> : <CaretRight className="w-3 h-3" />}
                <TreeStructure className="w-4 h-4 text-emerald-500" />
                <span className="text-xs font-bold">Learning Roadmap</span>
                <Badge variant="secondary" className="text-[0.4rem] h-2.5 bg-emerald-500/15 text-emerald-500">
                  {prog.completed}/{prog.total}
                </Badge>
                <div className="flex-1" />
                <span className="text-[0.5rem] text-muted-foreground">{prog.pct}%</span>
              </button>
              <div className="flex items-center gap-2 mb-2">
                <Progress value={prog.pct} className="h-1.5 flex-1" />
              </div>
              {roadmapExpanded && roadmapItems.length > 0 && (
                <div className="space-y-1 mt-2 border-t pt-2 max-h-[200px] overflow-y-auto">
                  {roadmapItems.map((item) => (
                    <RoadmapItem key={item.id} item={item} checked={checked} onToggle={handleToggle} />
                  ))}
                </div>
              )}
            </Card>
          )}

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
                      <Badge variant="secondary" className={cn("text-[0.4rem] h-2.5 shrink-0", relInfo.color)}>
                        {relInfo.label}
                      </Badge>
                      <span className="text-xs font-semibold">{otherName}</span>
                      {rel.confidence > 0 && (
                        <span className="text-[0.5rem] text-muted-foreground ml-auto">{Math.round(rel.confidence * 100)}%</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          {/* Actions */}
          <div className="flex gap-2">
            {!hasRoadmap && (
              <Button size="sm" onClick={() => { onGenerate?.(skillName); onOpenChange?.(false); }}
                className="gap-1 h-7 text-[0.6rem]">
                <TreeStructure className="w-3 h-3" /> Generate Roadmap
              </Button>
            )}
            <Button size="sm" variant="outline" onClick={() => { onHide?.(skillName); onOpenChange?.(false); }}
              className="gap-1 h-7 text-[0.6rem] text-red-500 hover:bg-red-500/10">
              <EyeSlash className="w-3 h-3" /> Hide Skill
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
