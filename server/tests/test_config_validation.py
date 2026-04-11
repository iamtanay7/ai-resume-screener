"""Tests for config validation logic."""

from server.config import Settings


def test_config_weights_sum_to_one():
    """Test that valid ranking weights sum to 1.0."""
    # Valid weights that sum to exactly 1.0
    valid_weights = {
        "ranking_weight_skills": 0.4,
        "ranking_weight_experience": 0.3,
        "ranking_weight_education": 0.15,
        "ranking_weight_keywords": 0.15,
    }
    
    # Should accept valid config
    settings = Settings(**valid_weights)
    assert settings.ranking_weight_skills + settings.ranking_weight_experience + \
           settings.ranking_weight_education + settings.ranking_weight_keywords == 1.0


def test_config_weights_invalid_sum_raises_error():
    """Test that invalid weight sums raise ValueError."""
    # Test case where sum > 1.0
    invalid_weights_greater = {
        "ranking_weight_skills": 0.5,
        "ranking_weight_experience": 0.4,
        "ranking_weight_education": 0.2,
        "ranking_weight_keywords": 0.2,  # Sum = 1.3
    }
    
    # Should raise ValueError
    try:
        Settings(**invalid_weights_greater)
        assert False, "Expected ValueError for weights sum > 1.0"
    except ValueError:
        pass  # Expected
    
    # Test case where sum < 1.0
    invalid_weights_less = {
        "ranking_weight_skills": 0.3,
        "ranking_weight_experience": 0.2,
        "ranking_weight_education": 0.1,
        "ranking_weight_keywords": 0.1,  # Sum = 0.7
    }
    
    # Should raise ValueError
    try:
        Settings(**invalid_weights_less)
        assert False, "Expected ValueError for weights sum < 1.0"
    except ValueError:
        pass  # Expected