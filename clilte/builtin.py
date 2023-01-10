from __future__ import annotations

import json
import os
from pprint import pprint
from pathlib import Path
from typing import Any
from arclet.alconna import Alconna, Arparma, CommandMeta, Option
from .main import register, BaseCommand, CommandMetadata, CommandLine


@register("*")
class Help(BaseCommand, option=True):
    def init(self) -> Alconna:
        return Alconna(["--help", "-h"], meta=CommandMeta("show this help message and exit"))

    def dispatch(self, result: Arparma):
        print(CommandLine.current().help)
        return True

    def meta(self) -> CommandMetadata:
        return CommandMetadata("help", "0.1.0", "help", ["help"], ["RF-Tar-Railt"])


@register("*")
class Version(BaseCommand, option=True):
    def init(self) -> Alconna:
        return Alconna(["--version", "-v"], meta=CommandMeta("show the version and exit"))

    def dispatch(self, result: Arparma):
        print('.'.join(map(str, CommandLine.current().version)))

    def meta(self) -> CommandMetadata:
        return CommandMetadata("version", "0.1.0", "version", ["version"], ["RF-Tar-Railt"])


@register("builtin.cache")
class Cache(BaseCommand):
    path: Path
    data: dict[str, Any]

    def init(self) -> Alconna:
        self.path = Path(f'.{CommandLine.current().prefix}.json')
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
        if result.find("show"):
            print('---------------------------------')
            print(f'in "{os.getcwd()}{os.sep}{self.path.name}":')
            return pprint(self.data)
        if result.find("clear"):
            self.data.clear()
            if self.path.exists():
                print('---------------------------------')
                print(f"removed {os.getcwd()}{os.sep}{self.path.name}.")
                return self.path.unlink(True)
            return print("cache cleared")
        return print(self.command.get_help())

    def meta(self) -> CommandMetadata:
        return CommandMetadata("cache", "0.1.0", "管理缓存", ["cache", "dev"], ["RF-Tar-Railt"])

    def save(self):
        with self.path.open('w+', encoding='UTF-8') as f_obj:
            json.dump(self.data, f_obj, ensure_ascii=False, indent=4)
