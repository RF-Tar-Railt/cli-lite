from arclet.alconna import Alconna, Arpamar, CommandMeta
from .main import register, BasePlugin, PluginMetadata, CommandLine


@register("*")
class Help(BasePlugin):
    def _init_plugin(self) -> Alconna:
        return Alconna(["--help", "-h"], meta=CommandMeta("显示帮助"))

    def dispatch(self, result: Arpamar):
        print(CommandLine.current().help)
        return True

    def meta(self) -> PluginMetadata:
        return PluginMetadata("help", "0.0.1", "help", ["help"], ["rf"])


@register("*")
class Version(BasePlugin):
    def _init_plugin(self) -> Alconna:
        return Alconna(["--version", "-v"], meta=CommandMeta("显示版本"))

    def dispatch(self, result: Arpamar):
        print('.'.join(map(str, self.cli_version)))

    def meta(self) -> PluginMetadata:
        return PluginMetadata("version", "0.0.1", "version", ["version"], ["rf"])
