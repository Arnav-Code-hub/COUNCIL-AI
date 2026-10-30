import pytest
from pydantic import ValidationError

from council.schemas import EvidenceFile, Project, evidence_inventory


def project(**updates):
    return Project.model_validate(
        dict(
            title="Pump study",
            research_question="Does it help?",
            findings="Reported fewer outages.",
            methods="Interviewed five users.",
            results="No baseline supplied.",
            limitations="Small sample.",
            **updates,
        )
    )


def test_stable_evidence_and_lines():
    p = project(files=[dict(name="study.py", content="x = 1\nprint(x)")])
    refs = evidence_inventory(p)
    assert refs == evidence_inventory(p)
    assert refs[-1].lines == ["x = 1", "print(x)"]
    assert len({r.id for r in refs}) == len(refs)


@pytest.mark.parametrize(
    "name", ["../a.py", "C:a.py", "a.exe", ".env", "x/y.txt", "a" * 130 + ".txt"]
)
def test_reject_unsafe_names(name):
    with pytest.raises(ValidationError):
        EvidenceFile(name=name, content="hello")


@pytest.mark.parametrize(
    "content",
    ["", "hello\x00", "\ud800", "x" * 50001],
    ids=["empty", "nul", "surrogate", "oversize"],
)
def test_reject_bad_file_content(content):
    with pytest.raises(ValidationError):
        EvidenceFile(name="a.txt", content=content)


def test_reject_total_evidence():
    with pytest.raises(ValidationError):
        project(files=[dict(name=f"a{i}.txt", content="x" * 40000) for i in range(6)])


def test_reject_duplicate_filenames():
    with pytest.raises(ValidationError):
        project(files=[dict(name="a.py", content="x"), dict(name="A.py", content="y")])
