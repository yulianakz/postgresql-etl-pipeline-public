import logging

log = logging.getLogger(__name__)


def notify_failure(context):
    task = context.get("task_instance")
    dag = context.get("dag")
    exception = context.get("exception")

    error_message = str(exception) if exception else "No exception info"

    log.error(
        "DAG %s | Task failed: %s | %s",
        dag.dag_id if dag else "unknown",
        task.task_id if task else "unknown",
        error_message,
    )