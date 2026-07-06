import pandas as pd

from barrett.data.cohort_filters import exclude_current_event_rows


def test_exclude_current_event_rows():
    df = pd.DataFrame({"sample": ["a", "b", "c"], "DaysFromCurrentToEvent": [0, 10, None]})
    out = exclude_current_event_rows(df)
    assert out["sample"].tolist() == ["b", "c"]

