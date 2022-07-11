# Lite-Cli

A simple framework to build a cli tool. Base on [`Alconna`](https://github/ArcletProject/Alconna)

## example

write as sample:

```python
from litecli import BasePlugin, CommandLine, PluginMetadata
from arclet.alconna import Alconna, Arpamar, Args

class MyPlugin(BasePlugin):
    
    def _init_command(self) -> Alconna:
        return Alconna("hello", Args["name", str])

    def dispatch(self, result: Arpamar):
        return print(f"Hello! {result.name}")

    def meta(self) -> PluginMetadata:
        return {"name": "hello", "description": "my first plugin", "author": ["john"], "tags": ["dev"], "version": "0.0.1"}

if __name__ == '__main__':
    cli = CommandLine("test", "My first CLI", "0.0.1")
    cli.add(MyPlugin)
    cli.main(load_preset=True)
```

and execute the line:

```powershell
python test.py hello world
```

