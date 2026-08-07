"""Candidate domain event tests."""

from candidates.domain.event_publisher import InMemoryEventCollector
from candidates.domain.events import (
    CandidateProfileCreated,
    CandidateProfileUpdated,
    CandidateSourceAdded,
    CandidateSourceUpdated,
    CandidateMergeCompleted,
    CandidateSourceSkipped,
    CandidateVersionCreated,
    CandidateSkillInferred,
)


def test_profile_created_event():
    event = CandidateProfileCreated(aggregate_id="p1", profile_id="p1")
    assert event.event_type == "candidate.profile.created"
    assert event.aggregate_id == "p1"
    assert event.profile_id == "p1"


def test_profile_updated_event():
    event = CandidateProfileUpdated(aggregate_id="p1", profile_id="p1")
    assert event.event_type == "candidate.profile.updated"


def test_source_added_event():
    event = CandidateSourceAdded(aggregate_id="p1", profile_id="p1", source_type="resume", version=2)
    assert event.event_type == "candidate.source.added"
    assert event.source_type == "resume"
    assert event.version == 2


def test_source_updated_event():
    event = CandidateSourceUpdated(aggregate_id="p1", profile_id="p1", source_type="linkedin", status="processed")
    assert event.event_type == "candidate.source.updated"
    assert event.status == "processed"


def test_merge_completed_event():
    event = CandidateMergeCompleted(aggregate_id="p1", profile_id="p1", source_type="resume", version=4)
    assert event.event_type == "candidate.merge.completed"
    assert event.version == 4


def test_version_created_event():
    event = CandidateVersionCreated(aggregate_id="p1", profile_id="p1", version=5)
    assert event.event_type == "candidate.version.created"
    assert event.version == 5


def test_skill_inferred_event():
    event = CandidateSkillInferred(aggregate_id="p1", profile_id="p1", skill_id=7, skill_name="Microservices", confidence=0.8)
    assert event.event_type == "candidate.skill.inferred"
    assert event.skill_name == "Microservices"


def test_source_skipped_event():
    event = CandidateSourceSkipped(aggregate_id="p1", profile_id="p1", source_type="resume", version=2, reason="already_processed")
    assert event.event_type == "candidate.source.skipped"
    assert event.reason == "already_processed"


class TestInMemoryEventCollector:
    def test_collects_and_drains_events(self):
        collector = InMemoryEventCollector()
        collector.publish(CandidateProfileCreated(profile_id="p1"))
        collector.publish(CandidateVersionCreated(profile_id="p1", version=1))

        assert len(collector.events) == 2
        drained = collector.take_events()
        assert len(drained) == 2
        assert collector.events == []

    def test_as_dicts_flat_contract(self):
        collector = InMemoryEventCollector()
        collector.publish(CandidateSourceAdded(profile_id="p1", source_type="resume", version=1))
        data = collector.as_dicts()
        assert data[0]["event_type"] == "candidate.source.added"
        assert data[0]["source_type"] == "resume"
        assert data[0]["version"] == 1
