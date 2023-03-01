import logging
from pathlib import Path
import psutil
import subprocess
import socket
import os
import datetime
import psutil
import numpy as np
import polars as pl
import io

GB = 1_024 * 1_024 * 1_024


def get_system_stats():
    cpu_per_cpu = psutil.cpu_percent(percpu=True)
    cpu_total = psutil.cpu_percent()
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    loadavg = psutil.getloadavg()
    # disk_io = psutil.disk_io_counters(perdisk=True)
    disk_util = psutil.disk_usage("/")
    hostname = socket.gethostname()
    data_time = datetime.datetime.now()
    return {
        "cpu_per_cpu (%)": cpu_per_cpu,
        "cpu_total (%)": cpu_total,
        "cpu_avg (%)": np.mean(cpu_per_cpu),
        "disk_total (GB)": disk_util.total / GB,
        "disk_percent (%)": disk_util.percent,
        "mem_total (GB)": vm.total / GB,
        "mem_available (GB)": vm.available / GB,
        "mem_used (GB)": vm.used / GB,
        "mem_percent (%)": vm.percent,
        "swap_total (GB)": swap.total / GB,
        "swap_used (GB)": swap.used / GB,
        "swap_free (GB)": swap.free / GB,
        "swap_percent (%)": swap.percent,
        #'disk_read_count:checkpoint': disk_io.read_count,
        #'disk_write_count:checkpoint': disk_io.write_count,
        #'disk_read_gb:checkpoint': disk_io.read_bytes / GB,
        #'disk_write_gb:checkpoint': disk_io.write_bytes / GB,
        "loadavg_1 (%)": loadavg[0],
        "loadavg_5 (%)": loadavg[1],
        "loadavg_15 (%)": loadavg[2],
        "hostname": hostname,
        "ip": socket.gethostbyname(hostname),
        "datetime": str(data_time),
        "timestamp": data_time.timestamp(),
    }


def get_gpu_stats():
    query = "index,gpu_name,utilization.gpu,utilization.memory,memory.used,memory.total,memory.free"
    try:
        out = subprocess.run(
            ["nvidia-smi", f"--query-gpu={query}", "--format=csv"],
            check=True,
            capture_output=True,
        )
        rows = out.stdout.decode()
        df = pl.read_csv(io.StringIO(rows))
        return df
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_slurm_env():
    slurm_env = {}
    env = os.environ
    slurm_env["SLURM_JOB_ID"] = env.get("SLURM_JOB_ID")
    if slurm_env["SLURM_JOB_ID"] is None:
        return None
    slurm_env["SLURM_LOCALID"] = env.get("SLURM_LOCALID")
    slurm_env["SLURM_NODEID"] = env.get("SLURM_NODEID")
    slurm_env["SLURM_PROCID"] = env.get("SLURM_PROCID")
    return slurm_env


def record_stats(stats_dir: Path):
    logging.info("Logging stats to: %s", stats_dir)
    system_stats = get_system_stats()
    new_system_stats_df = pl.DataFrame([system_stats])
    logging.info("Datetime: %s", system_stats["datetime"])
    gpu_stats = get_gpu_stats()
    system_file = stats_dir / "system.feather"
    gpu_file = stats_dir / "gpu.feather"
    if system_file.exists():
        logging.info("System stats file exists, appending...")
        system_df = pl.read_ipc(str(system_file))
        logging.info("System stats file has %d rows", len(system_df))
        logging.info("New stats had %d rows", len(new_system_stats_df))
        system_df = pl.concat([system_df, new_system_stats_df])
    else:
        logging.info(
            "System stats file does not exist, creating with %d rows",
            len(new_system_stats_df),
        )
        print(new_system_stats_df)
        system_df = new_system_stats_df

    system_df.write_ipc(str(system_file))

    if gpu_stats is not None:
        if gpu_file.exists():
            gpu_df = pl.read_ipc(str(gpu_file))
            gpu_df = pl.concat([gpu_df, gpu_stats])
        else:
            gpu_df = gpu_stats
        gpu_df.write_ipc(str(gpu_file))
