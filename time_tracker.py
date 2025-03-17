#!/usr/bin/env python
from datetime import datetime, timedelta
import json
import argparse
import os
import math
from collections import namedtuple

WORKING_HOURS = 37.5
WORKING_DAY = WORKING_HOURS / 5
LUNCH = 3.5
TARGETS_PATH = "config/targets.json"

PrintConfig = namedtuple("PrintConfig", ["max_bar_width", "max_key_length"])


def progress_bar(task: str, current: timedelta, target: timedelta, config: PrintConfig) -> None:
    frac_filled = (current / target)
    bar_width = int(frac_filled * config.max_bar_width)
    remaining = config.max_bar_width - bar_width
    bar = '█' * bar_width + '-' * remaining
    print(f"{task.ljust(config.max_key_length)}:|{bar}| {frac_filled*100:.1f}% ({current})")


def main():
    # Load up the targets and autogenerate args accordingly
    with open(TARGETS_PATH, "r") as f:
        targets = json.load(f)

    if sum(targets.values()) != WORKING_HOURS - LUNCH:
        raise ValueError(f"You're not working the correct amount of hours! Working: {sum(targets.values())}.")

    max_bar_width = int(math.lcm(*list(targets.values())))
    while max_bar_width < 10:
        # Make it a bit bigger and more satisfying
        max_bar_width *= 2
    max_key_length = max([len(t) for t in targets.keys()])
    print_config = PrintConfig(max_bar_width, max_key_length)
    dt_targets = {k: timedelta(hours=v) for k, v in targets.items()}
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--show", action='store_true', help='Print the time-tracking summary')
    parser.add_argument("--clean", action='store_true', help='Reset all values to 0')
    parser.add_argument("--save-to", type=str, default="", help="In addition to usual save, save to this path as well (e.g. at end of week, or backup.")
    for task in targets.keys():
        parser.add_argument(f'--{task}', type=float, default=0, help=f"Add this much time (in minutes) to {task}.")
        parser.add_argument(f'--reset-{task}', type=float, help=f"Reset time spent on {task} to value (in hours).")

    args = parser.parse_args()

    # Load up the current weekly set of times
    file_path = "data/current.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            raw = json.load(f)
            current = {t: timedelta(hours=v) for t, v in raw.items()} 
    else:
        current = {t: timedelta(0) for t in targets.keys()}

    def _update():
        for arg, argval in vars(args).items():
            if arg == 'clean':
                if argval:
                    for t in current.keys():
                        current[t] = timedelta(0)
                    return
                else:
                    continue
            elif arg in ['show', 'save_to']:
                continue
            elif 'reset' in arg:
                task = arg.split('_')[-1]
                if argval is not None:
                    print("Reseting")
                    current[task] = timedelta(hours=argval)
            else:
                current[arg] += timedelta(minutes=argval)

    _update()

    def _to_hrs(dtime: timedelta):
        return float(dtime.total_seconds() / 3600)

    if args.show:
        print("Current summary of time tracking...")
        print(f"The bar width (LCM) will be {print_config.max_bar_width}")
        for task, tgt in dt_targets.items():
            progress_bar(task, current[task], tgt, print_config)

    total_spent = sum(current.values(), start=timedelta(0))
    pct = 100 * total_spent / timedelta(hours=WORKING_HOURS)
    working_days_spent = total_spent/timedelta(hours=WORKING_DAY)
    print(f"Total working hours spent: {_to_hrs(total_spent):.2f}/{WORKING_HOURS} ({working_days_spent:.2f} days, or {pct:.1f}% of the working week).")


    # Save to file
    writeable = {t: _to_hrs(dtime_v) for t, dtime_v in current.items()}
    with open(file_path, "w") as f:
        json.dump(writeable, f, indent=4)
    print(f"Written results to {file_path}")

    if args.save_to:
        with open(args.save_to, "w") as f:
            json.dump(writeable, f, indent=4)
        print(f"Also written results to {args.save_to}")
    

if __name__ == "__main__":
    main()
