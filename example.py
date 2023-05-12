from __future__ import annotations

from clilte import BasePlugin, CommandLine, PluginMetadata
from arclet.alconna import Alconna, Arparma, Args, CommandMeta


class MyPlugin(BasePlugin):

    def init(self) -> Alconna | str:
        return Alconna("hello", Args["name", str], meta=CommandMeta("test command"))

    def meta(self) -> PluginMetadata:
        return PluginMetadata("hello", "0.0.1", "my first plugin", ["dev"], ["john"])

    def dispatch(self, result: Arparma) -> bool | None:
        return print(f"Hello! {result.name}")


if __name__ == '__main__':
    cli = CommandLine(title="My first CLI", version="example 0.0.1")
    cli.add(MyPlugin)
    cli.load_register('builtin.cache')
    cli.main()
