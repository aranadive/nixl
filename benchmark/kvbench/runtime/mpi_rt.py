import logging
import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, final

from .rt_base import _RTUtils, ReduceOp

from mpi4py import MPI


class _MPIDistUtils(_RTUtils):
    def get_rank(self) -> int:
        return MPI.COMM_WORLD.Get_rank()

    def get_world_size(self) -> int:
        return MPI.COMM_WORLD.Get_size()

    def allgather_obj(self, obj: Any) -> List[Any]:
        comm = MPI.COMM_WORLD
        return comm.allgather(obj)

    def alltoall_obj(self, send_objs: List[Any]) -> List[Any]:
        world_size = self.get_world_size()
        assert (
            len(send_objs) == world_size
        ), f"Invalid number of objects {len(send_objs)}, expected {world_size}"

        comm = MPI.COMM_WORLD
        return comm.alltoall(send_objs)
    
    def barrier(self, ranks: Optional[List[int]] = None):
        """Barrier for a group of ranks

        Args:
            ranks: List of ranks to barrier, if None, barrier for all ranks
        """
        if ranks is None:
            MPI.COMM_WORLD.Barrier()
            return
            
        if self.get_rank() not in ranks:
            return
            
        key = tuple(sorted(ranks))
        group = self.groups.get(key)
        if group is None:
            raise ValueError(
                f"[Rank {self.get_rank()}] Group with ranks {ranks} was not created"
            )
            
        group.Barrier()
    
    def all_reduce(self, vals: List[float | int], op: ReduceOp) -> List[float | int]:
        """All-reduce operation on a list of values

        Args:
            vals: List of values to reduce
            op: Reduction operation to perform

        Returns:
            List[float | int]: List of reduced values
        """
        if op == ReduceOp.SUM:
            mpi_op = MPI.SUM
        elif op == ReduceOp.MIN:
            mpi_op = MPI.MIN
        elif op == ReduceOp.MAX:
            mpi_op = MPI.MAX
        elif op == ReduceOp.AVG:
            # MPI doesn't have a native average operation
            # We'll implement it as sum and then divide by world size
            mpi_op = MPI.SUM
        
        result = MPI.COMM_WORLD.allreduce(vals, op=mpi_op)
        
        # If operation is average, divide by world size
        if op == ReduceOp.AVG:
            world_size = self.get_world_size()
            result = [val / world_size for val in result]
            
        return result
    
    def init_group(self, ranks: List[int]):
        """Initialize a group of ranks

        Args:
            ranks: List of ranks to initialize a group for
        """
        if not ranks:
            return None
            
        key = tuple(sorted(ranks))
        if key not in self.groups:
            group = MPI.COMM_WORLD.Get_group()
            new_group = group.Incl(ranks)
            self.groups[key] = MPI.COMM_WORLD.Create_group(new_group)
            
        return key
