"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  CaretDown,
  CircleNotch,
  LinkBreak,
  MagnifyingGlass,
} from "@phosphor-icons/react";
import { Popover, PopoverContent, PopoverTrigger } from "@/shared/ui/popover";
import { Button } from "@/shared/ui/button";
import { DebouncedInput } from "@/shared/ui/debounced-input";
import { companyApi } from "@/entities/company/api";

interface CompanyPickerProps {
  companyId: string | null;
  companyName: string | null;
  onSelect: (companyId: string | null) => void;
  pending?: boolean;
}

export function CompanyPicker({
  companyId,
  companyName,
  onSelect,
  pending,
}: CompanyPickerProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["companies-job-picker", query],
    queryFn: () =>
      companyApi.listInfinite({
        query: query || undefined,
        page_size: 20,
        sort: "name",
        order: "asc",
      }),
    enabled: open,
  });

  const candidates = data?.items ?? [];

  const pick = (id: string | null) => {
    onSelect(id);
    setOpen(false);
    setQuery("");
  };

  return (
    <div className="flex items-center justify-end gap-1 min-w-0">
      {companyId && companyName ? (
        <a
          href={`/companies?company=${encodeURIComponent(companyId)}`}
          title="Open company details"
          className="text-xs text-primary hover:underline truncate min-w-0"
        >
          {companyName}
        </a>
      ) : null}
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="h-4 gap-1 px-0 text-xs text-primary hover:bg-muted/50 shrink-0"
            aria-label="Change company"
          >
            {companyId ? (
              <CaretDown className="w-3 h-3 opacity-60" />
            ) : (
              <>
                <span>Set company</span>
                <CaretDown className="w-3 h-3 opacity-60" />
              </>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent align="end" className="w-64 p-0">
          <div className="p-2">
            <DebouncedInput
              value={query}
              onValueChange={setQuery}
              placeholder="Search companies..."
              icon={
                <MagnifyingGlass className="w-3.5 h-3.5 text-muted-foreground" />
              }
              clearable
              clearLabel="Clear search"
              wrapperClassName="w-full"
              inputClassName="pl-8 h-7 text-xs"
              aria-label="Search companies to link"
            />
          </div>
          <div className="max-h-56 overflow-y-auto border-t border-border/40">
            {isLoading && (
              <div className="flex items-center justify-center py-6">
                <CircleNotch className="w-5 h-5 text-muted-foreground animate-spin" />
              </div>
            )}
            {!isLoading && candidates.length === 0 && (
              <p className="py-6 text-center text-xs text-muted-foreground">
                No companies found.
              </p>
            )}
            {!isLoading &&
              candidates.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => pick(c.id)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-left text-xs hover:bg-muted/40 transition-colors"
                >
                  {c.logo_url && (
                    <img
                      src={c.logo_url}
                      alt=""
                      className="w-4 h-4 rounded shrink-0"
                    />
                  )}
                  <span className="font-medium truncate">{c.name}</span>
                </button>
              ))}
            {companyId && (
              <button
                type="button"
                onClick={() => pick(null)}
                disabled={pending}
                className="w-full flex items-center gap-2 px-3 py-2 text-left text-xs text-destructive hover:bg-muted/40 transition-colors border-t border-border/40"
              >
                <LinkBreak className="w-3.5 h-3.5 shrink-0" /> Unlink company
              </button>
            )}
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}
