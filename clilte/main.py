from __future__ import annotations

import sys
from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from importlib.metadata import entry_points
from typing import Any, Callable, TypeVar, overload, Literal

from arclet.alconna import (
    Alconna,
    Arparma,
    ArparmaBehavior,
    command_manager,
    namespace,
    output_manager,
)
from arclet.alconna.tools import ArgParserTextFormatter

cli_instance: ContextVar[CommandLine] = ContextVar("litecli")


@dataclass
class CommandMetadata:
    name: str
    version: str
    description: str | None = field(default=None)
    tags: list[str] = field(default_factory=list)
    author: list[str] = field(default_factory=list)


def _generate_behavior(func: Callable[[Arparma], Any]) -> ArparmaBehavior:
    class _(ArparmaBehavior):
        operate = staticmethod(func)

    return _()


class BaseCommand(metaclass=ABCMeta):
    _option = False

    def __init__(self):
        self.metadata = self.meta()
        self.command = self.init_plugin()
        self.command.reset_namespace(
            cli_instance.get().prefix, not self.__class__._option
        )
        self.command.behaviors.append(_generate_behavior(self.dispatch))
        if not self.command.meta.description or self.command.meta.description == "Unknown":
            self.command.meta = self.metadata.description or self.metadata.name or "Unknown"

    def __init_subclass__(cls, **kwargs):
        if kwargs.get("option", False):
            cls._option = True
        super().__init_subclass__()

    @abstractmethod
    def init_plugin(self) -> Alconna:
        """
        插件创建方法, 该方法只会调用一次
        """

    @abstractmethod
    def dispatch(self, result: Arparma):
        """
        当该插件命令解析成功后该方法负责将解析结果分发给指定的处理函数
        """

    @abstractmethod
    def meta(self) -> CommandMetadata:
        """
        提供描述信息的方法
        """


_storage: dict[str, list[type[BaseCommand]]] = {}
TPlugin = TypeVar("TPlugin", bound=BaseCommand)


def register(target: str):
    def wrapper(cls: type[BaseCommand]):
        _storage.setdefault(target, []).append(cls)
        return cls

    return wrapper

def generate_help(cli: 'CommandLine'):
    cmds = []
    cmds_description = []
    max_len = 1
    for name, plg in cli.plugins.items():
        if plg.command.headers and plg.command.command:
            cmds.append(
                f"[{''.join(map(str, plg.command.headers))}]{plg.command.command}"
            )
        elif plg.command.headers:
            cmds.append(
                f"[{', '.join(sorted(map(str, plg.command.headers), key=len, reverse=True))}"
            )
        else:
            cmds.append(f"{name}")
        cmds_description.append(plg.command.meta.description)
    if cmds:
        max_len = max(max(map(len, cmds)), max_len)
    opts = []
    opts_description = []
    for name, opt in cli.options.items():
        if opt.command.headers and opt.command.command:
            opts.append(
                f"[{''.join(map(str, opt.command.headers))}]{opt.command.command}"
            )
        elif opt.command.headers:
            opts.append(
                f"{', '.join(sorted(map(str, opt.command.headers), key=len))}"
            )
        else:
            opts.append(f"{name}")
        opts_description.append(opt.command.meta.description)
    if opts:
        max_len = max(max(map(len, opts)), max_len)
    cmd_string = "\n".join(
        f"    {i.ljust(max_len)}\t{j}" for i, j in zip(cmds, cmds_description)
    )
    opt_string = "\n".join(
        f"    {i.ljust(max_len)}\t{j}" for i, j in zip(opts, opts_description)
    )
    cmd_help = "Commands:\n" if cmd_string else ""
    opt_help = "Options:\n" if opt_string else ""
    return (
        f"{cli.name}\n\n"
        f"{cmd_help}{cmd_string}\n{opt_help}{opt_string}\n\n"
        "Use '$ <command> --help | -h' for more information about a command."
    )


class CommandLine:
    prefix: str
    name: str
    version: tuple[int, int, int]
    plugins: dict[str, BaseCommand]
    options: dict[str, BaseCommand]

    def __init__(
        self,
        prefix: str,
        name: str,
        version: str | tuple[int, int, int],
        fuzzy_match: bool = False,
        argparser_formatter: bool = False,
        load_preset: bool = True,
        helper: Callable[['CommandLine'], str] = generate_help,
    ):
        self.prefix = prefix.lower().replace(" ", "_")
        self.name = name
        self.version = (
            tuple(map(int, version.split("."))) if isinstance(version, str) else version
        )
        self.plugins = {}
        self.options = {}
        self.load_preset = load_preset
        self.helper = helper
        with namespace(prefix) as np:
            np.headers = []
            np.separators = (" ",)
            np.fuzzy_match = fuzzy_match
            if argparser_formatter:
                np.formatter_type = ArgParserTextFormatter

    @classmethod
    def current(cls):
        return cli_instance.get()

    @contextmanager
    def using(self):
        token = cli_instance.set(self)
        yield
        cli_instance.reset(token)

    def add(self, *plugin: type[TPlugin]):
        with self.using():
            res: list[TPlugin] = [cls() for cls in plugin]
        for plg in res:
            if plg._option:
                self.options[plg.command.name] = plg
            else:
                self.plugins[plg.command.name] = plg
        return res

    def preset(self):
        for cls in _storage.get(self.prefix, []) + _storage.get("*", []):
            self.add(cls)

    def load_register(self, target: str):
        if target in (self.prefix, "*"):
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
        return self.helper(self)

    def main(self, args: list[str] | None = None):
        if self.load_preset:
            self.preset()
        self.load_entry()
        args = sys.argv[1:] or args
        if args and args[0] == self.prefix:
            args.pop(0)
        if not args:
            print(self.help)
            return
        text = " ".join(args)
        with self.using():
            for alc in command_manager.get_commands(namespace=self.prefix):
                may_output_text = None

                def _h(string):
                    nonlocal may_output_text
                    may_output_text = string

                output_manager.set_action(_h, alc.name)
                try:
                    _res = alc.parse(text)
                except Exception as e:
                    _res = Arparma(alc.path, text)
                    _res.head_matched = False
                    _res.matched = False
                    _res.error_info = repr(e)
                if not may_output_text and not _res.matched and not _res.head_matched:
                    continue
                if not may_output_text and _res.error_info:
                    may_output_text = f"{self.name}\n\n{alc.get_help()}"
                if not may_output_text and _res.matched:
                    break
                if may_output_text:
                    print(may_output_text)
                    break
            else:
                print(self.help)


__all__ = ["CommandMetadata", "BaseCommand", "CommandLine", "register"]
