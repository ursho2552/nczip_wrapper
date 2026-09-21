#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Wrapper script to compress netcdf files.
Author: Urs Hofmann Elizondo
Date: 12-02-2025
"""

import sys
import os
import argparse
import subprocess
from datetime import datetime
from multiprocessing import Process, Queue

# Function to log messages
def log_message(message: str, config: dict) -> None:
    """
    Function to log messages to a file.
    """

    input_directory = config.input_directory

    with open(os.path.join(input_directory, 'nczip_log'), 'a', encoding="utf-8") as log_file:
        log_file.write(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}: {message}\n")

# Function to compress and check files
def process_file(file: str, queue: Queue, config: dict) -> None:
    """
    Function to compress and check a single netcdf file.
    """

    log_message(f"Processing {file}", config)

    input_directory = config.input_directory
    nczip_script = config.nczip_script
    ncequal_script = config.ncequal_script
    varnum = config.varnum

    # Run nczip script
    nczip_command = f"bash {nczip_script} -k {file}"
    nczip_result = subprocess.run(nczip_command, shell=True, check=False)
    if nczip_result.returncode != 0:
        log_message(f"nczip: Error code {nczip_result.returncode} while processing {file}", config)
        queue.put(False)
        return

    # nczip skips files already at the target compression level (or that are
    # missing/unwritable/not netCDF) without creating a .nz output - that is
    # not a failure, so don't run ncequal against a file that was never made.
    zipfilename = file[:-1] + 'z'
    if not os.path.exists(zipfilename):
        log_message(f"nczip: {file} already at target compression - nothing to do", config)
        queue.put(True)
        return

    # Run ncequal script
    ncequal_command = f"{ncequal_script} --nocolors --variable_number {varnum} {file} {zipfilename}"
    with open(os.path.join(input_directory, 'nczip_log'), 'a', encoding="utf-8") as log_file:
        ncequal_result = subprocess.run(ncequal_command, shell=True,
                                        check=False, stdout=log_file,
                                        stderr=log_file)
    if ncequal_result.returncode != 0:
        log_message(f"ncequal returned inequality of files {file} and {zipfilename}", config)
        queue.put(False)
        return

    # Replace original file with compressed file
    os.rename(zipfilename, file)
    queue.put(True)

# Function to sequentially process a bin (a share of the workload) of files
def process_bin(bin_files: list, queue: Queue, config: dict) -> None:
    """
    Function to process a list of files sequentially within a single worker process.
    """

    for file in bin_files:
        process_file(file, queue, config)

# Main function
def main(config: dict) -> None:
    """
    Main function to compress all netcdf files in the input directory.
    """

    input_directory = config.input_directory

    # Collect all files to process
    files_to_process = []
    for file in os.listdir(input_directory):
        if file.endswith('.nc'):
            files_to_process.append(os.path.join(input_directory, file))

    # Distribute files into max_workers bins of roughly equal total size
    # (LPT bin-packing: largest files first, each goes into the currently
    # smallest bin), then run each bin in its own worker process.
    max_workers = config.max_workers
    sized_files = sorted(
        ((os.path.getsize(file), file) for file in files_to_process),
        key=lambda sized_file: sized_file[0], reverse=True
    )
    bins = [[] for _ in range(max_workers)]
    bin_sizes = [0] * max_workers
    for size, file in sized_files:
        idx = bin_sizes.index(min(bin_sizes))
        bins[idx].append(file)
        bin_sizes[idx] += size

    # Process bins in parallel, one worker process per non-empty bin
    queue = Queue()
    processes = [Process(target=process_bin, args=(file_bin, queue, config))
                 for file_bin in bins if file_bin]
    for p in processes:
        p.start()
    # Drain results as they arrive, before joining: a worker's queue.put()
    # blocks once the underlying pipe buffer fills, and joining first (while
    # nothing is reading the queue) can deadlock a worker with many files.
    results = [queue.get() for _ in files_to_process]
    for p in processes:
        p.join()

    # Check results and log final message
    if all(results):
        log_message("finished zipping all files", config)
    else:
        log_message("compression job encountered errors", config)

if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Compress .nc files in a give directory')
    parser.add_argument('--input_directory', required=True, type=str,
                        help='Directory containing .nc files to compress')
    parser.add_argument('--nczip_script', required=False, nargs='?',
                        const='/path/to/nczip_wrapper/nczip.sh',
                        default='/path/to/nczip_wrapper/nczip.sh',
                        type=str, help='Path to nczip script')
    parser.add_argument('--ncequal_script', required=False, nargs='?',
                        const='/path/to/nczip_wrapper/ncequal.py',
                        default='/path/to/nczip_wrapper/ncequal.py',
                        type=str, help='Path to ncequal script')
    parser.add_argument('--varnum', required=False, default=3, type=int,
                        help='Number of variables to test')
    parser.add_argument('--max_workers', required=False, default=4, type=int,
                        help='Maximum number of files to compress in parallel (default: 4)')

    CONFIG = parser.parse_args()
    # check if scripts exists
    if not os.path.exists(CONFIG.nczip_script):
        print(f"Script file {CONFIG.nczip_script} does not exist.")
        sys.exit(1)
    if not os.path.exists(CONFIG.ncequal_script):
        print(f"Script file {CONFIG.ncequal_script} does not exist.")
        sys.exit(1)

    # check
    if not os.path.exists(CONFIG.input_directory):
        print(f"Directory {CONFIG.input_directory} does not exist.")
        sys.exit(1)

    # get a list of subdirectories that contain .nc files
    directories = []
    for root, dirs, files in os.walk(CONFIG.input_directory):
        for current_file in files:
            if current_file.endswith(".nc"):
                print(f"Found file {current_file} in {root}")
                directories.append(root)
                break

    # remove duplicates
    directories = list(set(directories))
    for directory in directories:
        print(f"Processing directory {directory}")
        CONFIG.input_directory = directory
        main(CONFIG)
        print(f"Finished processing directory {directory}")
