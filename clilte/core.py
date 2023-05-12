from __future__ import annotations

import sys
from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field, InitVar
from importlib.metadata import entry_points
from pathlib import Path
from typing import Callable, TypeVar, overload, Literal

from arclet.alconna import (
    Alconna,
    Arparma,
    Args,
    Option,
    CommandMeta,
    command_manager,
    namespace
)
from arclet.alconna.exceptions import SpecialOptionTriggered
from arclet.alconna.tools import ShellTextFormatter, RichConsoleFormatter

cli_instance: ContextVar[CommandLine] = ContextVar("litecli")


def handle_argv():
    path = Path(sys.argv[0])
    head = path.stem
    if head == "__main__":
        head = path.parent.stem
    return head


@dataclass
class PluginMetadata:
    name: str
    version: str
    description: str = field(default="Unknown")
    tags: list[str] = field(default_factory=list)
    author: list[str] = field(default_factory=list)
    priority: int = field(default=16)


class BasePlugin(metaclass=ABCMeta):

    def __init__(self):
        self.metadata: PluginMetadata = self.meta()
        self.command: Alconna | str = self.init()
        if isinstance(self.command, Alconna):
            self.name: str = self.command.name
            if (
                not self.command.meta.description
                or self.command.meta.description == "Unknown"
            ):
                self.command.meta = (
                        self.metadata.description or self.metadata.name or "Unknown"
                )
            command_manager.delete(self.command)
            ns = cli_instance.get()._command.namespace_config
            self.command.namespace = ns.name
            self.command.path = f"{ns.name}::{self.command.name}"
            self.command.prefixes = []
            self.command.options = self.command.options[:-3]

            self.command.meta.fuzzy_match = ns.fuzzy_match or self.command.meta.fuzzy_match
            self.command.meta.raise_exception = ns.raise_exception or self.command.meta.raise_exception
            self.command._hash = self.command._calc_hash()
            command_manager.register(self.command)
        else:
            self.name: str = self.command

    @abstractmethod
    def init(self) -> Alconna | str:
        """
        插件创建方法, 该方法只会调用一次

        若返回 Alconna, 则表示创建一个新的子命令, 该子命令的名称为插件的名称

        若返回 str, 则表示该插件不创建子命令, 该 str 会成为插件的名称
        """

    @abstractmethod
    def meta(self) -> PluginMetadata:
        """
        提供描述信息的方法
        """

    @abstractmethod
    def dispatch(self, result: Arparma) -> bool | None:
        """
        插件的主要逻辑

        若返回 True, 则表示插件继续传播
        若返回 None, 则表示插件传播结束
        若返回 False, 则表示命令执行结束
        """

    def supply_options(self) -> list[Option] | None:
        """
        为主命令提供额外的选项
        """
        return


_storage: dict[str, list[type[BasePlugin]]] = {}
TPlugin = TypeVar("TPlugin", bound=BasePlugin)


def register(target: str):
    def wrapper(cls: type[BasePlugin]):
        _storage.setdefault(target, []).append(cls)
        return cls

    return wrapper


@dataclass(repr=True)
class CommandLine:
    title: str
    version: str
    _name: InitVar[str | None] = field(default=None)
    load_preset: bool = field(default=True)
    rich: bool = field(default=False)
    fuzzy_match: InitVar[bool] = field(default=False)
    plugins: dict[str, BasePlugin] = field(default_factory=dict, init=False)
    _command: Alconna = field(init=False)
    callback: Callable[[Arparma], None] = field(default_factory=lambda: (lambda x: None), init=False)

    def __post_init__(self, _name: str | None, fuzzy_match: bool):
        if _name is None:
            self._command = Alconna(
                formatter_type=RichConsoleFormatter if self.rich else ShellTextFormatter,
                meta=CommandMeta(fuzzy_match=fuzzy_match, description=self.title)
            )
        else:
            self._command = Alconna(
                _name,
                formatter_type=RichConsoleFormatter if self.rich else ShellTextFormatter,
                meta=CommandMeta(fuzzy_match=fuzzy_match, description=self.title),
            )
        with namespace(self.name) as np:
            np.headers = []
            np.separators = (" ",)
            np.fuzzy_match = fuzzy_match
            np.formatter_type = RichConsoleFormatter if self.rich else ShellTextFormatter

    @property
    def name(self):
        return self._command.command

    @classmethod
    def current(cls):
        return cli_instance.get()

    @contextmanager
    def using(self):
        token = cli_instance.set(self)
        yield
        cli_instance.reset(token)

    def arguments(self, args: Args):
        command_manager.delete(self._command)
        self._command.args.__merge__(args)
        command_manager.register(self._command)

    def set_callback(self, callback: Callable[[Arparma], None]):
        self.callback = callback

    def add(self, *command: type[TPlugin]):
        with self.using():
            res: list[TPlugin] = [cls() for cls in command]
        for plg in res:
            self.plugins[plg.name] = plg
            if isinstance(plg.command, Alconna):
                self._command.add(plg.command)
            if _opts := plg.supply_options():
                for _opt in _opts:
                    self._command.add(_opt)
        return res

    def preset(self):
        for cls in _storage.get(self._command.command, []) + _storage.get("*", []):
            self.add(cls)

    def load_register(self, target: str):
        if target in (self._command.command, "*"):
            return
        for cls in _storage.get(target, []):
            self.add(cls)

    def load_entry(self):
        for entry in entry_points().get(f"litecli.{self.name}.plugins", []):
            self.add(entry.load())

    @overload
    def get_plugin(self, plg: type[TPlugin], default: Literal[True]) -> TPlugin:
        ...

    def get_plugin(self, plg: type[TPlugin], default: bool = False) -> TPlugin | None:
        return next(
            filter(lambda x: isinstance(x, plg), self.plugins.values()),
            self.add(plg)[0] if default else None,
        )

    def query(self, *tag: str):
        yield from filter(
            lambda x: set(x.metadata.tags).issuperset(tag), self.plugins.values()
        )

    @property
    def help(self):
        return self._command.get_help()

    def main(self, *args: str):
        if self.load_preset:
            self.preset()
        self.load_entry()
        if args:
            res = self._command.parse(list(args))  # type: ignore
        else:
            head = handle_argv()
            if head != self._command.command:
                res = self._command.parse(sys.argv[1:])  # type: ignore
            else:
                res = self._command.parse([head, *sys.argv[1:]])  # type: ignore
        if not res.matched:
            if isinstance(res.error_info, SpecialOptionTriggered):
                return
            return print(res.error_info)
        if res.non_component and not res.all_matched_args:
            return print(self.help)
        with self.using():
            for plg in sorted(self.plugins.values(), key=lambda x: x.metadata.priority):
                ans = plg.dispatch(res)
                if ans is None:
                    break
                if not ans:
                    return
            self.callback(res)


__all__ = ["PluginMetadata", "BasePlugin", "CommandLine", "register"]
