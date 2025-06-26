#!/usr/bin/env python3
"""
Test script for ETCD Python runtime
Run multiple instances of this script to test distributed functionality
"""

import os
import sys

# Add the kvbench runtime path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../kvbench/runtime"))

try:
    from etcd_rt import _EtcdDistUtils

    def test_basic_functionality():
        """Test basic rank and size functionality"""
        print("Testing basic functionality...")

        # Initialize runtime - modify size based on how many processes you're running
        runtime = _EtcdDistUtils(etcd_endpoints="http://localhost:2379", size=2)

        rank = runtime.get_rank()
        world_size = runtime.get_world_size()

        print(f"Rank: {rank}, World Size: {world_size}")

        # Test barrier
        print(f"Rank {rank}: Before barrier")
        runtime.barrier()
        print(f"Rank {rank}: After barrier")

        # Test allgather
        my_data = {"rank": rank, "message": f"Hello from rank {rank}"}
        print(f"Rank {rank}: Gathering data...")

        try:
            all_data = runtime.allgather_obj(my_data)
            print(f"Rank {rank}: Gathered data from all ranks:")
            for i, data in enumerate(all_data):
                print(f"  Rank {i}: {data}")
        except Exception as e:
            print(f"Rank {rank}: Allgather failed: {e}")

        # Test barrier again
        runtime.barrier()
        print(f"Rank {rank}: Test completed successfully!")

    if __name__ == "__main__":
        test_basic_functionality()

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure the etcd_runtime module is built and accessible")
    print("Also ensure the etcd server is running at http://localhost:2379")
    sys.exit(1)
except Exception as e:
    print(f"Runtime error: {e}")
    sys.exit(1)
