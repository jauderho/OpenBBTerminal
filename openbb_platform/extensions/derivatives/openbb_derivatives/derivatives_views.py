"""Views for the Derivatives Extension."""

from typing import Any, Dict, Tuple

from openbb_charting.charts.price_historical import price_historical
from openbb_charting.core.openbb_figure import OpenBBFigure


class DerivativesViews:
    """Derivatives Views."""

    @staticmethod
    def derivatives_futures_historical(  # noqa: PLR0912
        **kwargs,
    ) -> Tuple[OpenBBFigure, Dict[str, Any]]:
        """Get Derivatives Price Historical Chart."""
        return price_historical(**kwargs)
