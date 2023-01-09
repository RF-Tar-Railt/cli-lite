# Cli-Lite

A simple framework to build a cli tool. Base on [`Alconna`](https://github/ArcletProject/Alconna)

## install

```powershell
pip install cli-lite
```

## example

write as sample:

```python
from clilte import BaseCommand, CommandLine, CommandMetadata
from arclet.alconna import Alconna, Arparma, Args


class MyCommand(BaseCommand):

    def init_plugin(self) -> Alconna:
        return Alconna("hello", Args["name", str])

    def dispatch(self, result: Arparma):
        return print(f"Hello! {result.name}")

    def meta(self) -> CommandMetadata:
        return CommandMetadata("hello", "0.0.1", "my first plugin", ["dev"], ["john"])


if __name__ == '__main__':
    cli = CommandLine(
        "test",
        "My first CLI",
        "0.0.1"
    )
    cli.add(MyCommand)
    cli.main()
```

and execute the line:

```powershell
python test.py hello world
```

