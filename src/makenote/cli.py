import click
import makenote.config as _cfg


@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0", prog_name="mn", message="%(prog)s %(version)s")
@click.pass_context
def main(ctx: click.Context) -> None:
    """mn — fast terminal note logging."""
    if not _cfg.config_exists() and ctx.invoked_subcommand != "config":
        click.echo("No config found. Running first-time setup.")
        _cfg.run_config_flow()
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
def config() -> None:
    """Edit configuration."""
    _cfg.run_config_flow()
