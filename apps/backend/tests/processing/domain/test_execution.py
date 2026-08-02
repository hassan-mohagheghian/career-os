from processing.domain.enums import ExecutionType, ExecutionStatus
from processing.domain.entities.processing_execution import ProcessingExecution


def test_execution_type_enum_values():
    assert ExecutionType.JOB_PROCESSING.value == "job_processing"
    assert ExecutionType.COMPANY_PROCESSING.value == "company_processing"


def test_execution_status_enum_values():
    assert ExecutionStatus.CREATED.value == "created"
    assert ExecutionStatus.QUEUED.value == "queued"
    assert ExecutionStatus.STARTING.value == "starting"
    assert ExecutionStatus.RUNNING.value == "running"
    assert ExecutionStatus.COMPLETED.value == "completed"
    assert ExecutionStatus.FAILED.value == "failed"
    assert ExecutionStatus.CANCELLED.value == "cancelled"


def test_processing_execution_creation():
    execution = ProcessingExecution(
        execution_type=ExecutionType.JOB_PROCESSING,
        target_type="job",
        target_id="123",
    )
    assert execution.execution_type == ExecutionType.JOB_PROCESSING
    assert execution.target_type == "job"
    assert execution.target_id == "123"
    assert execution.status == ExecutionStatus.CREATED
    assert execution.retry_count == 0
    assert execution.error_message is None
    assert execution.id is not None


def test_processing_execution_to_dict():
    execution = ProcessingExecution(
        execution_type=ExecutionType.JOB_PROCESSING,
        target_type="job",
        target_id="123",
    )
    d = execution.to_dict()
    assert d["execution_type"] == "job_processing"
    assert d["target_type"] == "job"
    assert d["target_id"] == "123"
    assert d["status"] == "created"
    assert d["retry_count"] == 0


def test_processing_execution_from_dict():
    data = {
        "id": "test-id-1",
        "execution_type": "job_processing",
        "status": "queued",
        "target_type": "job",
        "target_id": "456",
        "created_at": None,
        "started_at": None,
        "finished_at": None,
        "retry_count": 0,
        "error_message": None,
    }
    execution = ProcessingExecution.from_dict(data)
    assert execution.id == "test-id-1"
    assert execution.execution_type == ExecutionType.JOB_PROCESSING
    assert execution.status == ExecutionStatus.QUEUED
    assert execution.target_type == "job"
    assert execution.target_id == "456"


def test_processing_execution_status_update():
    execution = ProcessingExecution(
        execution_type=ExecutionType.JOB_PROCESSING,
        target_type="job",
        target_id="123",
    )
    execution.status = ExecutionStatus.QUEUED
    assert execution.status == ExecutionStatus.QUEUED
