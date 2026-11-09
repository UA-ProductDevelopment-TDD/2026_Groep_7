"""Batch experiments (phase 3): the mission repeated over variants and random seeds, compared side by side.

A variant is a set of changes to the current scenario (another leg design, night, another detector, ...). Each
variant runs once per seed; a seed changes the terrain's bumps, the stones and the chickens, so the comparison does
not hang on one lucky layout. Every run is a headless coop session in a worker process (jobs.py): the mission starts
at time 0 and runs for the set number of simulated seconds. The result per variant is the mean and spread of the
metrics over its seeds.
"""
import copy
import csv
import io
import math
import statistics
import time

from coop import config

SEED_SECTIONS = {'terrain': 'seed', 'stones': 'seed', 'chickens': 'seed'}
# The numbers in the comparison table: (key, label, path into the metrics summary or the run record).
COLUMNS = (
    ('distance_m', 'Distance walked (m)', ('distance_m',)),
    ('laps', 'Laps', ('laps',)),
    ('deviation_m', 'Mean route deviation (m)', ('route_deviation_m', 'mean')),
    ('falls', 'Falls', ('falls',)),
    ('coverage_run', 'Fence seen in the whole run', ('coverage', 'run')),
    ('coverage', 'Fence seen per finished lap', ('coverage', 'mean')),
    ('camera_blocked', 'Camera image showing the robot itself', ('camera', 'own_share_mean')),
    ('time_to_alarm_s', 'Time to fox alarm (s)', ('fox', 'time_to_alarm_s')),
    ('alarm_in_view_s', 'Alarm after fox in view (s)', ('fox', 'time_to_alarm_in_view_s')),
    ('false_alarms', 'False alarms', ('alarms', 'false')),
    ('fox_fled', 'Fox chased off', ('fox', 'fled_at')),
    ('docking_rate', 'Docking success', ('docking', 'success_rate')),
    ('docking_lateral_m', 'Docking error beside (m)', ('docking', 'mean_lateral_m')),
    ('energy_wh', 'Energy used (Wh)', ('energy', 'used_wh')),
    ('energy_per_lap_wh', 'Energy per lap (Wh)', ('energy', 'mean_per_lap_wh')),
    ('battery_end', 'Battery at the end', ('battery_end',)),
)


def merge(base, changes):
    """A copy of base with changes put over it; nested objects merge, everything else replaces."""
    result = copy.deepcopy(base)
    for key, value in (changes or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def plan(scenario, variants, seeds, seconds):
    """The runs of an experiment: (label, scenario) per variant and seed, every scenario validated up front."""
    if not isinstance(variants, list) or not 1 <= len(variants) <= 8:
        raise ValueError('An experiment compares 1 to 8 variants')
    seeds = config.number(seeds, 'seeds per variant', 1, 20, integer=True)
    seconds = config.number(seconds, 'mission length', 10, 3600, unit='s')
    runs = []
    for index, variant in enumerate(variants):
        if not isinstance(variant, dict):
            raise ValueError('Every variant is an object with a name and changes')
        name = config.text(variant.get('name') or f'Variant {index + 1}', 'variant name')
        base = merge(scenario, variant.get('changes'))
        try:
            checked = config.validate(base)
        except ValueError as error:
            raise ValueError(f'{name}: {error}') from None
        for seed in range(seeds):
            run = copy.deepcopy(checked)
            for section, key in SEED_SECTIONS.items():
                run[section][key] = (run[section][key] + seed * 7919) % (2 ** 31 - 1)  # a prime step: unrelated layouts
            runs.append({'variant': name, 'seed': seed, 'scenario': run})
    if len(runs) > 120:
        raise ValueError('At most 120 runs per experiment: use fewer variants or seeds')
    return runs, seconds


def run_mission(scenario, seconds, variant='', seed=0):
    """One headless mission (runs in a worker process). Returns the metrics summary and a few extra numbers."""
    from coop.session import CoopSession  # imported in the worker: the parent never builds a world for this
    started = time.perf_counter()
    session = CoopSession(scenario)
    try:
        session.command({'action': 'mission', 'value': True})
        hz = session.scenario['simulation']['physics_hz']
        for _ in range(int(seconds * hz)):
            session.tick()
            if session.behaviour.state == 'flat' or not session.running:
                break  # battery empty, or the robot reached the terrain edge
        summary = session.metrics.summary(session.battery.used)
        return {'variant': variant, 'seed': seed, 'seconds': round(session.time, 2),
                'wall_seconds': round(time.perf_counter() - started, 1), 'final_state': session.behaviour.state,
                'battery_end': round(session.battery.state_of_charge(), 4), 'metrics': summary,
                'events': [event['text'] for event in list(session.events)[-40:]]}
    finally:
        session.close()


def _value(record, path):
    value = record if path[0] in ('battery_end',) else record['metrics']
    for part in path:
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    if path == ('fox', 'fled_at'):
        return 1. if value is not None else 0.
    return value


def summarise(job, results):
    """Mean, spread and count per variant and column, plus the runs; failed runs are listed apart."""
    by_variant = {}
    failures = []
    for run, result in zip(job['runs'], results):
        if result is None:
            failures.append({'label': run['label'], 'error': run.get('error') or run['status']})
            continue
        by_variant.setdefault(result['variant'], []).append(result)
    table = []
    for name in job['info'].get('variants', list(by_variant)):
        records = by_variant.get(name, [])
        row = {'variant': name, 'runs': len(records)}
        for key, _, path in COLUMNS:
            values = [v for v in (_value(r, path) for r in records) if isinstance(v, (int, float))]
            row[key] = {'mean': round(statistics.fmean(values), 4) if values else None,
                        'sd': round(statistics.stdev(values), 4) if len(values) > 1 else None, 'n': len(values)}
        table.append(row)
    return {'columns': [{'key': key, 'label': label} for key, label, _ in COLUMNS], 'table': table,
            'runs': [r for r in results if r is not None], 'failures': failures}


def to_csv(result):
    """One row per run with every column, for a spreadsheet."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(['variant', 'seed', 'simulated_s', 'final_state'] + [label for _, label, _ in COLUMNS])
    for record in result.get('runs', []):
        values = [_value(record, path) for _, _, path in COLUMNS]
        writer.writerow([record['variant'], record['seed'], record['seconds'], record['final_state']]
                        + ['' if v is None else (round(v, 4) if isinstance(v, float) and math.isfinite(v) else v)
                           for v in values])
    return out.getvalue()
