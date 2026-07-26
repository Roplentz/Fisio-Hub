from __future__ import annotations

from collections.abc import Callable
from typing import Any

LOGICAL_STEP_KEY = "studio_step"
WIDGET_STEP_KEY = "_studio_step_selector"


def install_safe_step_selectbox(st_module: Any) -> Callable[..., Any]:
    """Wrap ``st.selectbox`` so step buttons may navigate safely.

    Streamlit forbids changing a widget-bound session-state key after the widget
    is instantiated. The Studio used ``studio_step`` both as the selectbox key
    and as the programmatic navigation state, which raised
    ``StreamlitAPIException`` on every Continue button.

    This adapter keeps ``studio_step`` as the logical route and binds the widget
    to a private key. User changes are copied back through ``on_change``; button
    changes are copied into the widget before it is rendered on the next rerun.
    """

    original_selectbox = st_module.selectbox

    def safe_selectbox(*args: Any, **kwargs: Any) -> Any:
        if kwargs.get("key") != LOGICAL_STEP_KEY:
            return original_selectbox(*args, **kwargs)

        logical_step = st_module.session_state.get(LOGICAL_STEP_KEY)
        if (
            logical_step is not None
            and st_module.session_state.get(WIDGET_STEP_KEY) != logical_step
        ):
            st_module.session_state[WIDGET_STEP_KEY] = logical_step

        user_on_change = kwargs.get("on_change")
        user_args = kwargs.get("args") or ()
        user_kwargs = kwargs.get("kwargs") or {}

        def sync_step() -> None:
            st_module.session_state[LOGICAL_STEP_KEY] = st_module.session_state[
                WIDGET_STEP_KEY
            ]
            if user_on_change:
                user_on_change(*user_args, **user_kwargs)

        kwargs["key"] = WIDGET_STEP_KEY
        kwargs["on_change"] = sync_step
        kwargs.pop("args", None)
        kwargs.pop("kwargs", None)
        selected = original_selectbox(*args, **kwargs)
        st_module.session_state[LOGICAL_STEP_KEY] = selected
        return selected

    st_module.selectbox = safe_selectbox
    return original_selectbox


__all__ = [
    "LOGICAL_STEP_KEY",
    "WIDGET_STEP_KEY",
    "install_safe_step_selectbox",
]
