from typing import Tuple, Type, Dict, Optional, TypedDict, List, Callable, Any, Union
from abc import ABCMeta, abstractmethod
from importlib.metadata import entry_points
from arclet.alconna import command_manager, Alconna, Arpamar, ArpamarBehavior
from contextlib import contextmanager
from pathlib import Path
import sys
from contextvars import ContextVar

cli_instance: 'ContextVar[CommandLine]' = ContextVar("litecli")


class PluginMetadata(TypedDict):
    name: str
    version: str
    tags: List[str]
    author: List[str]
    description: str


def _generate_behavior(func: Callable[[Arpamar], Any]) -> ArpamarBehavior:
    class _(ArpamarBehavior):
        operate = staticmethod(func)

    return _()


class BasePlugin(metaclass=ABCMeta):
    def __init__(
            self,
            cli_name: str,
            version: Tuple[int, ...]
    ):
        self.cli_name = cli_name
        self.version = version
        self._command = self._init_plugin()
        self._command.reset_namespace(cli_name)
        self._command.behaviors.append(_generate_behavior(self.dispatch))
        self._path = Path(__file__)

    @property
    def command(self) -> Alconna:
        return self._command

    @abstractmethod
    def _init_plugin(self) -> Alconna:
        """
        插件创建方法, 该方法只会调用一次
        """

    @abstractmethod
    def dispatch(self, result: Arpamar):
        """
        当该插件命令解析成功后该方法负责将解析结果分发给指定的处理函数
        """

    @abstractmethod
    def meta(self) -> PluginMetadata:
        """
        提供描述信息的方法
        """


_storage: Dict[str, List[Type[BasePlugin]]] = {}


def register(target: str):
    def wrapper(cls: Type[BasePlugin]):
        _storage.setdefault(target, []).append(cls)
        return cls

    return wrapper


class CommandLine:
    prefix: str
    name: str
    version: Tuple[int, int, int]
    plugins: Dict[str, BasePlugin]

    def __init__(self, prefix: str, name: str, version: Union[str, Tuple[int, int, int]]):
        self.prefix = prefix
        self.name = name
        self.version = tuple(map(int, str.split('.'))) if isinstance(version, str) else version
        self.plugins = {}

    @classmethod
    def current(cls):
        return cli_instance.get()

    @contextmanager
    def using(self):
        token = cli_instance.set(self)
        yield
        cli_instance.reset(token)

    def add(self, *plugin: Type[BasePlugin]):
        for cls in plugin:
            plg = cls(self.name, self.version)
            self.plugins[plg.command.name] = plg

    def preset(self):
        for cls in (_storage.get(self.name, []) + _storage.get('*', [])):
            self.add(cls)

    def load_entry(self):
        for entry in entry_points().get(f"litecli.{self.name}.plugins", []):
            self.add(entry.load())

    @property
    def help(self):
        return f"{self.name} {'.'.join(map(str, self.version))}\n{command_manager.all_command_help(namespace=self.name)}"

    def main(self, args: Optional[List[str]] = None, load_preset: bool = False):
        if load_preset:
            self.preset()
        self.load_entry()
        if args is None:
            args = sys.argv[1:]
        if args and args[0] == self.prefix:
            args.pop(0)
        if not args:
            print(self.help)
            return
        text = " ".join(args)
        with self.using():
            for alc in command_manager.get_commands(namespace=self.name):
                alc.parse(text)


__all__ = ["PluginMetadata", "BasePlugin", "CommandLine", "register"]
