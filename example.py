from clilte import BaseCommand, CommandLine, CommandMetadata
from arclet.alconna import Alconna, Arparma, Args, CommandMeta


class MyCommand(BaseCommand):

    def init_plugin(self) -> Alconna:
        return Alconna("hello", Args["name", str], meta=CommandMeta("test command"))

    def dispatch(self, result: Arparma):
        return print(f"Hello! {result.name}")

    def meta(self) -> CommandMetadata:
        return CommandMetadata("hello", "0.0.1", "my first plugin", ["dev"], ["john"])


if __name__ == '__main__':
    cli = CommandLine("test", "My first CLI", "0.0.1")
    cli.add(MyCommand)
    cli.load_register('builtin.cache')
    cli.main(["test"])
