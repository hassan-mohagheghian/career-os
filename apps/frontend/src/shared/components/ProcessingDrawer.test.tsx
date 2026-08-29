import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { WorkflowPanel } from "@/shared/components/ProcessingDrawer";
import type { QueueEntry, WorkflowProgress } from "@/entities/processing/types";

function makeEntry(overrides: Partial<QueueEntry> = {}): QueueEntry {
  return {
    execution_id: "exec-1",
    job_id: "job-1",
    target_type: "job",
    target_id: "job-1",
    title: "Job 1",
    url: null,
    links: [],
    status: "running",
    current_step: null,
    progress: 0,
    error: null,
    failed_step: null,
    started_at: new Date(Date.now() - 11 * 60 * 1000).toISOString(),
    finished_at: null,
    ...overrides,
  };
}

function makeWorkflow(overrides: Partial<WorkflowProgress> = {}): WorkflowProgress {
  return {
    id: "wf-1",
    name: "Workflow",
    status: "running",
    current_step: null,
    progress: 0,
    steps: [],
    ...overrides,
  };
}

describe("WorkflowPanel", () => {
  it("renders the workflow name", () => {
    render(
      <WorkflowPanel
        workflow={makeWorkflow({ name: "Job Analysis" })}
        entry={makeEntry()}
      />,
    );
    expect(screen.getByText("Job Analysis")).toBeTruthy();
  });

  it("renders the error message for a failed entry", () => {
    render(
      <WorkflowPanel
        workflow={makeWorkflow({ status: "failed" })}
        entry={makeEntry({ status: "failed", error: "Execution timed out after 612s. Check status or retry." })}
      />,
    );
    expect(screen.getByText(/Execution timed out after 612s/i)).toBeTruthy();
  });

  it("renders without workflow progress", () => {
    render(<WorkflowPanel workflow={null} entry={makeEntry()} />);
    expect(screen.getByText(/No steps recorded yet/i)).toBeTruthy();
  });
});
