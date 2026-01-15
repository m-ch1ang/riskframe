"""Plotly chart scaffolds."""

import pandas as pd
import plotly.express as px


def sample_exposure_chart():
    """Return a trivial bar chart to demonstrate wiring."""
    data = pd.DataFrame(
        {"bucket": ["Cash", "Equities", "Fixed Income"], "value": [10_000, 25_000, 15_000]}
    )
    fig = px.bar(data, x="bucket", y="value", title="Sample Exposure")
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    return fig

