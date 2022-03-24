# prometheus
import prometheus_client

# system metrics with python
from linux_metrics import cpu_stat
from prometheus_client import Counter, Gauge

# metrics initialization
graphs = {
    'c': Counter('model_request_operations_total', 'numero total de peticiones al modelo procesadas'),
    't': Counter('test_request_operations_total', 'numero total de peticiones de testing'),
    'T': Counter('model_training_operations_total', 'numero total de entrenamientos procesados'),
    'g': Gauge('cpu_usage', 'The amount of cpu used.')
}


def increment_model_counter():
    graphs['c'].inc()


def increment_test_counter():
    graphs['t'].inc()


def increment_train_counter():
    graphs['T'].inc()


def get_metrics():
    return [prometheus_client.generate_latest(metrica) for metrica in graphs.values()]


def compute_system_metrics():
    # print 'cpu utilization: %.2f%%' % (100 - cpu_pcts['idle'])
    cpu_pcts = cpu_stat.cpu_percents(0.1)
    # cpu_usage = '%.2f%%' % (100 - cpu_pcts['idle'])
    cpu_usage = (100 - cpu_pcts['idle'])
    graphs['g'].set(cpu_usage)
    # return cpu_usage

# python linux_metrics API
# * linux_metrics
#   * cpu_stat
#     * cpu_times()
#     * cpu_percents(sample_duration=1)
#     * procs_running()
#     * procs_blocked()
#     * load_avg()
#     * cpu_info()
#   * disk_stat
#     * disk_busy(device, sample_duration=1)
#     * disk_reads_writes(device)
#     * disk_usage(path)
#     * disk_reads_writes_persec(device, sample_duration=1)
#   * mem_stat
#     * mem_stats()
#   * net_stat
#     * rx_tx_bytes(interface)
#     * rx_tx_bits(interface)
#     * rx_tx_dump(interface)
