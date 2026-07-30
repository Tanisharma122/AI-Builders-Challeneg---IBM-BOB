"use client";
/**
 * Custom hook that polls GET /api/video/status/{jobId} every 2 seconds until
 * the job reaches COMPLETE or FAILED.  Cleans up the interval on unmount.
 */

import { useCallback, useEffect, useState } from "react";
import { getJobStatus } from "@/lib/api";
import { ApiError, ProcessingJob } from "@/lib/types";

const TERMINAL_STATUSES = new Set(["COMPLETE", "FAILED"]);
const POLL_INTERVAL_MS = 2000;

interface UseJobPollingResult {
  job: ProcessingJob | null;
  isLoading: boolean;
  error: string | null;
}

export function useJobPolling(jobId: string | null): UseJobPollingResult {
  const [job, setJob] = useState<ProcessingJob | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(
    (id: string, onDone: () => void) => {
      getJobStatus(id)
        .then((updated) => {
          setJob(updated);
          setIsLoading(false);
          if (TERMINAL_STATUSES.has(updated.status)) onDone();
        })
        .catch((err) => {
          const msg =
            err instanceof ApiError
              ? `${err.status}: ${err.message}`
              : "Failed to fetch job status.";
          setError(msg);
          setIsLoading(false);
          onDone();
        });
    },
    []
  );

  useEffect(() => {
    if (!jobId) {
      const t = setTimeout(() => {
        setJob(null);
        setError(null);
        setIsLoading(false);
      }, 0);
      return () => clearTimeout(t);
    }

    const t = setTimeout(() => setIsLoading(true), 0);

    let stopped = false;

    const tick = () => {
      if (stopped) return;
      fetchStatus(jobId, () => {
        stopped = true;
        clearInterval(interval);
      });
    };

    // Fire first poll after the loading state is set (next tick)
    const t2 = setTimeout(tick, 0);
    const interval = setInterval(tick, POLL_INTERVAL_MS);

    return () => {
      clearTimeout(t);
      clearTimeout(t2);
      clearInterval(interval);
      stopped = true;
    };
  }, [jobId, fetchStatus]);

  return { job, isLoading, error };
}
