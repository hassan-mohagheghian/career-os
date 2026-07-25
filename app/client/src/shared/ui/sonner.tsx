import { useTheme } from "next-themes"
import { Toaster as Sonner } from "sonner"

const Toaster = ({ ...props }) => {
  const { theme = "system" } = useTheme()

  return (
    <>
      <style>{`
        [data-sonner-toaster] {
          --normal-bg: var(--card);
          --normal-border: var(--border);
          --normal-text: var(--card-foreground);
          --success-bg: var(--card);
          --success-border: oklch(0.473 0.137 46.201);
          --success-text: var(--card-foreground);
          --error-bg: var(--card);
          --error-border: var(--destructive);
          --error-text: var(--destructive);
          --info-bg: var(--card);
          --info-border: oklch(0.547 0.021 43.1);
          --info-text: var(--card-foreground);
          --warning-bg: var(--card);
          --warning-border: oklch(0.868 0.007 39.5);
          --warning-text: var(--card-foreground);
        }
        .dark [data-sonner-toaster] {
          --normal-bg: var(--card);
          --normal-border: var(--border);
          --normal-text: var(--card-foreground);
          --success-bg: var(--card);
          --success-border: oklch(0.473 0.137 46.201);
          --success-text: var(--card-foreground);
          --error-bg: var(--card);
          --error-border: var(--destructive);
          --error-text: var(--destructive);
          --info-bg: var(--card);
          --info-border: oklch(0.547 0.021 43.1);
          --info-text: var(--card-foreground);
          --warning-bg: var(--card);
          --warning-border: oklch(0.868 0.007 39.5);
          --warning-text: var(--card-foreground);
        }
      `}</style>
      <Sonner
        theme={theme}
        className="toaster group"
        position="bottom-left"
        toastOptions={{
          classNames: {
            toast:
              "group toast group-[.toaster]:bg-card group-[.toaster]:text-card-foreground group-[.toaster]:border-border group-[.toaster]:shadow-lg",
            description: "group-[.toast]:text-muted-foreground",
            actionButton:
              "group-[.toast]:bg-primary group-[.toast]:text-primary-foreground",
            cancelButton:
              "group-[.toast]:bg-muted group-[.toast]:text-muted-foreground",
          },
        }}
        {...props}
      />
    </>
  )
}

export { Toaster }
