"use client";

import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { ProcessingJob, JobStatus } from "@/lib/types";

interface Step {
  label: string;
  status: JobStatus;
  pct: number;
}

const STEPS: Step[] = [
  { label: "Transcribing", status: "TRANSCRIBING", pct: 25 },
  { label: "Analyzing",    status: "ANALYZING",    pct: 50 },
  { label: "Processing",   status: "PROCESSING",   pct: 75 },
  { label: "Complete",     status: "COMPLETE",     pct: 100 },
];

const STATUS_ORDER: Record<JobStatus, number> = {
  PENDING:      0,
  TRANSCRIBING: 1,
  ANALYZING:    2,
  PROCESSING:   3,
  COMPLETE:     4,
  FAILED:       5,
};

interface Props {
  job: ProcessingJob;
}

export function ProcessingProgress({ job }: Props) {
  const currentOrder = STATUS_ORDER[job.status] ?? 0;
  const isFailed = job.status === "FAILED";

  return (
    <div className="w-full max-w-xl mx-auto space-y-5 p-4">
      {/* Progress bar */}
      <Progress value={job.progress_pct} className="h-2 bg-secondary" />

      {/* Step indicators */}
      <div className="flex justify-between">
        {STEPS.map((step, i) => {
          const stepOrder = STATUS_ORDER[step.status];
          const isDone    = currentOrder > stepOrder;
          const isActive  = currentOrder === stepOrder && !isFailed;
          const isPending = currentOrder < stepOrder;

          return (
            <div key={step.status} className="flex flex-col items-center gap-1 flex-1">
              <div className="flex items-center w-full">
                <div className={`h-0.5 flex-1 ${i === 0 ? "invisible" : isDone || isActive ? "bg-brand" : "bg-border"}`} />
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-all ${
                    isFailed && isActive
                      ? "border-destructive bg-destructive/20 text-destructive"
                      : isDone
                      ? "border-brand bg-brand text-brand-foreground"
                      : isActive
                      ? "border-brand bg-background text-brand animate-pulse"
                      : "border-border bg-secondary text-muted-foreground"
                  }`}
                >
                  {isDone ? "✓" : i + 1}
                </div>
                <div className={`h-0.5 flex-1 ${i === STEPS.length - 1 ? "invisible" : isDone ? "bg-brand" : "bg-border"}`} />
              </div>
              <span className={`text-xs font-medium ${
                isActive  ? "text-brand" :
                isPending ? "text-muted-foreground" :
                isDone    ? "text-foreground" :
                            "text-muted-foreground"
              }`}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Status badge */}
      <div className="flex justify-center">
        <Badge
          variant={isFailed ? "destructive" : "secondary"}
          className={isFailed ? "" : "bg-secondary text-foreground border-border"}
        >
          {isFailed
            ? `Failed: ${job.error_msg ?? "Unknown error"}`
            : `${job.progress_pct}% — ${job.status}`}
        </Badge>
      </div>
    </div>
  );
}
