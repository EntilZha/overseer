from pathlib import Path
import logging
import socket
import time
import typer
from rich.logging import RichHandler
from overseer.record import get_slurm_env, record_stats

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

app = typer.Typer()


@app.command()
def record(stats_dir: str, interval: int = 15):
    stats_dir = Path(stats_dir)
    slurm_env = get_slurm_env()
    hostname = socket.gethostname()
    stats_dir = stats_dir / hostname
    if slurm_env is not None:
        slurm_path = "slurm_J{}_N{}_L{}_P{}".format(
            slurm_env["SLURM_JOB_ID"],
            slurm_env["SLURM_NODEID"],
            slurm_env["SLURM_LOCALID"],
            slurm_env["SLURM_PROCID"],
        )
        stats_dir = stats_dir / slurm_path
    stats_dir.mkdir(parents=True, exist_ok=True)
    while True:
        record_stats(stats_dir)
        time.sleep(interval)


@app.command()
def nop():
    pass


if __name__ == "__main__":
    app()
