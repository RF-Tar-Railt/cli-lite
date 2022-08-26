# Cli-Lite

A simple framework to build a cli tool. Base on [`Alconna`](https://github/ArcletProject/Alconna)

## install

```powershell
pip install cli-lite
```

## example

write as sample:

```python
from clilte import BasePlugin, CommandLine, PluginMetadata
from arclet.alconna import Alconna, Arpamar, Args

class MyPlugin(BasePlugin):
    
    def _init_plugin(self) -> Alconna:
        return Alconna("hello", Args["name", str])

    def dispatch(self, result: Arpamar):
        return print(f"Hello! {result.name}")

    def meta(self) -> PluginMetadata:
        return PluginMetadata("hellp", "0.0.1",  "my first plugin", ["dev"], ["john"])

if __name__ == '__main__':
    cli = CommandLine("test", "My first CLI", "0.0.1")
    cli.add(MyPlugin)
    cli.main(load_preset=True)
```

and execute the line:

```powershell
python test.py hello world
```

