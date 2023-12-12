from __future__ import annotations

from clilte import BasePlugin, PluginMetadata
from arclet.alconna import Alconna, Arparma, Args, CommandMeta


class MyPlugin1(BasePlugin):

    def init(self) -> Alconna | str:
        return Alconna(
            self.local,
            Args["name", str],
            meta=CommandMeta("test command")
        )

    def meta(self) -> PluginMetadata:
        return PluginMetadata("hello", "0.0.1", "my first plugin", ["dev"], ["john"])

    def dispatch(self, result: Arparma) -> bool | None:
        print(f"Hello! {result.name}")
        return True
