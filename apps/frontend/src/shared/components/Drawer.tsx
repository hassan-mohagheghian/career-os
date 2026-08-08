import * as React from "react";
import { X } from "@phosphor-icons/react";
import { cn } from "@/shared/lib/utils";
import {
  Drawer as DrawerPrimitive,
  DrawerContent as DrawerContentPrimitive,
  DrawerClose,
  DrawerTitle,
  DrawerDescription,
} from "@/shared/ui/drawer";

const DRAWER_VARIANTS = {
  xs: "max-w-[320px]",
  sm: "max-w-[420px]",
  md: "max-w-[560px]",
  lg: "max-w-[720px]",
  xl: "max-w-[960px]",
  full: "max-w-full",
} as const;

type DrawerVariant = keyof typeof DRAWER_VARIANTS;
type DrawerPlacement = "right" | "left" | "bottom";

interface DrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  variant?: DrawerVariant;
  placement?: DrawerPlacement;
  contentClassName?: string;
  children: React.ReactNode;
}

function Drawer({
  open,
  onOpenChange,
  variant = "lg",
  placement = "right",
  contentClassName,
  children,
}: DrawerProps) {
  return (
    <DrawerPrimitive
      open={open}
      onOpenChange={onOpenChange}
      direction={placement}
    >
      <DrawerContentPrimitive
        className={cn(
          "p-0 flex flex-col",
          DRAWER_VARIANTS[variant],
          placement === "bottom" && "max-h-[80vh]",
          placement === "right" &&
            "!fixed !inset-y-0 !right-0 !left-auto h-full rounded-l-[10px] w-screen !mt-0",
          placement === "left" &&
            "!fixed !inset-y-0 !left-0 !right-auto h-full rounded-r-[10px] w-screen !mt-0",
          contentClassName,
        )}
      >
        {children}
      </DrawerContentPrimitive>
    </DrawerPrimitive>
  );
}

interface DrawerHeaderProps {
  title: React.ReactNode;
  description?: string;
  onClose?: () => void;
  actions?: React.ReactNode;
  className?: string;
}

function DrawerHeader({
  title,
  description,
  onClose,
  actions,
  className,
}: DrawerHeaderProps) {
  return (
    <div
      className={cn(
        "flex items-start justify-between gap-4 px-6 py-4 border-b shrink-0",
        className,
      )}
    >
      <div className="flex flex-col gap-1 min-w-0">
        <DrawerTitle className="text-base font-bold truncate">
          {title}
        </DrawerTitle>
        {description && (
          <DrawerDescription className="text-sm text-muted-foreground">
            {description}
          </DrawerDescription>
        )}
      </div>
      {(actions || onClose) && (
        <div className="flex items-center gap-1 shrink-0">
          {actions}
          {onClose && (
            <DrawerClose asChild onClick={onClose}>
              <button className="shrink-0 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
                <X className="h-4 w-4" />
                <span className="sr-only">Close</span>
              </button>
            </DrawerClose>
          )}
        </div>
      )}
    </div>
  );
}

function DrawerContent({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex-1 overflow-y-auto px-6 py-4", className)}>
      {children}
    </div>
  );
}

function DrawerFooter({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex items-center justify-end gap-2 px-6 py-4 border-t shrink-0",
        className,
      )}
    >
      {children}
    </div>
  );
}

export { Drawer, DrawerHeader, DrawerContent, DrawerFooter, DRAWER_VARIANTS };
export type { DrawerProps, DrawerVariant, DrawerPlacement };
