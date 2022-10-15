# apologies for the poorly written code :P
import os
import gc
import json
import numpy as np
import scipy.sparse as sparse
import ipywidgets as widgets
import pyvis.network as net
from ipywidgets import interactive, fixed
from IPython.display import display, IFrame, clear_output

def run(path="."):

    with open(f"{path}/data/countries.json", "r") as w:
        country_list = json.load(w)

    dropdown = widgets.Dropdown(
        options=country_list.items(),
        value="ar",
        description="Country:",
    )

    slider = widgets.IntSlider(
        value=50,
        min=0,
        max=500,
        step=1,
        description="Top unis:",
    )

    checkbox = widgets.Checkbox(
        value=False,
        description="Graph settings",
    )

    widget_menu = interactive(
        generate_graph,
        {"manual": True},
        flag=dropdown,
        top_k=slider,
        buttons=checkbox,
        path=fixed(path),
    )
    return widgets.VBox(
        [widgets.HBox(widget_menu.children[:-1]), widget_menu.children[-1]]
    )


def read_files(path: str = "."):
    #adj_matrix = np.array(sparse.load_npz(f"{path}/data/coauthor.npz").todense())
    adj_matrix = sparse.load_npz(f"{path}/data/coauthor.npz")

    with open(f"{path}/data/path.np", "rb") as w:
        country, uni, author = np.load(w).T.tolist()

    return adj_matrix, country, uni, author


def generate_graph(flag, top_k, buttons, path="."):

    adj_matrix, country, uni, author = read_files(path)

    filter_ = [x == flag for x in country]
    f_adj = adj_matrix[filter_][:, filter_]
    f_uni = np.array(uni)[filter_]

    top_k_uni = {k: uni.count(k) for k in set(f_uni)}
    top_k_uni = sorted(top_k_uni.items(), key=lambda item: item[1], reverse=True)
    top_k_uni = [x[0] for x in top_k_uni]
    top_k_uni = top_k_uni[:top_k]

    filter_ = [x in top_k_uni for x in uni]

    f_adj = adj_matrix[filter_][:, filter_]
    f_author = np.array(author)[filter_]
    f_uni = np.array(uni)[filter_]

    # print stats
    global_w_deg = adj_matrix[~np.eye(adj_matrix.shape[0], dtype=bool)].reshape(
        adj_matrix.shape[0], -1
    )

    # avoid memory issues with binder
    del adj_matrix
    gc.collect()

    global_w_deg = global_w_deg[filter_]
    global_deg = np.zeros_like(global_w_deg)
    global_deg[global_w_deg.nonzero()] = 1
    global_deg = global_deg.sum(axis=1)
    with np.errstate(divide='ignore', invalid='ignore'):
        global_w_deg = np.nan_to_num(global_w_deg.sum(axis=1) / (global_w_deg != 0).sum(axis=1))

    print(f"All collaborations ({len(global_deg)} researchers)")
    print(f"Avg. collaborators per researcher: {global_deg.mean():.1f} ± {global_deg.std():.1f}")
    print(
        f"Avg. collaborations per researcher: {global_w_deg.mean():.1f} ± {global_w_deg.std():.1f}\n"
    )

    global_w_deg = f_adj[~np.eye(f_adj.shape[0], dtype=bool)].reshape(
        f_adj.shape[0], -1
    )
    global_deg = np.zeros_like(global_w_deg)
    global_deg[global_w_deg.nonzero()] = 1
    global_deg = global_deg.sum(axis=1)
    with np.errstate(divide='ignore', invalid='ignore'):
        global_w_deg = np.nan_to_num(global_w_deg.sum(axis=1) / (global_w_deg != 0).sum(axis=1))

    print("Collaborations contained within the graph")
    print(f"Avg. collaborators per researcher: {global_deg.mean():.1f} ± {global_deg.std():.1f}")
    print(
        f"Avg. collaborations per researcher: {global_w_deg.mean():.1f} ± {global_w_deg.std():.1f}\n"
    )

    graph = net.Network(height='550px',
                        width='100%',
                        notebook=True,
                        neighborhood_highlight=True)

    size_ = lambda x: 50 * f_adj[:, x].sum() / f_adj.sum(axis=0).max()

    f_adj = np.array(f_adj.todense())
    for i in range(len(f_adj)):
        group = list(set(f_uni)).index(f_uni[i])
        graph.add_node(
            i + 1,
            size=size_(i),
            title=f"{f_author[i]} ({f_uni[i]}): {f_adj[:, i].sum()} collabs",
            group=group,
        )

    for i, adj_i in enumerate(f_adj):
        for j, ij in enumerate(adj_i[i:], start=i):
            if ij:
                graph.add_edge(i + 1, j + 1, value=ij / f_adj.max(), title=f"Collabs: {ij}")

    # Add Legend Nodes
    step = 100
    x = -2000
    y = -800

    legend_group = list(set(f_uni))
    legend_idx = list(range(len(f_adj)+1, len(f_adj) + len(legend_group)+1))
    for i, idx in enumerate(legend_idx):
        graph.add_node(
            idx,
            size=60,
            group=i,
            shape="box",
            x=x,
            y=f"{y + i*step}px",
            label=legend_group[i],
            fixed=True,
            font={"size": 30, "align": "left"},
            widthConstraint=250,
        )
        for j in [j + 1 for j in range(len(f_uni)) if f_uni[j] == legend_group[i]]:
            graph.add_edge(idx, j, value=0, hidden=True, physics=False)

    if buttons:
        graph.show_buttons(filter_=["physics"])
        # graph.show_buttons(filter_=['nodes'])

    if os.path.exists("graph.html"):
        os.remove("graph.html")

    clear_output()
    display(graph.show("graph.html"))
