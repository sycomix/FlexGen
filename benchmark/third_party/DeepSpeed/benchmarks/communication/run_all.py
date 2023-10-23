from benchmarks.communication.utils import *
from benchmarks.communication.all_reduce import run_all_reduce
from benchmarks.communication.all_gather import run_all_gather
from benchmarks.communication.all_to_all import run_all_to_all
from benchmarks.communication.pt2pt import run_pt2pt
from benchmarks.communication.broadcast import run_broadcast
from benchmarks.communication.constants import *


# For importing
def main(args, rank):

    init_processes(local_rank=rank, args=args)

    ops_to_run = []
    if args.all_reduce:
        ops_to_run.append('all_reduce')
    if args.all_gather:
        ops_to_run.append('all_gather')
    if args.broadcast:
        ops_to_run.append('broadcast')
    if args.pt2pt:
        ops_to_run.append('pt2pt')
    if args.all_to_all:
        ops_to_run.append('all_to_all')

    if not ops_to_run:
        ops_to_run = ['all_reduce', 'all_gather', 'all_to_all', 'broadcast', 'pt2pt']

    for comm_op in ops_to_run:
        if comm_op == 'all_gather':
            run_all_gather(local_rank=rank, args=args)
        elif comm_op == 'all_reduce':
            run_all_reduce(local_rank=rank, args=args)
        elif comm_op == 'all_to_all':
            run_all_to_all(local_rank=rank, args=args)
        elif comm_op == 'broadcast':
            run_broadcast(local_rank=rank, args=args)
        elif comm_op == 'pt2pt':
            run_pt2pt(local_rank=rank, args=args)


# For directly calling benchmark
if __name__ == "__main__":
    args = benchmark_parser().parse_args()
    rank = args.local_rank
    main(args, rank)
