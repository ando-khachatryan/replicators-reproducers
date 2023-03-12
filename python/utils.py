from multiprocessing.sharedctypes import Value
import yaml
from pathlib import Path
import jsonpickle
import dataclasses
from typing import List, Dict

def read_settings(folder):
    with open(Path(folder, 'sim.yaml')) as f:
        settings = yaml.load(f, Loader=yaml.Loader)
    return settings


def grid_simulations_rows(parent_folder: str, *, last_round_only:bool=True) -> List[Dict[str, any]]:
    # p = Path(parent_folder)
    rows = []
    for sim_folder in Path(parent_folder).iterdir():
        if not sim_folder.is_dir():
            continue
        settings = read_settings(Path(sim_folder) / 'together')
        for subfolder in ['low-fidelity', 'high-fidelity', 'together']:
            low_bm, low_rf = None, None
            hi_bm, hi_rf = None, None

            for cell in settings["population"]:
                if cell["type"] == 'low-fidelity':
                    low_bm = cell["base-metabolism-energy"]
                    low_rf = cell["replication-fidelity"]
                elif cell["type"] == 'high-fidelity':
                    hi_bm = cell["base-metabolism-energy"]
                    hi_rf = cell["replication-fidelity"]
                else:
                    raise ValueError(f'Cell type {cell["type"]} not recognized')

            this_folder = Path(sim_folder) / subfolder
            if not Path(this_folder).is_dir():
                continue
            for run_num, run_folder in enumerate(this_folder.iterdir()):
                if not run_folder.is_dir():
                    continue
                with open(run_folder / 'results.json', 'r') as f:
                    s = f.read()
                    res = jsonpickle.loads(s)
                    
                    # if subfolder == 'together':
                    #     for ri in res[::-1]:
                    if last_round_only:
                        tci = dataclasses.asdict(res[-1])['typed_cell_info']
                        rows.append({
                                'low-bm': low_bm,
                                'low-rf': low_rf,
                                'hi-bm': hi_bm,
                                'hi-rf': hi_rf, 
                                'run': run_num,
                                'type': subfolder,
                                'low-fidelity': tci.get('low-fidelity', {}).get('count', 0),
                                'high-fidelity': tci.get('high-fidelity', {}).get('count', 0)
                            })
                    else:
                        for ri in res:
                            tci = dataclasses.asdict(ri)['typed_cell_info']
                            rows.append({
                                'low-bm': low_bm,
                                'low-rf': low_rf,
                                'hi-bm': hi_bm,
                                'hi-rf': hi_rf, 
                                'run': run_num,
                                'type': subfolder,
                                'round-no': ri.round_no,
                                'low-fidelity': tci.get('low-fidelity', {}).get('count', 0),
                                'high-fidelity': tci.get('high-fidelity', {}).get('count', 0)
                            })
    return rows            

