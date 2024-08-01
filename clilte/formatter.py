from __future__ import annotations

from typing import ClassVar
from arclet.alconna import Option
from arclet.alconna.formatter import Trace
from arclet.alconna.tools import ShellTextFormatter as _ShellFormatter
from arclet.alconna.tools import RichConsoleFormatter as _RichFormatter


class ShellTextFormatter(_ShellFormatter):
    main_name: ClassVar[str]
    global_options: ClassVar[list[Option]] = []

    def format(self, trace: Trace) -> str:
        if trace.head["name"] == self.__class__.main_name:
            return super().format(trace)
        new_trace = Trace(
            trace.head,
            trace.args,
            trace.separators,
            [*self.__class__.global_options, *trace.body],
            trace.shortcuts
        )
        return super().format(new_trace)


class RichConsoleFormatter(_RichFormatter):
    main_name: ClassVar[str]
    global_options: ClassVar[list[Option]] = []

    def format(self, trace: Trace) -> str:
        if trace.head["name"] == self.__class__.main_name:
            return super().format(trace)
        new_trace = Trace(
            trace.head,
            trace.args,
            trace.separators,
            [*self.__class__.global_options, *trace.body],
            trace.shortcuts
        )
        return super().format(new_trace)
