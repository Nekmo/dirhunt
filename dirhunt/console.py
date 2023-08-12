from __future__ import unicode_literals

from typing import Sequence, Tuple, Optional, TypeVar, Union, Coroutine, Any

from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.key_binding import KeyPressEvent
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.key_binding.key_bindings import KeyBindings, merge_key_bindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.styles import BaseStyle
from prompt_toolkit.widgets import RadioList, Label
from prompt_toolkit.layout.containers import HSplit


_T = TypeVar("_T")
E = KeyPressEvent


def status_code_colors(status_code):
    """Return a color for a status code."""
    if 100 <= status_code < 200:
        return "white"
    elif 200 == status_code:
        return "green1"
    elif 200 < status_code < 300:
        return "green3"
    elif 300 <= status_code < 400:
        return "deep_sky_blue1"
    elif 400 <= status_code < 404 or 404 < status_code < 500:
        return "deep_pink2"
    elif 404 == status_code:
        return "bright_red"
    elif 500 == status_code:
        return "magenta1"
    else:
        return "medium_orchid1"


def radiolist_prompt(
    title: str = "",
    values: Sequence[Tuple[_T, AnyFormattedText]] = None,
    default: Optional[_T] = None,
    cancel_value: Optional[_T] = None,
    style: Optional[BaseStyle] = None,
    async_: bool = False,
) -> Union[_T, Coroutine[Any, Any, _T]]:
    """Create a mini inline application for a radiolist prompt.

    :param title: The title to display above the radiolist.
    :param values: A sequence of tuples of the form (value, formatted_text).
    :param default: The default value to select.
    :param cancel_value: The value to return if the user presses Ctrl-C.
    :param style: A style to apply to the radiolist.
    :param async_: If True, run the prompt in async mode.
    :return: The value selected by the user.
    """
    # Create the radio list
    radio_list = RadioList(values, default)
    # Remove the enter key binding so that we can augment it
    radio_list.control.key_bindings.remove("up")
    radio_list.control.key_bindings.remove("down")
    radio_list.control.key_bindings.remove("enter")

    bindings = KeyBindings()

    @bindings.add("up")
    def up(_) -> None:
        radio_list._selected_index = max(0, radio_list._selected_index - 1)
        radio_list._handle_enter()

    @bindings.add("down")
    def down(_) -> None:
        radio_list._selected_index = min(
            len(radio_list.values) - 1, radio_list._selected_index + 1
        )
        radio_list._handle_enter()

    # Replace the enter key binding to select the value and also submit it
    @bindings.add("enter")
    def exit_with_value(event: E):
        """
        Pressing Enter will exit the user interface, returning the highlighted value.
        """
        radio_list._handle_enter()
        event.app.exit(result=radio_list.current_value)

    @bindings.add("c-c")
    def backup_exit_with_value(event: E):
        """
        Pressing Ctrl-C will exit the user interface with the cancel_value.
        """
        event.app.exit(result=cancel_value)

    merged_key_bindings = merge_key_bindings([load_key_bindings(), bindings])
    # Create and run the mini inline application
    application = Application(
        layout=Layout(HSplit([Label(title), radio_list])),
        key_bindings=merged_key_bindings,
        mouse_support=True,
        style=style,
        full_screen=False,
    )
    if async_:
        return application.run_async()
    else:
        return application.run()
