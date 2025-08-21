from __future__ import annotations

from clilte import BasePlugin, PluginMetadata
from arclet.alconna import Alconna, Arparma, Args, CommandMeta, Option


class MyPlugin1(BasePlugin):

    def init(self) -> Alconna:
        return Alconna(
            self.local,
            Args["name", str],
            meta=CommandMeta("test command")
        )

    def meta(self) -> PluginMetadata:
        return PluginMetadata("hello", "0.0.1", "my first plugin", ["dev"], ["john"])

    def dispatch(self, result: Arparma, next_):
        return next_(f"Hello! {result.name}")
