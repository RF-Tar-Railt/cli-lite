from __future__ import annotations

import sys
from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field, InitVar
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
    description: str = field(default="Unknown")
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
        self.command = self.init()
        self.command.reset_namespace(
            cli_instance.get().prefix, not self.__class__._option
        )
        self.command.behaviors.append(_generate_behavior(self.dispatch))
        if (
            not self.command.meta.description
            or self.command.meta.description == "Unknown"
        ):
            self.command.meta = (
                self.metadata.description or self.metadata.name or "Unknown"
            )

    def __init_subclass__(cls, **kwargs):
        if kwargs.get("option", False):
            cls._option = True
        super().__init_subclass__()

    @abstractmethod
    def init(self) -> Alconna:
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
TCommand = TypeVar("TCommand", bound=BaseCommand)


def register(target: str):
    def wrapper(cls: type[BaseCommand]):
        _storage.setdefault(target, []).append(cls)
        return cls

    return wrapper


@dataclass
class Helper:
    cli: CommandLine

    def cmds(self):
        yield from self.cli.commands.keys()

    def cmd_descriptions(self):
        for cmd in self.cli.commands.values():
            yield cmd.metadata.description

    def opts(self):
        for name, opt in self.cli.options.items():
            if opt.command.headers and opt.command.command:
                yield f"[{''.join(map(str, opt.command.headers))}]{opt.command.command}"
            elif opt.command.headers:
                yield f"{', '.join(sorted(map(str, opt.command.headers), key=len))}"
            else:
                yield name

    def opts_descriptions(self):
        for opt in self.cli.commands.values():
            yield opt.metadata.description

    def cmd_line(self, name, desc, max_len: int = 0):
        return f"  {name:<{max_len}}    {desc}"

    def opt_line(self, name, desc, max_len: int = 0):
        return f"  {name:<{max_len}}    {desc}"

    def lines(self, cmd_title: str = "Commands", opt_title: str = "Options"):
        cmds, opts, = list(self.cmds()), list(self.opts())
        cmd_desc, opt_desc = list(self.cmd_descriptions()), list(self.opts_descriptions())
        max_len = max(max(map(len, cmds or [''])), max(map(len, opts or [''])))
        cmd_string = "\n".join(self.cmd_line(i, j, max_len) for i, j in zip(cmds, cmd_desc))
        opt_string = "\n".join(self.opt_line(i, j, max_len) for i, j in zip(opts, opt_desc))
        return f"{cmd_title}:\n{cmd_string}\n{opt_title}:\n{opt_string}"

    def help(self):
        footer = f"Use '{self.cli.prefix} <command> --help' for more information about a command."
        return f"{self.cli.name}\n\n{self.lines()}\n\n{footer}"


@dataclass(repr=True)
class CommandLine:
    prefix: str
    name: str
    version: str
    output_action: Callable[[str], ...] = field(default=lambda x: print(x))
    load_preset: bool = field(default=True)
    fuzzy_match: InitVar[bool] = field(default=False)
    argparser_formatter: InitVar[bool] = field(default=False)
    _helper: InitVar[type[Helper]] = field(default=Helper)
    helper: Helper = field(init=False)
    commands: dict[str, BaseCommand] = field(init=False, default_factory=dict)
    options: dict[str, BaseCommand] = field(init=False, default_factory=dict)

    def __post_init__(self, fuzzy_match: bool, argparser_formatter: bool, _helper: type[Helper]):
        self.prefix = self.prefix.lower().replace(" ", "_")
        self.helper = _helper(self)
        with namespace(self.prefix) as np:
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

    def add(self, *command: type[TCommand]):
        with self.using():
            res: list[TCommand] = [cls() for cls in command]
        for plg in res:
            if plg._option or plg.command.command.startswith("-"):
                self.options[plg.command.name] = plg
            else:
                self.commands[plg.command.name] = plg
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
    def get_command(self, plg: type[TCommand], default: Literal[True]) -> TCommand:
        ...

    def get_command(self, plg: type[TCommand], default: bool = False) -> TCommand | None:
        return next(
            filter(lambda x: isinstance(x, plg), self.commands.values()),
            self.add(plg)[0] if default else None,
        )

    def query(self, *tag: str):
        yield from filter(
            lambda x: set(x.metadata.tags).issuperset(tag), self.commands.values()
        )

    @property
    def help(self):
        return self.helper.help()

    def main(self, args: list[str] | None = None):
        if self.load_preset:
            self.preset()
        self.load_entry()
        args = sys.argv[1:] or args
        if args and args[0] == self.prefix:
            args.pop(0)
        if not args:
            return self.output_action(self.help)
        text = " ".join(args)
        with self.using():
            for alc in command_manager.get_commands(namespace=self.prefix):
                with output_manager.capture(alc.name) as cap:
                    output_manager.set_action(lambda x: x, alc.name)
                    try:
                        _res = alc.parse(message)  # type: ignore
                    except Exception as e:
                        _res = Arparma(alc.path, text, False, error_info=repr(e))
                    may_output_text: str | None = cap.get("output", None)
                if not may_output_text and not _res.matched and not _res.head_matched:
                    continue
                if not may_output_text and _res.error_info:
                    may_output_text = f"{self.name}\n\n{alc.get_help()}"
                if not may_output_text and _res.matched:
                    break
                if may_output_text:
                    self.output_action(may_output_text)
                    break
            else:
                return self.output_action(self.help)


__all__ = ["CommandMetadata", "BaseCommand", "CommandLine", "register", "Helper"]
