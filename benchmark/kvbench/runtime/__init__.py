from .etcd_rt import _EtcdDistUtils
import os

# Initialize with default parameters, can be overridden by environment variables
etcd_endpoints = os.environ.get('ETCD_ENDPOINTS', 'http://localhost:2379')
world_size = int(os.environ.get('WORLD_SIZE', '1'))

dist_rt = _EtcdDistUtils(etcd_endpoints=etcd_endpoints, size=world_size)
dist_rt.init_dist()
