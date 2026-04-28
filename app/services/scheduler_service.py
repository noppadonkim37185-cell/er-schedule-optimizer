from core.engine import generate_er_schedule


def generate_schedule(year, month, special_holidays, off_requests, on_requests, preferences):
    """Thin wrapper around the protected scheduling engine."""
    return generate_er_schedule(
        int(year),
        int(month),
        list(special_holidays),
        list(off_requests),
        list(on_requests),
        preferences=dict(preferences),
    )
