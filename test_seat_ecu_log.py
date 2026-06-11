import pytest
import pandas as pd


# 📌 Fixture: Load log once for all tests
@pytest.fixture(scope="module")
def log_data():
    df = pd.read_csv("seat_ecu_log_10min_updated.csv")
    # df = pd.read_csv("seat_ecu_log_10min.csv")
    return df


# ✅ 1. No ERROR status should exist
def test_no_error_status(log_data):
    errors = log_data[log_data["status"] == "ERROR"]
    assert errors.empty, f"\nERROR entries found:\n{errors}"


# ✅ 2. Value range validation (0–100 for %, 0–60 for angle)
def test_value_range(log_data):
    invalid_percent = log_data[
        (log_data["unit"] == "%") &
        ((log_data["value"] < 0) | (log_data["value"] > 100))
    ]

    invalid_angle = log_data[
        (log_data["unit"] == "deg") &
        ((log_data["value"] < 0) | (log_data["value"] > 60))
    ]

    assert invalid_percent.empty, f"\nInvalid % values:\n{invalid_percent}"
    assert invalid_angle.empty, f"\nInvalid angle values:\n{invalid_angle}"


# ✅ 3. No missing/null values
def test_no_missing_values(log_data):
    assert log_data.isnull().sum().sum() == 0


# ✅ 4. Timestamp format + monotonic check
def test_timestamp_order(log_data):
    timestamps = log_data["timestamp"]

    # Convert to comparable format
    timestamps_parsed = pd.to_datetime(timestamps, format="%H:%M:%S")

    assert timestamps_parsed.is_monotonic_increasing, \
        "Timestamps are not in increasing order"


# ✅ 5. Validate allowed signals
def test_valid_signals(log_data):
    valid_signals = {"seat_length", "seat_height", "backrest_angle"}
    invalid = log_data[~log_data["signal"].isin(valid_signals)]

    assert invalid.empty, f"\nInvalid signals found:\n{invalid}"


# ✅ 6. Check recovery after ERROR
def test_error_recovery(log_data):
    error_rows = log_data[log_data["status"] == "ERROR"]

    for idx in error_rows.index:
        if idx + 1 < len(log_data):
            next_row = log_data.iloc[idx + 1]
            assert next_row["status"] == "OK", \
                f"No recovery after ERROR at index {idx}"


# ✅ 7. Logical consistency (seat_length should not jump drastically)
def test_smooth_transition(log_data):
    seat_length = log_data[log_data["signal"] == "seat_length"]["value"]

    diffs = seat_length.diff().abs()

    # Allow max jump of 20%
    violations = diffs[diffs > 20]

    assert violations.empty, f"\nAbrupt seat movement detected:\n{violations}"


# ✅ 8. Final state stability check
def test_final_state_stable(log_data):
    last_entries = log_data.tail(3)

    assert all(last_entries["status"] == "OK"), \
        "Final state is not stable"
    
# End of test_seat_ecu_log.py