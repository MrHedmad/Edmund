For future me: All scripts in here that do not start with a _ and end with a `.py` file extension will be loaded. Just make sure that they include the decorators provided by `cli`:

```
from edmund.entrypoint import cli

@cli.command()
@click.argument(some_arg)
def some_command(some_arg):
    """Some help message
    """
    ...
```
