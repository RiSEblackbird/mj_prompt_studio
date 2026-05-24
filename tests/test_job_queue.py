from threading import Event

from mj_prompt_studio.llm.job_queue import LLMJobQueue


def test_job_queue_runs_work_and_reports_success() -> None:
    done = Event()
    seen = {}
    queue = LLMJobQueue(max_workers=1)

    def callback(job):
        seen["status"] = job.status
        seen["output"] = job.output_json
        done.set()

    queue.submit(
        agent_name="VocabularyAgent",
        model="mock",
        reasoning_effort="low",
        input_snapshot={"text": "高級感"},
        work=lambda: {"ok": True},
        callback=callback,
    )

    assert done.wait(3)
    assert seen["status"] == "succeeded"
    assert seen["output"] == {"ok": True}
    queue.shutdown()
