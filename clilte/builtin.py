from arclet.alconna import Alconna, Arpamar
from .main import register, BasePlugin, PluginMetadata, CommandLine


@register("*")
class Help(BasePlugin):
    def _init_plugin(self) -> Alconna:
        return Alconna(headers=["--help", "-h"], help_text="显示帮助")

    def dispatch(self, result: Arpamar):
        print(CommandLine.current().help)
        return True

    def meta(self) -> PluginMetadata:
        return {
            "name": "help",
            "description": "help",
            "author": ["rf"],
            "tags": ["help"],
            "version": "0.0.1"
        }


@register("*")
class Version(BasePlugin):
    def _init_plugin(self) -> Alconna:
        return Alconna(headers=["--version", "-v"], help_text="显示版本")

    def dispatch(self, result: Arpamar):
        print('.'.join(f'{i}' for i in self.version))

    def meta(self) -> PluginMetadata:
        return {
            "name": "version",
            "description": "version",
            "author": ["rf"],
            "tags": ["version"],
            "version": "0.0.1"
        }
