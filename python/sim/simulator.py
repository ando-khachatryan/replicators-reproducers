# try:
#     from .cell import Cell, Environment, FoodFlowEnvironment
# except:
#     from cell import Cell, Environment, FoodFlowEnvironment

# try:
#     from .callbacks import default_stats_collector, parasite_stats_collector
# except:
#     from callbacks import default_stats_collector, parasite_stats_collector
from .cell import Cell, Environment, FoodFlowEnvironment
from .callbacks import default_stats_collector, parasite_stats_collector
# except:
#     from cell import Cell, Environment, FoodFlowEnvironment


# except:
#     from callbacks import default_stats_collector, parasite_stats_collector


import plot_helpers as ph

import numpy as np
from typing import Callable, List, Dict, Tuple, Union
from dataclasses import dataclass
import ray
import logging
import yaml
import time
from pathlib import Path
import copy
import jsonpickle
from pprint import pformat, pprint
import os



def ray_check_init():
    if not ray.is_initialized:
        ray.init(num_cpus=6)

ray_check_init()

def shuffle(n):
    indices = np.arange(n)
    np.random.shuffle(indices)
    return indices


@ray.remote
def run_sim(
    sim_id: int, 
    env: Union[Environment, FoodFlowEnvironment], 
    population: List[Cell], 
    number_of_rounds: int,
    # cell_finds_food_prob: float,
    stop_when_one_type_wins: bool,
    print_progress:float=0.0,
    gather_stats_every: int=10):

    initial_celltype_count = len(set([cell.type for cell in population]))
    stats = []
    for ri in range(1, number_of_rounds + 1):
        # print(f'sim_id: {sim_id}, env.regen() called')
        env.regen()
        population = [cell for cell in population if cell.is_alive]
        
        indices = shuffle(len(population))
        for celli in indices:
            # if ri == 0 and celli == 0:
            #     pprint(cell.__dict__)
            cell = population[celli]
            if np.random.random() < cell.cell_dies_in_round_prob:
                cell.is_alive = False
                continue
            cell.metabolise()           
            # if np.random.random() < cell_finds_food_prob:
            cell.feed(env)
            # cell.feed_extra(env)
            newcell = cell.split()
            if newcell:
                # this is ok because we are adding to the end of the list
                population.append(newcell)
        if stop_when_one_type_wins:
            cell_type_count = len(set([cell.type for cell in population]))
            if (cell_type_count == 1) and (initial_celltype_count) > 1:
                stats.append(default_stats_collector(
                    env=env, 
                    population=population,
                    round_no=ri
                ))
                break 

        if (ri == 1) or ri % gather_stats_every == 0:
            stats.append(default_stats_collector(
                env=env, 
                population=population,
                round_no=ri
            ))

        if print_progress and ((ri % int(number_of_rounds * print_progress) == 0) or (ri == number_of_rounds)):
            print(f'sim: {sim_id} {ri}/{number_of_rounds}')


    return sim_id, stats



def run_multiple_sims(sim_param_li: List):
    # , sim_type: Union[str, List[str]]):
    funcs = [
        run_sim.remote(**({'sim_id': i} | sim_params))
         for i, sim_params in enumerate(sim_param_li)]
    results = ray.get(funcs)
    results = [t[1] for t in sorted(results, key=lambda t: t[0])]
    return results


def get_timestamp():
    return time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())


def run_from_folder(folder):
    with open(Path(folder, 'sim.yaml')) as f:
        settings = yaml.load(f, Loader=yaml.Loader)
    if settings['env']['type'] == 'accumulate':
        env = Environment(
            resource_regen_rate=settings['env']['regen-rate'],
            regen_prob=settings['env']['regen-probability']
        )
    elif settings['env']['type'] == 'flow':
        env = FoodFlowEnvironment(
            resource_regen_rate=settings['env']['regen-rate'],
            regen_prob=settings['env']['regen-probability']
        )
    else:
        raise ValueError(f'Environment type not recognized: {settings["env"]["type"]}')

    population = []
    for cs in settings['population']:
        cell_params = {key.replace('-', '_'): cs[key] for key in cs}
        population += [
            Cell(**cell_params) for _ in range(settings['simulation']['initial-cell-count'])
        ]

    # sim.run_sim()
    # for cell in settings['cells']:
    ss = {
        key.replace('-', '_'): value for key, value in settings['simulation'].items()
    }
    del ss['number_of_runs']
    del ss['initial_cell_count']
    sim_param_li = [
        ss | {
            'env': copy.deepcopy(env), 
            'population': population.copy()
            } 
            for _ in range(settings['simulation']['number-of-runs'])]
    results = run_multiple_sims(sim_param_li)
    for sim_id, sim_results in enumerate(results):
        run_folder = Path(folder, f'run={sim_id}')
        run_folder.mkdir(parents=True, exist_ok=True)
        with open(run_folder / 'results.json', 'w') as f:
            # f.write(json.dumps(sim_results))
            f.write(jsonpickle.encode(sim_results))
        

# @ray.remote
# def run_sim_parasites(
#     sim_id: int, 
#     env: Environment, 
#     population: List[Cell], 
#     n_rounds: int,
#     stats_collector,
#     cell_finds_food_prob: float=1.0,
#     gather_stats_every: int=10, 
#     ):

#     stats = []
#     for ri in range(n_rounds):
#         env.regen()
#         for cell in population:
#             cell.live_count += 1
#             if cell.live_count >= cell.life_duration:
#                 cell.is_alive = False
                
#         population = [cell for cell in population if cell.is_alive]
#         indices = shuffle(len(population))
#         for celli in indices:
#             cell = population[celli] 
#             if np.random.random() < cell.cell_dies_in_round_prob:
#                 cell.is_alive = False
#                 continue
#             cell.metabolise()           
#             if np.random.random() < cell_finds_food_prob:
#                 cell.feed(env)
#                 cell.feed_extra(env)
#                 newcell = cell.split()
#                 if newcell:
#                     # this is ok because we are adding to the end of the list
#                     population.append(newcell)
#         # if ri < 100:
#         #     print(f'ri: {ri}, len(population): {len(population)}')
#         if ri % gather_stats_every == 0:
#             stats.append(stats_collector(
#                 env=env, 
#                 population=population,
#                 round_no=ri
#             ))
#     return sim_id, stats
#         # if callbacks:
#         #     for func in callbacks:
#         #         func(env, population, ri)

# def run_multiple_parasite_sims(sim_param_li: List):
#     funcs = [
#         run_sim.remote(**(
#             {
#                 'sim_id': i,
#                 'stats_collector':parasite_stats_collector
#             } | sim_params))
#          for i, sim_params in enumerate(sim_param_li)]
#     results = ray.get(funcs)
#     results = [t[1] for t in sorted(results, key=lambda t: t[0])]
#     return results


def run_grid_sim(
    job_prefix: str, 
    settings: dict,
    cell_params: dict,
    pbar: any,
    bm_range: np.ndarray,
    rf_range: np.ndarray,
    st_range: np.ndarray=None,
    run_together_only=False,
    create_figure_for_each_run=False
    ):
    # print(f'Inside run_grid_sim, create_figure_for_each_run: {create_figure_for_each_run}')
    for bmi in range(len(bm_range) - 1):
        for rfj in range(len(rf_range) - 1):
            lf_cell = cell_params | {
                "type": "low-fidelity",
                "base-metabolism-energy": float(bm_range[bmi]),
                "replication-fidelity": float(rf_range[rfj]),
            }
            hf_cell = cell_params | {
                "type": "high-fidelity",
                "base-metabolism-energy": float(bm_range[bmi + 1]),
                "replication-fidelity": float(rf_range[rfj + 1]),
            }
            if st_range is not None:
                lf_cell["energy-threshold-for-split"] = float(st_range[bmi])
                hf_cell["energy-threshold-for-split"] = float(st_range[bmi+1])

            if st_range is not None:
                this_folder = ( f'bm-low = {bm_range[bmi]:.3f} '
                                f'rf-low = {rf_range[rfj]:.3f} '
                                f'st-low = {st_range[bmi]:.3f} '
                                f'bm-hi  = {bm_range[bmi+1]:.3f} '
                                f'rf-hi = {rf_range[rfj+1]:.3f}'
                                f'st-hi = {st_range[bmi+1]:.3f}'
                              )
            else:
                this_folder = ( f'bm-low = {bm_range[bmi]:.4f} '
                                f'rf-low = {rf_range[rfj]:.4f} '
                                f'bm-hi  = {bm_range[bmi+1]:.4f} '
                                f'rf-hi = {rf_range[rfj+1]:.4f}'
                              )

            job_folder = os.path.join(
                job_prefix, 
                this_folder)

            if run_together_only:
                subfolders = ['together']
                populations = [[lf_cell, hf_cell]]
            else:
                subfolders = [
                    'low-fidelity', 
                    'high-fidelity',  
                    'together'
                ]
                populations = [
                    [lf_cell],
                    [hf_cell],
                    [lf_cell, hf_cell]
                ]

            for subfolder, population in zip(subfolders, populations):
                folder = os.path.join(job_folder, subfolder)
                Path(folder).mkdir(parents=True, exist_ok=True)
                # print(f'folder: {folder}')
                settings["population"] = population
                with open(os.path.join(folder, 'sim.yaml'), 'w') as f:
                    yaml.dump(settings, f, 
                        sort_keys=False, 
                        default_style=None, 
                        default_flow_style=False)
            for subfolder in subfolders:
                run_from_folder(os.path.join(job_folder, subfolder))
            pbar.update(1)
            # time.sleep(0.01)
            if create_figure_for_each_run:
                ph.plot_folder(job_folder, save_figures=True, height_per_run=200)


def run_one_vs_grid(
    job_prefix: str, 
    settings: dict,
    base_cell_params: dict,
    pbar: any,
    bm_range: np.ndarray,
    rf_range: np.ndarray,
    # st_range: np.ndarray=None,
    run_together_only=False,
    create_figure_for_each_run=False
    ):
    for bmi in range(len(bm_range) ):
        for rfj in range(len(rf_range)):
            hf_cell = base_cell_params | {
                "type": "high-fidelity",
                "base-metabolism-energy": float(bm_range[bmi]),
                "replication-fidelity": float(rf_range[rfj]),
            }
            this_folder = '(bm={bm0:.4f}, rf={rf0:.4f}) vs (bm={bm1:.4f}, rf={rf1:.4f})'.format(
                bm0 = base_cell_params["base-metabolism-energy"],
                rf0 = base_cell_params["replication-fidelity"],
                bm1 = bm_range[bmi],
                rf1 = rf_range[rfj]
            )

            job_folder = os.path.join(
                job_prefix, 
                this_folder)

            if run_together_only:
                subfolders = ['together']
                populations = [[base_cell_params, hf_cell]]
            else:
                subfolders = [
                    'low-fidelity', 
                    'high-fidelity',  
                    'together'
                ]
                populations = [
                    [base_cell_params],
                    [hf_cell],
                    [base_cell_params, hf_cell]
                ]

            for subfolder, population in zip(subfolders, populations):
                folder = os.path.join(job_folder, subfolder)
                Path(folder).mkdir(parents=True, exist_ok=True)
                # print(f'folder: {folder}')
                settings["population"] = population
                with open(os.path.join(folder, 'sim.yaml'), 'w') as f:
                    yaml.dump(settings, f, 
                        sort_keys=False, 
                        default_style=None, 
                        default_flow_style=False)
            for subfolder in subfolders:
                run_from_folder(os.path.join(job_folder, subfolder))
            pbar.update(1)
            # time.sleep(0.01)
            if create_figure_for_each_run:
                ph.plot_folder(job_folder, save_figures=True, height_per_run=200)