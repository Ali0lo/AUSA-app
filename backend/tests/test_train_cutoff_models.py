import pandas as pd

from scripts.train_cutoff_models import temporal_split_years


def test_three_intakes_use_the_two_observed_steps_for_a_one_step_forecast():
    frame = pd.DataFrame({"intake_year": [2023, 2024, 2025]})

    assert temporal_split_years(frame) == (2024, 2024, 2025)