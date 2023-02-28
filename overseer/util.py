import re

def parse_nodelist(nodelist: str):
    match = re.match(r'learnfair\[([0-9\-]+(?:,[0-9\-]+)*)\]', nodelist)
    nodelist = match.group(1)
    node_groups = nodelist.split(',')
    node_nums = []
    for n in node_groups:
        if '-' in n:
            for i in range(int(n.split('-')[0]), int(n.split('-')[1]) + 1):
                node_nums.append(str(i).zfill(4))
        else:
            node_nums.append(n)
    return [f'learnfair{i}' for i in node_nums]