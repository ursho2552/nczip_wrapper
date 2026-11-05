# NCZIP Wrapper

This repository contains scripts to compress NetCDF files using the `nczip` script and verify the compression using the `ncequal` script. The compression process is managed by a Python wrapper script that handles parallel processing and logging.

## Contents

- `nczip.sh`: Bash script to compress NetCDF files by converting them to NetCDF-4 if needed.
- `ncequal.py`: Python script to compare two NetCDF files for equality.
- `run_compression.py`: Python wrapper script to compress NetCDF files and verify the compression.
- `compress_output.sh`: SLURM job script to compress the contents of a directory (configured for CSCS, see below).
- `requirements.txt`: Pinned Python package versions.

## Running the Compression Script
To run the compression script, you can use the provided compression script:

```bash
compression_script=./run_compression.py
python $compression_script --input_directory <input_directory> \
                           --nczip_script <path_nczip.sh> \
                           --ncequal_script <path_ncequal.py> \
                           --varnum <int> \
                           --max_workers <int>
```

| Argument | Required | Default | Description |
|---|---|---|---|
| `--input_directory` | yes | – | Directory searched (recursively) for `.nc` files |
| `--nczip_script` | no | `nczip.sh` in the same directory as `run_compression.py` | Path to `nczip.sh` |
| `--ncequal_script` | no | `ncequal.py` in the same directory as `run_compression.py` | Path to `ncequal.py` |
| `--varnum` | no | `3` | Number of randomly chosen variables checked by `ncequal.py` |
| `--max_workers` | no | `4` | Number of files compressed in parallel |

Table: Command-line arguments of `run_compression.py`.

With the defaults, the script works from any clone of this repository. You only need `--nczip_script` and `--ncequal_script` to use other copies of the helper scripts.

**Warning:** once a compressed file has passed the `ncequal.py` check, it replaces the original file. If the check fails, the original is kept and the `.nz` file is left next to it for inspection (see `nczip_log`).

### Running as a SLURM job

`compress_output.sh` wraps `run_compression.py` in a SLURM job:

```bash
cd /path/to/nczip_wrapper
sbatch compress_output.sh <input_directory> [--nczip_script <path>] [--ncequal_script <path>] [--varnum <int>]
```

SLURM runs a copy of the job script from a spool directory, so the job script cannot find the repository from its own location. It reads the repository location from these environment variables:

| Variable | Default | Description |
|---|---|---|
| `NCZIP_DIR` | Directory `sbatch` was called from | Repository directory containing `run_compression.py`, `nczip.sh` and `ncequal.py` |
| `NCZIP_VENV` | unset (no environment activated) | Python virtual environment to activate (directory containing `bin/activate`) |

Table: Environment variables read by `compress_output.sh`.

To submit from elsewhere, or with a virtual environment:

```bash
NCZIP_DIR=/path/to/nczip_wrapper NCZIP_VENV=/path/to/my-venv sbatch compress_output.sh <input_directory>
```

The job script is configured for CSCS (account `<account>`, partition `normal`, Cray modules). On other clusters, adapt the `#SBATCH` header and the `module load` lines. It does not pass `--max_workers`, so the default of 4 workers is used even though 16 CPUs are requested.

## Script Descriptions

```nczip.sh```

The ```nczip.sh``` script compresses NetCDF files by converting them to NetCDF-4 if needed. It supports various options for compression levels, chunking policies, and more (see `nczip.sh -h`). By default the original file is overwritten. With `-k` the original is kept and the compressed file is written next to it, with the extension `.nc` replaced by `.nz`. Files in which every variable already has the target compression level are skipped.

```ncequal.py```

The ```ncequal.py``` script compares two NetCDF files for equality. It checks whether the files contain the same variables, then compares a random selection of variables (`--variable_number`, default 3). Variables with a `time`/`TIME` dimension are compared at randomly selected time steps (`--time_step_number`, default 3). All other variables, including those in files without a time axis, are compared in full.

```run_compression.py```

The ```run_compression.py``` script is a Python wrapper that compresses NetCDF files using the nczip script and verifies the compression using the ncequal script.
It walks through the provided input directory to find every subdirectory that contains NetCDF files, then processes each directory in turn. For each file it:

1. runs `nczip.sh -k`, which writes a `.nz` file,
2. compares the original and the `.nz` file with `ncequal.py`,
3. replaces the original with the `.nz` file if they are equal.

Within a directory, files are compressed in parallel by `--max_workers` processes. The files are distributed so that each worker gets roughly the same total data volume, with the largest files assigned first. Progress and errors are logged to a file called `nczip_log` in each processed directory.

## Dependencies

The following command-line tools must be available in `PATH`:

- [NCO](https://nco.sourceforge.net/) (`ncks`, `ncpdq`), built with netCDF-4 support
- netCDF utilities (`ncdump`, `nc-config`), with netCDF-4 support

`nczip.sh` stops with an error if netCDF-4 support is missing.

The Python packages are listed with pinned versions in `requirements.txt`. Use the following to get a working python environment using conda:

```bash
conda create -n py313_nczip python=3.13 -y
conda activate py313_nczip
pip install -r requirements.txt
```

On CSCS this can be done by using the following:
```bash
uenv start --view=netcdf netcdf-tools/2025:v2
```

In the uenv, you can define a new python environment built on top of the existing environment using:

```bash
unset PYTHONPATH
export PYTHONUSERBASE="$(dirname "$(dirname "$(which python)")")"
python -m venv --system-site-packages path/to/my-venv
```

Then activate it using:

```bash
source path/to/my-venv/bin/activate
```

After activating the virtual environment, you can install the required Python packages using:

```bash
pip install -r requirements.txt
```

## Notes

The code in this repository is based on https://gitlab.climate.unibe.ch/burger/nczip_wrapper
