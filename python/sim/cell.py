
# from ctypes import Union
from dataclasses import dataclass
from functools import total_ordering
from multiprocessing.sharedctypes import Value
from typing import List, Union, Dict
import numpy as np


class Environment:
    def __init__(self, resource_regen_rate, regen_prob):
        self.resource_regen_rate = resource_regen_rate
        self.regen_prob = regen_prob
        self.energy = self.resource_regen_rate
        
    def regen(self):
        if np.random.random() < self.regen_prob:
            self.energy += self.resource_regen_rate


class FoodFlowEnvironment:
    def __init__(self, resource_regen_rate, regen_prob=1):
        self.resource_regen_rate = resource_regen_rate
        self.regen_prob = regen_prob
        self.energy = self.resource_regen_rate

    def regen(self):
        # We "reset" the energy from previous state
        if np.random.random() < self.regen_prob:
            self.energy = self.resource_regen_rate


class Cell:
    def __init__(
        self, 
        initial_energy: float, 
        energy_threshold_for_split: float, 
        base_metabolism_energy: float, 
        single_period_energy_accu: float, 
        replication_fidelity: float,
        type: str,
        cell_dies_in_round_prob,
        energy_distribution_on_split: str,
        *, 
        kill_both_on_bad_replication: bool=True, 
        proofreading_energy=0
        ):
        if proofreading_energy >= energy_threshold_for_split/2:
            raise ValueError(f"proofreading energy == {proofreading_energy} should be less than 1/2 of energy_threshold_for_split == {energy_threshold_for_split}")
        edos_values = ['random::uniform', 'equal']
        if energy_distribution_on_split not in edos_values:
            raise ValueError(f"energy_distribution_on_split must be one of {edos_values}, but was {energy_distribution_on_split}")
        self.energy_bank = initial_energy
        self.energy_threshold_for_split = energy_threshold_for_split
        self.base_metabolism_energy = base_metabolism_energy
        self.single_period_energy_accu = single_period_energy_accu
        self.replication_fidelity = replication_fidelity
        # self.life_duration = life_duration
        self.cell_dies_in_round_prob = cell_dies_in_round_prob
        self.energy_distribution_on_split = energy_distribution_on_split
        self.type = type
        self.kill_both_on_bad_replication = kill_both_on_bad_replication
        self.proofreading_energy = proofreading_energy
        self.live_count = 0
        self.is_alive = True

  
    def feed(self, env: Environment):
        if not self.is_alive:
            return
        if env.energy >= self.single_period_energy_accu:
            env.energy -= self.single_period_energy_accu
            self.energy_bank += self.single_period_energy_accu
        # if env.energy >= self.base_metabolism_energy:
        #     env.energy -= self.base_metabolism_energy
        #     self.energy_bank += self.base_metabolism_energy

    def metabolise(self):
        if self.energy_bank >= self.base_metabolism_energy:
            self.energy_bank -= self.base_metabolism_energy
        else:
            self.is_alive = False
    
    # def feed_extra(self, env: Environment):
    #     if not self.is_alive:
    #         return
    #     if self.energy_bank >= self.energy_threshold_for_split:
    #         return
    #     if env.energy >= self.single_period_energy_accu:
    #         take = min(self.single_period_energy_accu, self.energy_threshold_for_split - self.energy_bank)
    #         env.energy -= take
    #         self.energy_bank += take
            
    def split(self):
        if not self.is_alive:
            return
        if self.energy_bank >= self.energy_threshold_for_split:
            if self.energy_distribution_on_split == 'equal':
                rem = self.energy_bank - self.proofreading_energy
                my_newbank = rem/2
                daughter_newbank = rem - my_newbank
            elif self.energy_distribution_on_split == 'random::uniform':
                rem = self.energy_bank - self.proofreading_energy
                my_newbank = rem * np.random.uniform()
                daughter_newbank = rem - my_newbank
            else:
                raise ValueError(f"self.energy_distribution_on_split = {self.energy_distribution_on_split} not supported")
            self.energy_bank = my_newbank
            if np.random.random() < self.replication_fidelity:                
                return Cell(
                    initial_energy = daughter_newbank,
                    energy_threshold_for_split = self.energy_threshold_for_split,
                    base_metabolism_energy = self.base_metabolism_energy,
                    single_period_energy_accu = self.single_period_energy_accu,
                    replication_fidelity=self.replication_fidelity,
                    type = self.type,
                    energy_distribution_on_split = self.energy_distribution_on_split,
                    cell_dies_in_round_prob = self.cell_dies_in_round_prob,
                    kill_both_on_bad_replication=self.kill_both_on_bad_replication
                )
            else:
                if self.kill_both_on_bad_replication:
                    self.is_alive = False


@dataclass
class Parasite:
    volume: float
    name: str


class CellWithParasites:
    def __init__(self, 
        initial_parasite_counts: Dict[Parasite, float],
        energy_threshold_for_split: float, 
        base_metabolism_energy: float, 
        single_period_energy_accu: float, 
        replication_fidelity: float,
        type: str,
        *, 
        life_duration: float=float('inf'),
        kill_both_on_bad_replication: bool=False, 
        proofreading_energy=0
    ) -> None:

        self.parasite_counts = initial_parasite_counts
        if proofreading_energy >= energy_threshold_for_split/2:
            raise ValueError(f"proofreading energy == {proofreading_energy} should be less than 1/2 of energy_threshold_for_split == {energy_threshold_for_split}")
        self.energy_threshold_for_split = energy_threshold_for_split
        self.base_metabolism_energy = base_metabolism_energy
        self.single_period_energy_accu = single_period_energy_accu
        self.replication_fidelity = replication_fidelity
        self.life_duration = life_duration
        self.type = type
        self.kill_both_on_bad_replication = kill_both_on_bad_replication
        self.proofreading_energy = proofreading_energy
        self.live_count = 0
        self.is_alive = True


    def feed(self, env: Environment):
        if not self.is_alive:
            return
        if self.energy_bank >= self.energy_threshold_for_split:
            return
        take = min(
            [
                self.single_period_energy_accu,
                env.energy,
                self.energy_threshold_for_split - self.total_energy()
            ]
        )
        env.energy -= take
        self._update_energy(take)

    def feed_extra(self, env):
        pass

    def total_energy(self):
        return np.sum([p.volume * count for (p, count) in self.parasite_counts.items()])

    def _update_energy(self, energy):
        total_energy = self.total_energy()
        for ptype in self.parasite_counts:
            self.parasite_counts[ptype] += energy/total_energy
 

    def metabolise(self):
        if self.get_energy() < self.base_metabolism_energy:
            self.is_alive = False
        else:
            self._update_energy(-self.base_metabolism_energy)


    def split(self):
        if not self.is_alive:
            return
        if self.total_energy() >= self.energy_threshold_for_split:
            self._update_energy(-self.proofreading_energy)
            new_counts = {ptype: pcount/2 for (ptype, pcount) in self.parasite_counts.items()}
            self.parasite_counts = new_counts.copy()
            if np.random.random() < self.replication_fidelity:                
                return CellWithParasites(
                    initial_parasite_counts=new_counts.copy(),
                    energy_threshold_for_split=self.energy_threshold_for_split,
                    base_metabolism_energy=self.base_metabolism_energy,
                    single_period_energy_accu=self.single_period_energy_accu,
                    replication_fidelity=self.replication_fidelity,
                    life_duration=self.life_duration,
                    kill_both_on_bad_replication=self.kill_both_on_bad_replication,
                    proofreading_energy=self.proofreading_energy
                )
            else:
                if self.kill_both_on_bad_replication:
                    self.is_alive = False
                return None

