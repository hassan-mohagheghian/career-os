"use client";

import { useEffect, useState } from "react";
import {
  Drawer,
  DrawerHeader,
  DrawerContent,
  DrawerFooter,
} from "@/shared/components/Drawer";
import { Input } from "@/shared/ui/input";
import { Textarea } from "@/shared/ui/textarea";
import { Button } from "@/shared/ui/button";
import { CircleNotch, Pencil, Warning } from "@phosphor-icons/react";
import type { CompanyDetail, CompanyEditInput } from "@/entities/company/types";
import { companyApi } from "@/entities/company/api";
import { useQueryClient } from "@tanstack/react-query";
import CompanyNotesTab from "./CompanyNotesTab";

const COMPANY_KEY = "companies-v2-infinite";
const COMPANY_DETAIL_KEY = "company-detail";

interface CompanyEditDrawerProps {
  companyId: string | null;
  onOpenChange: (id: string | null) => void;
}

function Field({
  label,
  required = false,
  children,
  hint,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
  hint?: string;
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
      {hint && <p className="text-2xs text-destructive">{hint}</p>}
    </div>
  );
}

export function CompanyEditDrawer({
  companyId,
  onOpenChange,
}: CompanyEditDrawerProps) {
  const queryClient = useQueryClient();
  const [detail, setDetail] = useState<CompanyDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [industry, setIndustry] = useState("");
  const [city, setCity] = useState("");
  const [country, setCountry] = useState("");
  const [website, setWebsite] = useState("");
  const [companySize, setCompanySize] = useState("");
  const [companyType, setCompanyType] = useState("");
  const [description, setDescription] = useState("");

  const open = !!companyId;

  useEffect(() => {
    if (!companyId) return;
    let active = true;
    setLoading(true);
    setError(null);
    companyApi
      .get(companyId)
      .then((d) => {
        if (!active) return;
        setDetail(d);
        setName(d.name ?? "");
        setIndustry(d.industry ?? "");
        setCity(d.city ?? "");
        setCountry(d.country ?? "");
        setWebsite(d.website ?? "");
        setCompanySize(d.company_size ?? "");
        setCompanyType(d.company_type ?? "");
        setDescription(d.description ?? "");
      })
      .catch(() => active && setError("Unable to load company details."))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [companyId]);

  const handleSave = async () => {
    if (!companyId) return;
    if (!name.trim()) {
      setError("Name is required");
      return;
    }
    setSubmitting(true);
    setError(null);
    const payload: CompanyEditInput = {
      name: name.trim(),
      industry: industry.trim() || null,
      city: city.trim() || null,
      country: country.trim() || null,
      website: website.trim() || null,
      company_size: companySize.trim() || null,
      company_type: companyType.trim() || null,
      description: description.trim() || null,
    };
    try {
      await companyApi.update(companyId, payload);
      queryClient.invalidateQueries({ queryKey: [COMPANY_KEY] });
      queryClient.invalidateQueries({
        queryKey: [COMPANY_DETAIL_KEY, companyId],
      });
      onOpenChange(null);
    } catch {
      setError("Failed to save changes. Please try again.");
    } finally {
      setSubmitting(false);
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
            <Pencil className="w-3.5 h-3.5" /> Edit Company
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

        {!loading && error && !detail && (
          <div className="flex items-start gap-1 text-xs text-destructive bg-destructive/10 rounded p-2 m-4">
            <Warning className="w-3.5 h-3.5 shrink-0" />
            {error}
          </div>
        )}

        {!loading && detail && (
          <div className="space-y-3">
            <Field label="Name" required>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Acme GmbH"
              />
            </Field>
            <Field label="Industry">
              <Input
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                placeholder="Software Development"
              />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="City">
                <Input
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  placeholder="Berlin"
                />
              </Field>
              <Field label="Country">
                <Input
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  placeholder="Germany"
                />
              </Field>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Company Size">
                <Input
                  value={companySize}
                  onChange={(e) => setCompanySize(e.target.value)}
                  placeholder="51-200"
                />
              </Field>
              <Field label="Company Type">
                <Input
                  value={companyType}
                  onChange={(e) => setCompanyType(e.target.value)}
                  placeholder="PRODUCT_COMPANY"
                />
              </Field>
            </div>
            <Field label="Website">
              <Input
                type="url"
                value={website}
                onChange={(e) => setWebsite(e.target.value)}
                placeholder="https://..."
              />
            </Field>
            <Field label="Description">
              <Textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Company description..."
                className="min-h-[80px] text-xs resize-none"
              />
            </Field>

            <div className="pt-1 border-t" />
            <CompanyNotesTab company={detail} />

            {error && detail && (
              <div className="flex items-start gap-1 text-xs text-destructive bg-destructive/10 rounded p-2">
                <Warning className="w-3.5 h-3.5 shrink-0" />
                {error}
              </div>
            )}
          </div>
        )}
      </DrawerContent>

      {!loading && detail && (
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
            {submitting ? "Saving..." : "Save"}
          </Button>
        </DrawerFooter>
      )}
    </Drawer>
  );
}
