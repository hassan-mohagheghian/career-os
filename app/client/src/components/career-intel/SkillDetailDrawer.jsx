import { useState, useEffect, useCallback } from "react";
import {
  X, TrendUp, Brain, BookOpen, EyeSlash, GitMerge, TreeStructure,
  Link, Target, Lightbulb, Spinner,
} from "@phosphor-icons/react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
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

export default function SkillDetailDrawer({
  skillName, open, onOpenChange, techStackSkills = [],
  roadmapProgress = {}, onHide, onGenerate,
}) {
  const [relationships, setRelationships] = useState([]);
  const [loading, setLoading] = useState(false);

  const skill = techStackSkills.find((s) => s.name === skillName) || {};

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

  useEffect(() => { fetchRelationships(); }, [fetchRelationships]);

  if (!skillName) return null;

  const prog = roadmapProgress[skillName];
  const hasRoadmap = prog && prog.total > 0;
  const evidence = (() => { try { return JSON.parse(skill.evidence || "[]"); } catch { return []; } })();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[400px] sm:w-[450px] p-0 flex flex-col">
        <SheetHeader className="p-6 pb-3">
          <SheetTitle className="flex items-center gap-2 text-base">
            {skillName}
            {skill.category && (
              <Badge variant="secondary" className={cn("text-[0.5rem]", CATEGORY_COLORS[skill.category] || "bg-gray-500/15 text-gray-400")}>
                {skill.category}
              </Badge>
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

          {/* Roadmap Progress */}
          {hasRoadmap && (
            <Card className="p-3">
              <div className="flex items-center gap-2 mb-2">
                <TreeStructure className="w-4 h-4 text-emerald-500" />
                <span className="text-xs font-bold">Learning Roadmap</span>
              </div>
              <div className="flex items-center gap-2">
                <Progress value={prog.pct} className="h-2 flex-1" />
                <span className="text-sm font-extrabold">{prog.completed}/{prog.total}</span>
              </div>
              <div className="text-[0.55rem] text-muted-foreground mt-1">{prog.pct}% complete</div>
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
