"""Tests for ranking-oriented NLP normalization helpers."""

from server.services.nlp_normalization import build_structured_fields


def test_build_structured_fields_extracts_adverse_fit_job_requirements():
    text = """
    Principal Autonomous Surgical Robotics Safety Architect
    Location: Cambridge, MA
    PhD in Robotics, Electrical Engineering, or related field.
    12+ years of hands-on industry experience shipping complex robotic systems.
    Expert-level mastery of modern C++, embedded Linux, computer vision, ROS 2, CUDA, TensorRT, OpenCV, FPGA, and SLAM.
    IEC 60601, IEC 62304, ISO 13485, ISO 14971, and FDA design controls required.
    """

    fields = build_structured_fields(text, [], "job_description")

    assert fields["educationLevel"] == "phd"
    assert fields["requiredYearsExperience"] == 12.0
    assert fields["hardFilters"]["location"] == "Cambridge, MA"
    assert "C++" in fields["skills"]
    assert "Linux" in fields["skills"]
    assert "ROS 2" in fields["skills"]
    assert "FDA" in fields["keywords"]
    assert "IEC 60601" in fields["keywords"]


def test_build_structured_fields_extracts_resume_signals_without_fake_requirements():
    text = """
    Michael J. Ellis
    Bachelor of Science in Computer Science
    Technical Skills
    Python, C++, JavaScript, SQL
    Infrastructure
    Docker, Kubernetes, Git, Linux
    Security
    Active DoD Secret Clearance (TS/SCI eligible)
    """

    fields = build_structured_fields(text, [], "resume")

    assert fields["educationLevel"] == "bachelors"
    assert fields["requiredYearsExperience"] == 0.0
    assert "Python" in fields["skills"]
    assert "Linux" in fields["skills"]
    assert "DoD Clearance" in fields["keywords"]
    assert "TS/SCI" in fields["keywords"]


def test_build_structured_fields_infers_resume_experience_from_date_ranges():
    text = """
    Professional Experience
    U.S. Space Force - Space Systems Command
    May 2023 - Present
    Software Engineer

    Research Lab
    Jun 2021 - Apr 2023
    Student Developer
    """

    fields = build_structured_fields(text, [], "resume")

    assert fields["yearsExperience"] >= 4.0


def test_build_structured_fields_cleans_section_labels_from_skill_tokens():
    text = """
    TECHNICAL SKILLS
    Languages
    Python, C++, JavaScript, SQL
    Frameworks
    Django, REST APIs
    Infrastructure
    Docker, Kubernetes, Git, Linux
    """

    fields = build_structured_fields(text, [], "resume")

    assert "Languages" not in fields["skills"]
    assert "Frameworks" not in fields["skills"]
    assert "Infrastructure" not in fields["skills"]
    assert "Python" in fields["skills"]
    assert "Django" in fields["skills"]
    assert "Linux" in fields["skills"]


def test_build_structured_fields_avoids_duplicate_keywords_already_counted_as_skills():
    text = """
    Required Qualifications
    Expert-level mastery of CUDA, TensorRT, OpenCV, and ROS 2.
    FDA and IEC 60601 experience required.
    """

    fields = build_structured_fields(text, [], "job_description")

    assert "CUDA" in fields["skills"]
    assert "CUDA" not in fields["keywords"]
    assert "FDA" in fields["keywords"]
