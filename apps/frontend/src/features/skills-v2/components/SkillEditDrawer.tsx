"use client";

import { useEffect, useState } from "react";
import {
  Drawer,
  DrawerHeader,
  DrawerContent,
  DrawerFooter,
} from "@/shared/components/Drawer";
import { Input } from "@/shared/ui/input";
import { Button } from "@/shared/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from "@/shared/ui/select";
import { Badge } from "@/shared/ui/badge";
import {
  PencilSimple,
  Warning,
  Check,
  TagSimple,
  CircleNotch,
  Plus,
  X,
  GitMerge,
  Crown,
} from "@phosphor-icons/react";
import { skillApi } from "@/entities/skill/api";
import {
  useMergeSkills,
  usePromoteAliasToCanonical,
  useSkillCategories,
} from "@/entities/skill/hooks";
import { useQueryClient } from "@tanstack/react-query";
import { MergeSkillDialog } from "./MergeSkillDialog";
import { CategoryMultiSelect } from "./CategoryMultiSelect";

const SKILLS_KEY = "skills-v2-infinite";

interface SkillEditDrawerProps {
  skillId: number | null;
  onOpenChange: (id: number | null) => void;
}

function Field({
  label,
  required = false,
  hint,
  children,
}: {
  label: string;
  required?: boolean;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1">
      <label className="flex items-center gap-0.5 text-xs text-muted-foreground">
        <span>{label}</span>
        {required && <span className="text-destructive">*</span>}
        {!required && (
          <span className="text-muted-foreground/60">(optional)</span>
        )}
      </label>
      {children}
      {hint && <p className="text-2xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

export function SkillEditDrawer({
  skillId,
  onOpenChange,
}: SkillEditDrawerProps) {
  const queryClient = useQueryClient();
  const mergeMutation = useMergeSkills();
  const { categories, createMutation } = useSkillCategories();
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [level, setLevel] = useState(1);
  const [categoriesState, setCategoriesState] = useState<string[]>([]);
  const [roles, setRoles] = useState("");
  const [tagsInput, setTagsInput] = useState("");
  const [aliases, setAliases] = useState<string[]>([]);
  const [newAlias, setNewAlias] = useState("");
  const [aliasBusy, setAliasBusy] = useState(false);
  const [mergeOpen, setMergeOpen] = useState(false);
  const [mergePending, setMergePending] = useState(false);
  const [canonicalAlias, setCanonicalAlias] = useState<string | null>(null);
  const [canonicalPending, setCanonicalPending] = useState(false);
  const promoteMutation = usePromoteAliasToCanonical();

  const open = skillId != null;

  useEffect(() => {
    if (skillId == null) return;
    let active = true;
    setLoading(true);
    setError(null);
    skillApi
      .get(skillId)
      .then((d) => {
        if (!active) return;
        setName(d.name ?? "");
        setLevel(d.level ?? 1);
        setCategoriesState(d.categories ?? (d.category ? [d.category] : []));
        setRoles(d.roles ?? "");
        setTagsInput((d.tags ?? []).join(", "));
        setAliases(d.aliases ?? []);
      })
      .catch(() => active && setError("Unable to load skill details."))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [skillId]);

  const handleSave = async () => {
    if (skillId == null) return;
    if (!name.trim()) {
      setError("Name is required");
      return;
    }
    setSubmitting(true);
    setError(null);
    const payload = {
      name: name.trim(),
      level,
      categories: categoriesState,
      roles: roles.trim(),
      tags: tagsInput
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
    };
    try {
      await skillApi.update(skillId, payload);
      queryClient.invalidateQueries({ queryKey: [SKILLS_KEY] });
      onOpenChange(null);
    } catch {
      setError("Failed to save changes. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddAlias = async () => {
    if (skillId == null) return;
    const alias = newAlias.trim();
    if (!alias || aliases.includes(alias)) return;
    setAliasBusy(true);
    setError(null);
    try {
      const updated = await skillApi.addAlias(skillId, alias);
      setAliases(updated.aliases ?? [...aliases, alias]);
      setNewAlias("");
      queryClient.invalidateQueries({ queryKey: [SKILLS_KEY] });
    } catch {
      setError("Failed to add alias.");
    } finally {
      setAliasBusy(false);
    }
  };

  const handleRemoveAlias = async (alias: string) => {
    if (skillId == null) return;
    setAliasBusy(true);
    setError(null);
    try {
      const updated = await skillApi.removeAlias(skillId, alias);
      setAliases(updated.aliases ?? aliases.filter((a) => a !== alias));
      queryClient.invalidateQueries({ queryKey: [SKILLS_KEY] });
    } catch {
      setError("Failed to remove alias.");
    } finally {
      setAliasBusy(false);
    }
  };

  const handleAddCategory = async (name: string) => {
    await createMutation.mutateAsync(name);
    return { name };
  };

  const handlePromoteAlias = async () => {
    if (skillId == null || canonicalAlias == null) return;
    setCanonicalPending(true);
    setError(null);
    try {
      const updated = await promoteMutation.mutateAsync({
        id: skillId,
        aliasName: canonicalAlias,
      });
      setName(updated.name ?? canonicalAlias);
      setAliases(updated.aliases ?? []);
      setCanonicalAlias(null);
      queryClient.invalidateQueries({ queryKey: [SKILLS_KEY] });
    } catch {
      setError(
        "Failed to promote alias. Make sure it does not clash with another skill.",
      );
    } finally {
      setCanonicalPending(false);
    }
  };

  const handleMerge = async (targetId: number) => {
    if (skillId == null) return;
    setMergePending(true);
    setError(null);
    try {
      await mergeMutation.mutateAsync({ targetId, sourceIds: [skillId] });
      onOpenChange(null);
    } catch {
      setError("Failed to merge skill.");
    } finally {
      setMergePending(false);
    }
  };

  return (
    <Drawer
      open={open}
      onOpenChange={(o) => {
        if (!o) onOpenChange(null);
      }}
    >
      <DrawerHeader
        title={
          <span className="flex items-center gap-1.5">
            <PencilSimple className="w-3.5 h-3.5" /> Edit Skill
          </span>
        }
        onClose={() => onOpenChange(null)}
      />
      <DrawerContent>
        {loading && (
          <div className="flex items-center justify-center h-40">
            <CircleNotch className="w-6 h-6 text-muted-foreground animate-spin" />
          </div>
        )}

        {!loading && error && (
          <div className="flex items-start gap-1 text-xs text-destructive bg-destructive/10 rounded p-2">
            <Warning className="w-3.5 h-3.5 shrink-0" />
            {error}
          </div>
        )}

        {!loading && skillId != null && (
          <div className="space-y-3">
            <Field label="Name" required>
              <Input value={name} onChange={(e) => setName(e.target.value)} />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Level">
                <Select
                  value={String(level)}
                  onValueChange={(v) => setLevel(Number(v))}
                >
                  <SelectTrigger className="h-8 text-xs">{level}</SelectTrigger>
                  <SelectContent position="popper">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                      <SelectItem key={n} value={String(n)}>
                        {n}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Categories">
                <CategoryMultiSelect
                  value={categoriesState}
                  onChange={setCategoriesState}
                  options={categories.map((c) => c.category)}
                  onCreate={handleAddCategory}
                  size="md"
                />
              </Field>
            </div>
            <Field label="Relevant Roles">
              <Input value={roles} onChange={(e) => setRoles(e.target.value)} />
            </Field>
            <Field label="Tags" hint="Comma-separated">
              <div className="flex items-center gap-1">
                <TagSimple className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                <Input
                  value={tagsInput}
                  onChange={(e) => setTagsInput(e.target.value)}
                  placeholder="ai, ml, backend"
                />
              </div>
            </Field>

            <Field
              label="Aliases"
              hint="Other names for this skill (e.g. 'ReactJS' for 'React')"
            >
              <div className="space-y-2">
                {aliases.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {aliases.map((a) => (
                      <Badge
                        key={a}
                        variant="outline"
                        className="gap-1 pr-1 text-2xs"
                      >
                        {a}
                        <button
                          type="button"
                          onClick={() => handleRemoveAlias(a)}
                          className="rounded-full p-0.5 hover:bg-destructive/10 text-muted-foreground hover:text-destructive"
                          aria-label={`Remove alias ${a}`}
                          disabled={aliasBusy}
                        >
                          <X className="w-2.5 h-2.5" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-2xs text-muted-foreground">
                    No aliases yet.
                  </p>
                )}
                <div className="flex items-center gap-1">
                  <Input
                    value={newAlias}
                    onChange={(e) => setNewAlias(e.target.value)}
                    placeholder="Add alias..."
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        handleAddAlias();
                      }
                    }}
                  />
                  <Button
                    type="button"
                    size="icon"
                    variant="outline"
                    className="h-7 w-7 shrink-0"
                    onClick={handleAddAlias}
                    disabled={aliasBusy || !newAlias.trim()}
                    aria-label="Add alias"
                  >
                    {aliasBusy ? (
                      <CircleNotch className="w-3 h-3 animate-spin" />
                    ) : (
                      <Plus className="w-3 h-3" />
                    )}
                  </Button>
                </div>
                {aliases.length > 0 && (
                  <div className="pt-1 border-t border-border/40">
                    <label className="text-2xs text-muted-foreground mb-1 block">
                      Make an alias the canonical name
                    </label>
                    <div className="flex items-center gap-1">
                      <select
                        value={canonicalAlias ?? ""}
                        onChange={(e) =>
                          setCanonicalAlias(e.target.value || null)
                        }
                        className="h-7 flex-1 rounded-md border border-input bg-transparent px-2 text-xs"
                        aria-label="Alias to promote to canonical"
                      >
                        <option value="">Choose alias...</option>
                        {aliases.map((a) => (
                          <option key={a} value={a}>
                            {a}
                          </option>
                        ))}
                      </select>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        className="h-7 gap-1 text-2xs shrink-0"
                        onClick={handlePromoteAlias}
                        disabled={canonicalAlias == null || canonicalPending}
                      >
                        {canonicalPending ? (
                          <CircleNotch className="w-3 h-3 animate-spin" />
                        ) : (
                          <Crown className="w-3 h-3" />
                        )}
                        Make canonical
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </Field>

            <div className="pt-1">
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-2xs gap-1"
                onClick={() => setMergeOpen(true)}
              >
                <GitMerge className="w-3 h-3" /> Merge into another skill
              </Button>
            </div>

            {error && (
              <div className="flex items-start gap-1 text-xs text-destructive bg-destructive/10 rounded p-2">
                <Warning className="w-3.5 h-3.5 shrink-0" />
                {error}
              </div>
            )}
          </div>
        )}
      </DrawerContent>

      {!loading && skillId != null && (
        <DrawerFooter>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onOpenChange(null)}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={handleSave}
            disabled={submitting}
          >
            {submitting ? (
              <CircleNotch className="w-3 h-3 animate-spin" />
            ) : (
              <Check className="w-3 h-3" />
            )}
            {submitting ? "Saving..." : "Save"}
          </Button>
        </DrawerFooter>
      )}
      <MergeSkillDialog
        sources={skillId != null ? [{ id: skillId, name }] : []}
        open={mergeOpen}
        onOpenChange={setMergeOpen}
        onMerge={handleMerge}
        pending={mergePending}
      />
    </Drawer>
  );
}
