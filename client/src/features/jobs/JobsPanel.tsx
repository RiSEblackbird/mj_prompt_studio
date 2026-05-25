import { RefreshCw, RotateCcw, X } from "lucide-react";

import type { LLMJob } from "../../shared/types/api";

interface JobsPanelProps {
  jobs: LLMJob[];
  onRefresh: () => void;
  onCancel: (jobId: string) => void;
  onRetry: (jobId: string) => void;
}

export function JobsPanel({ jobs, onRefresh, onCancel, onRetry }: JobsPanelProps) {
  return (
    <section className="jobs-panel" aria-label="Jobs">
      <div className="panel-title-row">
        <h2>Jobs</h2>
        <button type="button" className="icon-button" onClick={onRefresh} title="Refresh">
          <RefreshCw size={15} />
        </button>
      </div>
      <div className="job-list">
        {jobs.map((job) => (
          <article className={`job-row ${job.status}`} key={job.id}>
            <div>
              <strong>{job.agent_name}</strong>
              <span>{job.status}</span>
              {job.error_message && <small>{job.error_message}</small>}
            </div>
            <div className="job-actions">
              {(job.status === "queued" || job.status === "running") && (
                <button
                  type="button"
                  className="icon-button"
                  title="Cancel"
                  onClick={() => onCancel(job.id)}
                >
                  <X size={14} />
                </button>
              )}
              {job.status === "failed" && (
                <button
                  type="button"
                  className="icon-button"
                  title="Retry"
                  onClick={() => onRetry(job.id)}
                >
                  <RotateCcw size={14} />
                </button>
              )}
            </div>
          </article>
        ))}
        {jobs.length === 0 && <p>Job はありません。</p>}
      </div>
    </section>
  );
}
