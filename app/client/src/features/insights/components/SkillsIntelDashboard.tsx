import { useState, useMemo, useEffect, useCallback } from "react";
import {
  Brain, Target, TrendUp, Warning, BookOpen, Wrench, Users,
  Lightning, ArrowRight, TreeStructure, Clock, CaretDown, CaretRight,
  ArrowsClockwise,
} from "@phosphor-icons/react";
import { cn } from "@/shared/lib/utils";
import { toast } from "sonner";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import { Card } from "@/shared/ui/card";
import { Progress } from "@/shared/ui/progress";
import { Tabs, TabsList, TabsTrigger } from "@/shared/ui/tabs";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import SkillRoadmapDrawer from "./SkillRoadmapDrawer";

const API = "/api";

const CATEGORY_COLORS: Record<string, string> = {
  technical: "bg-blue-500/15 text-blue-500",
  engineering: "bg-green-500/15 text-green-500",
  professional: "bg-purple-500/15 text-purple-500",
  domain: "bg-yellow-500/15 text-yellow-500",
  career: "bg-cyan-500/15 text-cyan-500",
};

const PRIORITY_COLORS: Record<string, string> = {
  P1: "bg-red-500/15 text-red-500",
  P2: "bg-yellow-500/15 text-yellow-600",
  P3: "bg-blue-500/15 text-blue-500",
};

const GAP_COLORS: Record<string, string> = {
  critical: "text-red-500",
  high: "text-orange-500",
  medium: "text-yellow-500",
  low: "text-green-500",
};

function ReadinessGauge({ score }: { score: number }) {
  const color = score >= 70 ? "text-green-500" : score >= 40 ? "text-yellow-500" : "text-red-500";
  const bgColor = score >= 70 ? "stroke-green-500" : score >= 40 ? "stroke-yellow-500" : "stroke-red-500";
  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative w-24 h-24 flex items-center justify-center">
      <svg className="w-24 h-24 -rotate-90" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" strokeWidth="6"
          className="text-muted/30" />
        <circle cx="50" cy="50" r="40" fill="none" strokeWidth="6"
          strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round" className={bgColor} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={cn("text-xl font-extrabold", color)}>{score}</span>
        <span className="text-3xs text-muted-foreground">/ 100</span>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, subtext, color }: {
  icon: React.ReactNode; label: string; value: number | string;
  subtext?: string; color?: string;
}) {
  return (
    <Card className="p-3 flex flex-col gap-1.5">
      <div className="flex items-center gap-1.5">
        <div className={cn("w-6 h-6 rounded flex items-center justify-center", color || "bg-primary/10")}>
          {icon}
        </div>
        <span className="text-2xs text-muted-foreground font-medium">{label}</span>
      </div>
      <div className="text-lg font-extrabold">{value}</div>
      {subtext && <span className="text-2xs text-muted-foreground">{subtext}</span>}
    </Card>
  );
}

function MarketDemandChart({ data }: { data: any[] }) {
  if (!data || data.length === 0) {
    return (
      <Card className="p-4">
        <h4 className="font-extrabold text-xs mb-3">Market Demand</h4>
        <p className="text-2xs text-muted-foreground text-center py-4">No market data available. Run skills intelligence to generate.</p>
      </Card>
    );
  }

  const chartData = data.slice(0, 10).map(d => ({
    name: d.skill.length > 12 ? d.skill.slice(0, 12) + '…' : d.skill,
    demand: d.demand || d.demand_percentage || 0,
    fullSkill: d.skill,
  }));

  return (
    <Card className="p-4">
      <h4 className="font-extrabold text-xs mb-3">Top Skills by Market Demand</h4>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={chartData} margin={{ top: 5, right: 5, bottom: 25, left: 5 }}>
          <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-35} textAnchor="end" interval={0} />
          <YAxis tick={{ fontSize: 10 }} domain={[0, 100]} />
          <Tooltip
            formatter={(value: number) => [`${value}%`, 'Demand']}
            labelFormatter={(label: string) => chartData.find(d => d.name === label)?.fullSkill || label}
            contentStyle={{ fontSize: 11, borderRadius: 8 }}
          />
          <Bar dataKey="demand" radius={[4, 4, 0, 0]} maxBarSize={32}>
            {chartData.map((entry, idx) => (
              <Cell key={idx} fill={entry.demand >= 70 ? "#22c55e" : entry.demand >= 40 ? "#eab308" : "#3b82f6"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}

function GapMatrix({ gaps, activeCategory }: { gaps: any[]; activeCategory: string }) {
  const filtered = useMemo(() => {
    let result = gaps;
    if (activeCategory !== "all") {
      result = result.filter(g => g.category === activeCategory);
    }
    return result.sort((a, b) => {
      const pOrder = { P1: 0, P2: 1, P3: 2 };
      return (pOrder[a.priority] ?? 3) - (pOrder[b.priority] ?? 3);
    });
  }, [gaps, activeCategory]);

  if (filtered.length === 0) {
    return (
      <Card className="p-4">
        <h4 className="font-extrabold text-xs mb-3">Skill Gap Matrix</h4>
        <p className="text-2xs text-muted-foreground text-center py-4">No gaps identified. Run skills intelligence to analyze.</p>
      </Card>
    );
  }

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-extrabold text-xs">Skill Gap Matrix</h4>
        <Badge variant="secondary" className="text-2xs">{filtered.length} gaps</Badge>
      </div>
      <div className="space-y-1 max-h-[260px] overflow-y-auto">
        {/* Header */}
        <div className="grid grid-cols-[1fr_80px_70px_50px_40px] gap-2 text-2xs text-muted-foreground font-medium px-1 pb-1 border-b border-muted">
          <span>Skill</span>
          <span>Market</span>
          <span>User Level</span>
          <span>Gap</span>
          <span>Priority</span>
        </div>
        {filtered.map((g, i) => (
          <div key={i} className="grid grid-cols-[1fr_80px_70px_50px_40px] gap-2 items-center text-xs px-1 py-1 rounded hover:bg-muted/50">
            <div className="flex items-center gap-1.5 min-w-0">
              <span className="font-semibold truncate">{g.skill}</span>
              {g.category && (
                <Badge variant="secondary" className={cn("text-3xs h-2 shrink-0", CATEGORY_COLORS[g.category])}>
                  {g.category}
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-1">
              <div className="w-12 h-1 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-primary/60 rounded-full" style={{ width: `${Math.min(g.market_demand || 0, 100)}%` }} />
              </div>
              <span className="text-2xs text-muted-foreground">{g.market_demand || 0}%</span>
            </div>
            <span className="text-2xs">{g.current_level || "—"}</span>
            <span className={cn("text-2xs font-semibold", GAP_COLORS[g.gap])}>
              {g.gap || "—"}
            </span>
            <Badge variant="secondary" className={cn("text-3xs h-3 w-7 justify-center", PRIORITY_COLORS[g.priority])}>
              {g.priority}
            </Badge>
          </div>
        ))}
      </div>
    </Card>
  );
}

function RecommendationsSection({ recommendations, onLearn }: { recommendations: any[]; onLearn: (skill: string) => void }) {
  const [expanded, setExpanded] = useState(false);
  const p1Recs = recommendations.filter(r => r.priority === "P1");
  const displayRecs = expanded ? recommendations : p1Recs.slice(0, 5);

  if (recommendations.length === 0) {
    return (
      <Card className="p-4">
        <h4 className="font-extrabold text-xs mb-3">Recommendations</h4>
        <p className="text-2xs text-muted-foreground text-center py-4">No recommendations yet. Run skills intelligence to generate.</p>
      </Card>
    );
  }

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h4 className="font-extrabold text-xs">Recommendations</h4>
          <Badge variant="secondary" className={cn("text-2xs h-3", PRIORITY_COLORS.P1)}>
            {p1Recs.length} P1
          </Badge>
        </div>
        {recommendations.length > 5 && (
          <button onClick={() => setExpanded(!expanded)} className="text-2xs text-primary hover:underline">
            {expanded ? "Show less" : `View all ${recommendations.length}`}
          </button>
        )}
      </div>
      <div className="space-y-2">
        {displayRecs.map((rec, i) => (
          <div key={i} className="p-2.5 rounded-lg bg-muted/30 hover:bg-muted/50 transition">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="font-semibold text-sm">{rec.skill}</span>
                  <Badge variant="secondary" className={cn("text-3xs h-2", PRIORITY_COLORS[rec.priority])}>
                    {rec.priority}
                  </Badge>
                  {rec.category && (
                    <Badge variant="secondary" className={cn("text-3xs h-2", CATEGORY_COLORS[rec.category])}>
                      {rec.category}
                    </Badge>
                  )}
                </div>
                {rec.reasoning && (
                  <p className="text-2xs text-muted-foreground line-clamp-2">{rec.reasoning}</p>
                )}
                <div className="flex items-center gap-3 mt-1.5 text-2xs text-muted-foreground">
                  <span>{rec.current_level} → {rec.target_level}</span>
                  {rec.market_demand > 0 && <span>{rec.market_demand}% demand</span>}
                  {rec.roi_score > 0 && <span>ROI: {rec.roi_score}</span>}
                  {rec.estimated_effort && <span>{rec.estimated_effort}</span>}
                </div>
              </div>
              <Button size="sm" variant="ghost" className="h-6 text-2xs gap-0.5 shrink-0"
                onClick={() => onLearn(rec.skill)}>
                <Lightning className="w-2.5 h-2.5" /> Learn
              </Button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function RoadmapPreview({ roadmap, roadmapProgress }: { roadmap: any; roadmapProgress: Record<string, any> }) {
  const phases = [
    { key: "now", label: "Now", color: "text-green-500", bg: "bg-green-500/10" },
    { key: "next", label: "Next", color: "text-yellow-500", bg: "bg-yellow-500/10" },
    { key: "later", label: "Later", color: "text-blue-500", bg: "bg-blue-500/10" },
  ];

  const hasData = phases.some(p => roadmap?.[p.key]?.length > 0);

  if (!hasData) {
    return (
      <Card className="p-4">
        <h4 className="font-extrabold text-xs mb-3">Learning Roadmap</h4>
        <p className="text-2xs text-muted-foreground text-center py-4">No roadmap available. Generate roadmaps from skill details.</p>
      </Card>
    );
  }

  return (
    <Card className="p-4">
      <h4 className="font-extrabold text-xs mb-3">Learning Roadmap</h4>
      <div className="space-y-3">
        {phases.map(phase => {
          const skills = roadmap?.[phase.key] || [];
          if (skills.length === 0) return null;
          return (
            <div key={phase.key}>
              <div className="flex items-center gap-1.5 mb-1.5">
                <span className={cn("text-xs font-bold", phase.color)}>{phase.label}</span>
                <Badge variant="secondary" className={cn("text-3xs h-2", phase.bg, phase.color)}>
                  {skills.length} skills
                </Badge>
              </div>
              <div className="space-y-1 ml-2">
                {skills.map((skill: string) => {
                  const prog = roadmapProgress[skill];
                  const pct = prog?.pct || 0;
                  return (
                    <div key={skill} className="flex items-center gap-2">
                      <span className="text-2xs font-medium w-28 truncate">{skill}</span>
                      {prog?.total > 0 ? (
                        <>
                          <div className="flex-1 h-1 bg-muted rounded-full overflow-hidden">
                            <div className="h-full bg-primary/60 rounded-full" style={{ width: `${pct}%` }} />
                          </div>
                          <span className="text-3xs text-muted-foreground w-8 text-right">{pct}%</span>
                        </>
                      ) : (
                        <span className="text-3xs text-muted-foreground">No roadmap</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

export default function SkillsIntelDashboard({
  refreshing, onRefresh, status, onOpenDrawer,
}: {
  refreshing?: any; onRefresh?: () => void;
  status?: any; onOpenDrawer?: (num: number) => void;
}) {
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState("all");
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchDashboard = useCallback(() => {
    setLoading(true);
    fetch(`${API}/skills-intelligence/dashboard`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setDashboardData(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchDashboard(); }, [fetchDashboard]);

  // Auto-refresh when insights generation completes
  useEffect(() => {
    if (!refreshing) return;
    if (refreshing.skills_intel === false && !isRunning) {
      fetchDashboard();
    }
  }, [refreshing]);

  // Extract data from the dashboard response
  const data = dashboardData || {};
  const summary = data?.summary || {};
  const topMarketSkills = data?.top_market_skills || [];
  const gapMatrix = data?.gap_matrix || [];
  const categoryStats = data?.category_stats || {};
  const recommendations = data?.recommendations || [];
  const roadmap = data?.roadmap || {};
  const roadmapProgress = data?.roadmap_progress || {};

  // Also merge in data from the intel report if available
  const intelData = data?.intel_report?.data || {};
  const currentState = intelData.current_state || {};
  const strengths = currentState.strengths || [];
  const gaps = currentState.gaps || [];
  const missing = currentState.missing || [];
  const allRecommendations = intelData.recommendations || recommendations;

  // Build gap matrix from intel data if dashboard gap_matrix is empty
  const effectiveGapMatrix = useMemo(() => {
    if (gapMatrix.length > 0) return gapMatrix;
    const result: any[] = [];
    for (const g of gaps) {
      result.push({
        skill: g.skill, category: g.category, market_demand: g.market_demand,
        current_level: g.current_level, gap: "high", priority: "P1", evidence: g.evidence,
      });
    }
    for (const m of missing) {
      result.push({
        skill: m.skill, category: m.category, market_demand: m.demand_percentage,
        current_level: "none", gap: "critical", priority: "P1", evidence: m.evidence,
      });
    }
    return result;
  }, [gapMatrix, gaps, missing]);

  const isRunning = refreshing?.skills_intel || refreshing?.skills || loading;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="font-extrabold text-sm">Skills Intelligence</h3>
          {summary.last_generated && (
            <span className="text-2xs text-muted-foreground/60 flex items-center gap-0.5">
              <Clock className="w-2.5 h-2.5" />
              {new Date(summary.last_generated).toLocaleDateString()}
            </span>
          )}
        </div>
        <Button onClick={() => { onRefresh?.(); setTimeout(fetchDashboard, 2000); }} disabled={isRunning} variant="outline" size="sm" className="gap-1 h-6 text-2xs">
          <ArrowsClockwise className={cn("w-3 h-3", isRunning && "animate-spin")} />
          {isRunning ? "Analyzing..." : "Refresh Intelligence"}
        </Button>
      </div>

      {/* ═══ Section A: Overview Cards ═══ */}
      <div className="grid grid-cols-6 gap-3">
        <Card className="p-3 flex flex-col items-center justify-center gap-1">
          <ReadinessGauge score={summary.career_readiness_score || 0} />
          <span className="text-2xs text-muted-foreground font-medium">Readiness</span>
        </Card>
        <StatCard
          icon={<Brain className="w-3.5 h-3.5 text-blue-500" />}
          label="Total Skills"
          value={summary.total_skills || 0}
          subtext={`${summary.total_jobs_analyzed || 0} jobs analyzed`}
          color="bg-blue-500/10"
        />
        <StatCard
          icon={<Target className="w-3.5 h-3.5 text-green-500" />}
          label="Strengths"
          value={summary.strengths_count || strengths.length}
          subtext={summary.main_strength ? `Best: ${summary.main_strength}` : undefined}
          color="bg-green-500/10"
        />
        <StatCard
          icon={<Warning className="w-3.5 h-3.5 text-orange-500" />}
          label="Skill Gaps"
          value={summary.gaps_count || effectiveGapMatrix.length}
          subtext={summary.biggest_gap ? `Critical: ${summary.biggest_gap}` : undefined}
          color="bg-orange-500/10"
        />
        <StatCard
          icon={<Lightning className="w-3.5 h-3.5 text-yellow-500" />}
          label="High ROI"
          value={summary.high_roi_count || allRecommendations.filter((r: any) => r.priority === "P1").length}
          subtext={summary.highest_roi_skill ? `Top: ${summary.highest_roi_skill}` : undefined}
          color="bg-yellow-500/10"
        />
        <StatCard
          icon={<TreeStructure className="w-3.5 h-3.5 text-purple-500" />}
          label="Roadmaps"
          value={summary.roadmap_skills || Object.keys(roadmapProgress).length}
          subtext={`${Object.values(roadmapProgress).filter((p: any) => (p as any).pct === 100).length} completed`}
          color="bg-purple-500/10"
        />
      </div>

      {/* ═══ Section B: Charts & Gap Matrix ═══ */}
      <div className="grid grid-cols-2 gap-4">
        <MarketDemandChart data={topMarketSkills} />

        <Card className="p-4">
          <h4 className="font-extrabold text-xs mb-3">Category Breakdown</h4>
          {Object.keys(categoryStats).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(categoryStats).map(([cat, stats]: [string, any]) => (
                <div key={cat} className="flex items-center gap-2">
                  <Badge variant="secondary" className={cn("text-2xs h-3 w-20 justify-center", CATEGORY_COLORS[cat])}>
                    {cat}
                  </Badge>
                  <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                    <div className="h-full bg-primary/40 rounded-full"
                      style={{ width: `${Math.min(stats.avg_demand || 0, 100)}%` }} />
                  </div>
                  <span className="text-2xs text-muted-foreground w-12 text-right">{stats.count} skills</span>
                  <span className="text-2xs text-muted-foreground w-10 text-right">{stats.avg_demand || 0}%</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-2xs text-muted-foreground text-center py-4">No category data available.</p>
          )}
        </Card>
      </div>

      {/* Gap Matrix (full width) */}
      <div>
        <Tabs value={activeCategory} onValueChange={setActiveCategory}>
          <TabsList className="bg-muted mb-2">
            <TabsTrigger value="all" className="text-2xs">All Gaps</TabsTrigger>
            <TabsTrigger value="technical" className="text-2xs">Technical</TabsTrigger>
            <TabsTrigger value="engineering" className="text-2xs">Engineering</TabsTrigger>
            <TabsTrigger value="professional" className="text-2xs">Professional</TabsTrigger>
            <TabsTrigger value="domain" className="text-2xs">Domain</TabsTrigger>
            <TabsTrigger value="career" className="text-2xs">Career</TabsTrigger>
          </TabsList>
        </Tabs>
        <GapMatrix gaps={effectiveGapMatrix} activeCategory={activeCategory} />
      </div>

      {/* ═══ Section C: Recommendations + Roadmap ═══ */}
      <div className="grid grid-cols-2 gap-4">
        <RecommendationsSection
          recommendations={allRecommendations}
          onLearn={(skill) => setSelectedSkill(skill)}
        />
        <RoadmapPreview roadmap={roadmap} roadmapProgress={roadmapProgress} />
      </div>

      {/* Skill Roadmap Drawer */}
      <SkillRoadmapDrawer
        skillName={selectedSkill}
        open={!!selectedSkill}
        onOpenChange={(open) => { if (!open) setSelectedSkill(null); }}
      />
    </div>
  );
}
