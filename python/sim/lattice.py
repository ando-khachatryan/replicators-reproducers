from xml.dom import NotSupportedErr
from .cell import Cell, Environment, FoodFlowEnvironment
import numpy as np
from typing import List, Dict, Tuple


def _calc_neighborhood(row, col, lattice_size):
    neighbors = []
    for r in [-1, 0, 1]:
        for c in [-1, 0, 1]:
            if (r == 0) and (c == 0):
                continue
            nei_row = row + nei_row
            nei_col = col + nei_col
            if (nei_row >= 0 and nei_row < lattice_size) and (nei_col >= 0 and nei_col < lattice_size):
                neighbors.append((nei_row, nei_col))
    return neighbors


class LatticeWorld:

    def __init__(self, lattice_size: int, is_thoroid: False) -> None:
        self.lattice = np.empty((lattice_size, lattice_size))
        self.lattice_size = lattice_size
        self.is_thoroid = is_thoroid
        if is_thoroid: 
            raise NotSupportedErr('Thoroid lattice not supported')
        self.neighbors = {}
        for row in range(self.lattice_size):
            for col in range(self.lattice_size):
                self.neighbors[(row, col)] = _calc_neighborhood(row, col, self.lattice_size)

    def __getitem__(self, row_and_col: Tuple[int, int]) -> Cell:
        row, col = row_and_col
        return self.lattice[row, col]

    def __setitem__(self, key: Tuple[int, int], newvalue: Cell):
        assert not self.lattice[key].is_alive()
        self.lattice[key] = newvalue


def run_round(
    world: LatticeWorld, 
    env: FoodFlowEnvironment, 
    randomize_neighborhood: bool = True) -> LatticeWorld:
    
    env.regen()
    live_indices = world.live_cell_coordinates()
    live_indices = np.random.shuffle(live_indices)

    for row, col in live_indices:
        cell = world[row, col]
        cell.metabolise()
        cell.feed(env)
        cell.feed_extra(env)
        if cell.energy_bank >= cell.energy_threshold_for_split:
            neighbor_coords = world.neighbors[(row, col)]
            if randomize_neighborhood:
                neighbor_coords = np.random.shuffle(neighbor_coords)

            for nei_row, nei_col in neighbor_coords:
                if not world[nei_row, nei_col].is_alive():
                    # Empty space found, add the new cell here.
                    newcell = cell.split()
                    assert newcell is not None
                    world[nei_row, nei_col] = newcell
                    break


def run_sim(n_rounds, lattice_size: int, initial_cells: List[Cell], initial_cell_coords: List[Tuple[int, int]]):
    world = LatticeWorld(lattice_size=lattice_size)
    for i, (row, col) in enumerate(initial_cell_coords):
        world[row, col] = initial_cells[i]

    for round in range(n_rounds):
        grid = run_round(grid)
        
