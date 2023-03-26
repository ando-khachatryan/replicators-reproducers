from sim.callbacks import TypedCellInfo

import jsonpickle
from pathlib import Path 
import yaml
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# def plot_single(
#     both_sims, 
#     sims_per_figure: int,
#     low_fidelity_color='firebrick',
#     high_fidelity_color='royalblue'
#     ):
    
#     if len(both_sims) % sims_per_figure != 0:
#         raise ValueError((f"Number of sims ({len(both_sims)}) should be divisibe "
#                           f"by sims_per_figure ({sims_per_figure})"))
#     fig_1 = make_subplots(
#         rows=len(both_sims), 
#         cols=2, 
#         subplot_titles=['Separate populations', 'Both types within a single population'])
#     fig_1.update_layout(hovermode=False)
#     for i in range(len(both_sims)):
#         both = both_sims[i]        
#         cells_lo = np.array(
#             [s.typed_cell_info.get('low-fidelity', sim.TypedCellInfo()).count for s in both])
#         cells_hi = np.array(
#             [s.typed_cell_info.get('high-fidelity', sim.TypedCellInfo()).count for s in both])
#         x = [ri.round_no for ri in both]
#         showlegend = (i == 0)
#         fig_1.add_trace(
#             go.Scattergl(
#                 x=x,
#                 y=cells_hi,
#                 line=dict(color=high_fidelity_color, width=2),
#                 name='high-fidelity',
#                 showlegend=showlegend,
#                 legendgroup="hf-group"
#                 # hoverinfo='skip'
#                 ), 
#             row=i+1, col=2)
#         fig_1.add_trace(
#             go.Scattergl(
#                 x=x,
#                 y=cells_lo,
#                 line=dict(color=low_fidelity_color, width=2),
#                 name='low-fidelity',
#                 showlegend=showlegend,
#                 legendgroup="lf-group"
#                 # hoverinfo='skip'
#                 ), 
#             row=i+1, col=2)

#     return fig_1


def plot_single_and_together(
    low_fidelity_sims, 
    high_fidelity_sims, 
    both_sims, 
    max_rounds_to_show=float('inf'), 
    low_fidelity_color='firebrick',
    high_fidelity_color='royalblue'):
    
    max_rounds_to_show = min(low_fidelity_sims[0][-1].round_no, max_rounds_to_show)

    fig_1 = make_subplots(
        rows=len(low_fidelity_sims), 
        cols=2, 
        subplot_titles=['Separate populations', 'Both types within a single population'])
    fig_1.update_layout(hovermode=False)
    for i in range(len(low_fidelity_sims)):
        low_fidelity = low_fidelity_sims[i]
        high_fidelity = high_fidelity_sims[i]
        both = both_sims[i]
        
        cells_lo = np.array(
            [ri.cell_count for ri in low_fidelity if ri.round_no <= max_rounds_to_show])
        x = [ri.round_no for ri in low_fidelity if ri.round_no <= max_rounds_to_show]
        showlegend = (i == 0)
        fig_1.add_trace(
            go.Scattergl(
                x=x,
                y=cells_lo,
                line=dict(color=low_fidelity_color, width=2),
                # opacity=0.5,
                name='low-fidelity',
                legendgroup="lf-group1",
                showlegend=showlegend,
                # hoverinfo='skip'
                ), 
            row=i+1, col=1)
        cells_hi = np.array(
            [ri.cell_count for ri in high_fidelity if ri.round_no <= max_rounds_to_show])
        fig_1.add_trace(
            go.Scattergl(
                x=x,
                y=cells_hi,
                line=dict(color=high_fidelity_color, width=2),
                # opacity=0.5,
                name='high-fidelity',
                legendgroup="hf-group1",
                showlegend=showlegend
                # hoverinfo='skip'
                ), 
            row=i+1, col=1)
        
        cells_lo = np.array(
            [s.typed_cell_info.get('low-fidelity', TypedCellInfo()).count for s in both if s.round_no < max_rounds_to_show])
        cells_hi = np.array(
            [s.typed_cell_info.get('high-fidelity', TypedCellInfo()).count for s in both if s.round_no < max_rounds_to_show])
        fig_1.add_trace(
            go.Scattergl(
                x=x,
                y=cells_hi,
                line=dict(color=high_fidelity_color, width=2),
                name='high-fidelity',
                showlegend=False,
                legendgroup="hf-group"
                # hoverinfo='skip'
                ), 
            row=i+1, col=2)
        fig_1.add_trace(
            go.Scattergl(
                x=x,
                y=cells_lo,
                line=dict(color=low_fidelity_color, width=2),
                name='low-fidelity',
                showlegend=False,
                legendgroup="lf-group"
                # hoverinfo='skip'
                ), 
            row=i+1, col=2)

    return fig_1

def plot_two(
    sim_1_li, 
    sim_2_li, 
    sim_1_colors,
    sim_2_colors=None,
    max_rounds_to_show=float('inf')):
    
    if sim_2_colors is None:
        sim_2_colors = sim_1_colors
    
    max_rounds_to_show = min(sim_1_li[0][-1].round_no, max_rounds_to_show)
    fig = make_subplots(rows=len(sim_1_li), 
        cols=2, subplot_titles=['Food is flowing', 'Food can accumulate'])

    for sim_li, colors, fig_column, line_dash in zip(
        [sim_1_li, sim_2_li], 
        [sim_1_colors, sim_2_colors], 
        [1, 2], 
        ['dash', None]):

        for i, currsim in enumerate(sim_li):
            cells_lo = np.array(
                [s.typed_cell_info.get('low-fidelity', TypedCellInfo()).count 
                    for s in currsim if s.round_no < max_rounds_to_show])
            cells_hi = np.array(
                [s.typed_cell_info.get('high-fidelity', TypedCellInfo()).count 
                    for s in currsim if s.round_no < max_rounds_to_show])
            x = [ri.round_no for ri in currsim if ri.round_no <= max_rounds_to_show]
            fig.add_trace(
                go.Scattergl(
                    x=x,
                    y=cells_lo,
                    line=dict(color=colors[0], width=2),
                    name='low-fidelity',
                    showlegend=False,
                    hoverinfo='skip'), 
                row=i+1, col=fig_column)
            fig.add_trace(
                go.Scattergl(
                    x=x,
                    y=cells_hi,
                    line=dict(color=colors[1], width=2),
                    name='high-fidelity',
                    showlegend=False,
                    hoverinfo='skip'), 
                row=i+1, col=fig_column)
    return fig


def legend_captions_from_settings(settings: dict):
    captions = {}
    for cell in settings["population"]:
        # if cell["type"] == 'low-fidelity':
        #     caption = 'Lo('
        # elif cell["type"] == 'high-fidelity':
        #     caption = 'Hi('
        # else:
        #     raise ValueError(f'cell["type"] == {cell["type"]} not recognized')
        if cell["type"] not in ['low-fidelity', 'high-fidelity']:
            raise ValueError(f'cell["type"] == {cell["type"]} not recognized')
        caption = 'st={st} bm={bm:.3f} rf={rf:.3f} delta={delta:.3f}'.format(
            st=cell["energy-threshold-for-split"],
            bm=cell["base-metabolism-energy"],
            rf=cell["replication-fidelity"],
            delta=cell["cell-dies-in-round-prob"]
        )
        captions[cell["type"]] = caption    


    return captions    

def plot_folder(job_folder: str, height_per_run: int=200, save_figures=False):

    lf_results, hf_results, together_results = [], [], []
    for (subfolder, res_li) in [
        ('low-fidelity', lf_results),
        ('high-fidelity', hf_results),
        ('together', together_results)
    ]:
        with open(Path(job_folder, subfolder, 'sim.yaml')) as f:
            settings = yaml.load(f, Loader=yaml.Loader)

        for rundir in (Path(job_folder) / subfolder).iterdir():
            if not rundir.is_dir():
                continue
            with open(rundir / 'results.json', 'r') as f:
                s = f.read()
                res = jsonpickle.loads(s)
                res_li.append(res)

    fig = plot_single_and_together(low_fidelity_sims=lf_results, high_fidelity_sims=hf_results, both_sims=together_results)
    captions = legend_captions_from_settings(settings)
    for d in fig.data:
        d['name'] = d['name'] + ': ' + captions[d['name']]
    fig.update_layout({
        'height': height_per_run*settings["simulation"]["number-of-runs"],
        'legend': {
            'y': 1.06,
            'x': 0.1, 
            'font':{
                'size': 18
            }
        }
    })
    # print(captions)
    if save_figures:
        import os
        savepath = os.path.join(job_folder, 'figures', ' '.join([f'{key}--{captions[key]}' for key in captions]) + '.png')
        Path(savepath).parent.mkdir(parents=True, exist_ok=True)
        fig.write_image(savepath, scale=1.0)
    return fig, captions


