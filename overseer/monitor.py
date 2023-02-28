import re
import os
from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st

from overseer.util import parse_nodelist
from overseer.record import get_system_stats

st.set_page_config(layout="wide")

def metric_group(metric):
    prefix = metric.split('_')
    if len(prefix) == 1:
        return 'NA'
    else:
        return prefix[0]

def metric_scale(metric):
    if '%' in metric:
        return 'Percent (%)'
    elif 'GB' in metric:
        return 'Gigabytes (GB)'
    else:
        return 'NA'



def sort_groups(group):
    if group == 'cpu':
        return 0
    elif group == 'mem':
        return 1
    elif group == 'swap':
        return 2
    elif group == 'disk':
        return 3
    else:
        return 4


JOB_RE = r'slurm_J([0-9]+)_N[0-9]+_L[0-9]+_P[0-9]+'

def parse_job_id(job):
    return re.match(JOB_RE, job).group(1)


def collect_stats(stats_dir: Path):
    """
    Structure will be either:
    - {stats_dir}/{hostname}/{system,gpu}.feather
    - {stats_dir}/{hostname}/slurm_J{}_N{}_L{}_P{}/{system,gpu}.feather
    Where: J=jobid, N=nodeid, L=localid, P=procid
    """
    hostnames = set()
    system_frames = []
    gpu_frames = []
    local_system_stats_files = Path(stats_dir).glob('*/system.feather')
    
    for f in local_system_stats_files:
        df = pd.read_feather(f)
        df['job'] = 'local'
        system_frames.append(df)
        hostnames.add(f.parent.name)

    local_gpu_stats_files = Path(stats_dir).glob('*/gpu.feather')
    for f in local_gpu_stats_files:
        df = pd.read_feather(f)
        df['job'] = 'local'
        gpu_frames.append(df)
        hostnames.add(f.parent.name)

    slurm_jobs = set()
    slurm_system_stats_files = Path(stats_dir).glob("*/slurm_*/system.feather")
    for f in slurm_system_stats_files:
        df = pd.read_feather(f)
        df['job'] = f.parent.name
        slurm_jobs.add(parse_job_id(f.parent.name))
        system_frames.append(df)
        hostnames.add(f.parent.parent.name)

    slurm_gpu_stats_files = Path(stats_dir).glob("*/slurm_*/gpu.feather")
    for f in slurm_gpu_stats_files:
        df = pd.read_feather(f)
        slurm_jobs.add(parse_job_id(f.parent.name))
        df['job'] = f.parent.name
        gpu_frames.append(df)
        hostnames.add(f.parent.parent.name)
    
    if len(system_frames) > 0:
        system_df = pd.concat(system_frames)
    else:
        system_df = None
    
    if len(gpu_frames) > 0:
        gpu_df = pd.concat(gpu_frames)
    else:
        gpu_df = None

    return {
        'system': system_df,
        'gpu': gpu_df,
        'slurm_jobs': slurm_jobs,
        'hostnames': hostnames,
    }



with st.sidebar:
    STATS_ENV = os.environ.get('OVERSEER_STATS_ROOT', '/checkpoint/par/overseer')
    STATS_ROOT = Path(st.text_input('Root Path', STATS_ENV))
    stats_dict = collect_stats(STATS_ROOT)
    hostnames = stats_dict['hostnames']
    slurm_jobs = stats_dict['slurm_jobs']
    system_df = stats_dict['system']
    gpu_df = stats_dict['gpu']
    st.header("Cluster Info")
    st.write("Enter SLURM Nodelist or Hostname")
    selected_hostnames = st.multiselect("Hostname", sorted(hostnames), default=hostnames)
    nodelist = st.text_input("Filter by Nodelist", "", help='E.G. learnfair[1078,1080,1131-1132]')
    if nodelist != '':
        filtered_hostnames = set(parse_nodelist(nodelist))
        selected_hostnames = [h for h in selected_hostnames if h in filtered_hostnames]
    groups = set(metric_group(m) for m in get_system_stats().keys())
    selected_groups = sorted(st.multiselect("Metric Groups", groups, default=sorted(groups, key=sort_groups)), key=sort_groups)



st.header("System")
system_df["datetime"] = pd.to_datetime(system_df["datetime"])
melt_sys_df = system_df.drop(columns=["timestamp", "ip", "cpu_per_cpu (%)"]).melt(
    id_vars=["hostname", "datetime"],
    var_name="metric",
    value_name="value"
)
melt_sys_df['metric_group'] = melt_sys_df['metric'].map(metric_group)
melt_sys_df['scale'] = melt_sys_df['metric'].map(metric_scale)
melt_sys_df = melt_sys_df[melt_sys_df.hostname.isin(selected_hostnames)]
    
# st.write(melt_sys_df)

for g in selected_groups:
    st.subheader(f'Metric Group: {g}')
    for scale in ['Percent (%)', 'Gigabytes (GB)']:
        chart_df = melt_sys_df[(melt_sys_df["metric_group"] == g) & (melt_sys_df["scale"] == scale)]
        if len(chart_df) > 0:
            chart = (
                alt.Chart(chart_df)
                .mark_line()
                .encode(
                    x="datetime",
                    y=alt.Y("value", title=scale),
                    color=alt.Color('hostname'),
                )
                .facet("metric", columns=3)
                .resolve_scale(y="independent")
            )
            st.write(chart)

st.header("GPU")
st.write(gpu_df)
