from dataclasses import dataclass, field
from collections import defaultdict
from decimal import ROUND_DOWN
from typing import List, Dict
import ray

from sim.cell import CellWithParasites
# from .cell import Cell

@dataclass 
class TypedCellInfo:
    # energy_distribution     : List[float] = field(default_factory=list)
    count                   : int = 0
    avg_energy              : float = 0
    newborn_count           : int = 0
    # dead_count              : int = 0


@dataclass 
class RoundInfo:
    round_no                : int
    avg_cell_energy         : float 
    env_energy              : float
    cell_count              : int
    total_newborn_count     : int
    typed_cell_info         : Dict[str, TypedCellInfo]
   


def default_stats_collector(
    env, 
    population: List, 
    round_no, 
    gather_each=1):
    if round_no % gather_each != 0:
        return
    
    tci: Dict[str, TypedCellInfo] = {}
    for cell in population:
        if not cell.is_alive:
            continue        
        if cell.type not in tci:
            tci[cell.type] = TypedCellInfo()
        info: TypedCellInfo = tci[cell.type]
        info.count += 1
        # info.energy_distribution.append(cell.energy_bank)
        info.avg_energy += cell.energy_bank
        if cell.live_count == 0:
            info.newborn_count += 1
    
    for celltype in tci:
        tci[celltype].avg_energy = tci[celltype].avg_energy/tci[celltype].count

    cell_count = sum([ci.count for ci in tci.values()])
    if cell_count > 0:
        avg_cell_energy = sum([(ci.avg_energy * ci.count) for ci in tci.values()])/cell_count
    else:
        avg_cell_energy = 0
        
    return RoundInfo(
            round_no=round_no,
            avg_cell_energy=avg_cell_energy,
            env_energy=env.energy, 
            cell_count=cell_count,
            total_newborn_count=sum([ci.newborn_count for ci in tci.values()]),
            typed_cell_info=tci
        )


def parasite_stats_collector(
    env, 
    population: List[CellWithParasites], 
    round_no: int, 
    gather_each: int=1):

    stats = []
    if round_no % gather_each != 0:
        return
    for cell in population:
        stats.append(cell.parasite_counts.copy())
    
    return {
        'round_no': round_no,
        'parasites': stats
    }

    # tci: Dict[str, TypedCellInfo] = {}
    # for cell in population:
    #     if cell.type not in tci:
    #         tci[cell.type] = TypedCellInfo()
    #     info: TypedCellInfo = tci[cell.type]
    #     info.count += 1
    #     info.energy_distribution.append(cell.energy_bank)
    #     info.avg_energy += cell.energy_bank
    #     if cell.live_count == 0:
    #         info.newborn_count += 1
    
    # for celltype in tci:
    #     tci[celltype].avg_energy = tci[celltype].avg_energy/tci[celltype].count

    # return RoundInfo(
    #         round_no=round_no,
    #         avg_cell_energy=sum([(ci.avg_energy * ci.count) for ci in tci.values()]),
    #         env_energy=env.energy, 
    #         cell_count=len(population),
    #         total_newborn_count=sum([ci.newborn_count for ci in tci.values()]),
    #         typed_cell_info=tci
    #     )


# def default_stats_collector(stats_li, gather_each=1):
#     if isinstance(stats_li, ray.ObjectRef):
#         stats_li = ray.get(stats_li)

#     def default_stats_collector_callback(env, population, round_no):
#         if round_no % gather_each != 0:
#             return
        
#         tci: Dict[str, TypedCellInfo] = {}
#         for cell in population:
#             if cell.type not in tci:
#                 tci[cell.type] = TypedCellInfo()
#             info: TypedCellInfo = tci[cell.type]
#             info.count += 1
#             info.energy_distribution.append(cell.energy_bank)
#             info.avg_energy += cell.energy_bank
#             if cell.live_count == 0:
#                 info.newborn_count += 1
        
#         for celltype in tci:
#             tci[celltype].avg_energy = tci[celltype].avg_energy/tci[celltype].count
#         stats_li.append(
#             RoundInfo(
#                 round_no=round_no,
#                 avg_cell_energy=sum([(ci.avg_energy * ci.count) for ci in tci.values()]),
#                 env_energy=env.energy, 
#                 cell_count=len(population),
#                 total_newborn_count=sum([ci.newborn_count for ci in tci.values()]),
#                 typed_cell_info=tci
#             )
#         )
     
#     return default_stats_collector_callback   