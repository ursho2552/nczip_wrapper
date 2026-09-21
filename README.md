# NCZIP Wrapper

This repository contains scripts to compress NetCDF files using the `nczip` script and verify the compression using the `ncequal` script. The compression process is managed by a Python wrapper script that handles parallel processing and logging.

## Contents

- `nczip.sh`: Bash script to compress NetCDF files by converting them to NetCDF-4 if needed.
- `ncequal.py`: Python script to compare two NetCDF files for equality.
- `run_compression.py`: Python wrapper script to compress NetCDF files and verify the compression.
- `config.yaml`: Configuration file for the `run_compression.py` script.
- `compress_output.sh`: SLURM job script to compress the contents of a directory.

## Running the Compression Script
To run the compression script, you can use the provided compression script:

```bash
compression_script=./run_compression.py
python $compression_script --input_directory <input_directory> --nczip_script <path_nczip.sh> --ncequal_script <path_ncequal.py> --varnum <int>
```

## Script Descriptions

```nczip.sh```

The ```nczip.sh``` script compresses NetCDF files by converting them to NetCDF-4 if needed. It supports various options for compression levels, chunking policies, and more. Note that the compressed and original files will be kept.

```ncequal.py```

The ```ncequal.py``` script compares two NetCDF files for equality. It checks whether the files contain the same variables and whether the variables have the same values at randomly selected time steps.

```run_compression.py```

The ```run_compression.py``` script is a Python wrapper that compresses NetCDF files using the nczip script and verifies the compression using the ncequal script. It processes files in parallel and logs the results.
This script performs a walk to find all NetCDF files in the subdirectories of the provided input directory.

## Dependencies

Use the following to get a working python environment using conda:

```bash
conda create -n py313_nczip python=3.13 -y
conda activate py313_nczip
pip install cftime netCDF4 numpy sty xarray
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
pip install cftime netCDF4 numpy sty xarray
```

## Notes

The code in this repository is based on https://gitlab.climate.unibe.ch/burger/nczip_wrapper
