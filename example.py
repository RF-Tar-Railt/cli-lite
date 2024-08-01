from __future__ import annotations

from clilte import BasePlugin, CommandLine, PluginMetadata
from arclet.alconna import Alconna, Arparma, Args, CommandMeta, Option


class MyPlugin(BasePlugin):

    def init(self) -> Alconna | str:
        return Alconna(
            "hello",
            Args["name", str],
            meta=CommandMeta("test command")
        )

    def meta(self) -> PluginMetadata:
        return PluginMetadata("hello", "0.0.1", "my first plugin", ["dev"], ["john"])

    def dispatch(self, result: Arparma) -> bool | None:
        print(f"Hello! {result.name}")
        return True

    @classmethod
    def supply_options(cls) -> list[Option] | None:
        return


if __name__ == '__main__':
    cli = CommandLine(title="My first CLI", version="example 0.0.1", rich=True, fuzzy_match=True)
    cli.add(MyPlugin)
    cli.load_plugins("examples")
    cli.load_register('builtin.cache')
    cli.main()
