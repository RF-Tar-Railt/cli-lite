from __future__ import annotations

import json
import os
from pprint import pprint
from pathlib import Path
from typing import Any
from arclet.alconna import Alconna, Arparma, CommandMeta, Option
from .core import register, BasePlugin, PluginMetadata, CommandLine


@register("*")
class Version(BasePlugin):
    def init(self) -> Alconna | str:
        return "version"

    def supply_options(self) -> list[Option] | None:
        return [
            Option("--version|-V", help_text="show the version and exit")
        ]

    def dispatch(self, result: Arparma):
        if result.find("version"):
            print(CommandLine.current().version)
            return False
        return True

    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            "version", "0.1.0", "version", ["version"], ["RF-Tar-Railt"], 0
        )


@register("builtin.cache")
class Cache(BasePlugin):
    path: Path
    data: dict[str, Any]

    def init(self) -> Alconna:
        self.path = Path(f'.{CommandLine.current().name}.json')
        self.data = {}
        if self.path.exists():
            with self.path.open('r+', encoding='UTF-8') as f_obj:
                self.data.update(json.load(f_obj))
        return Alconna(
            "cache",
            Option("clear", help_text="清理缓存"),
            Option("show", help_text="显示内容"),
            meta=CommandMeta("管理缓存")
        )

    def dispatch(self, result: Arparma):
        if result.find("cache.show"):
            print('---------------------------------')
            print(f'in "{os.getcwd()}{os.sep}{self.path.name}":')
            pprint(self.data)
            return
        if result.find("cache.clear"):
            self.data.clear()
            if self.path.exists():
                print('---------------------------------')
                print(f"removed {os.getcwd()}{os.sep}{self.path.name}.")
                self.path.unlink(True)
                return
            print("cache cleared")
            return
        if result.find("cache"):
            print(self.command.get_help())
        return

    def meta(self) -> PluginMetadata:
        return PluginMetadata("cache", "0.1.0", "管理缓存", ["cache", "dev"], ["RF-Tar-Railt"])

    def save(self):
        with self.path.open('w+', encoding='UTF-8') as f_obj:
            json.dump(self.data, f_obj, ensure_ascii=False, indent=4)
