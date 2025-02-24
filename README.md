# NCZIP Wrapper

This repository contains scripts to compress NetCDF files using the `nczip` script and verify the compression using the `ncequal` script. The compression process is managed by a Python wrapper script that handles parallel processing and logging.

## Contents

- `nczip.sh`: Bash script to compress NetCDF files by converting them to NetCDF-4 if needed.
- `ncequal.py`: Python script to compare two NetCDF files for equality.
- `run_compression.py`: Python wrapper script to compress NetCDF files and verify the compression.
- `config.yaml`: Configuration file for the `run_compression.py` script.
- `compress_output.sh`: SLURM job script to compress the contents of a directory.


## Running the Compression Script
To run the compression script, use the provided SLURM job script compress_output.sh. This script sets up the environment, loads the necessary modules, and runs the compression script with the specified configuration.

In your runscript you can add the path to your local copy of the repository as:

```bash
compression_script=/path/to/nczip_wrapper/compress_output.sh
```

And run the compression at an appropriate time as:

```bash
sbatch $compression_script $WRKDIR/$YEAR
```

Note that you will have to setup your own python environment (see requiremnts.txt) and either define the nczip.sh and ncequal.py paths in compress_output.sh or provide them in the sbatch command as additional inputs:

```bash
sbatch $compression_script <input_directory> --nczip_script <path> --ncequal_script <path> --varnum <int>
```



## SLURM Job Script

To use the compression you can use the following:

```bash
#!/bin/bash -l
#SBATCH --job-name=compress_output
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=<your_email>
#SBATCH --time=00:15:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --partition=normal
#SBATCH --constraint=mc
#SBATCH --account=<account>

# Setup Environment
module purge
module load cray
module load cpeGNU
module load NCO
module load cray-python/3.11.5

# Ensure at least one argument (config file) is provided
if [[ "$#" -lt 1 ]]; then
    echo "Usage: $0 <input_directory> [--nczip_script <path>] [--ncequal_script <path>] [--varnum <int>]"
    exit 1
fi

INPUT_DIRECTORY=$1
shift  # Shift arguments so that optional ones can be processed

# Default values for optional arguments
NCZIP_SCRIPT="/path/to/nczip_wrapper/nczip.sh"
NCEQUAL_SCRIPT="/path/to/nczip_wrapper/ncequal.py"
VARNUM=5

# Parse optional arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --nczip_script)
            NCZIP_SCRIPT="$2"
            shift 2
            ;;
        --ncequal_script)
            NCEQUAL_SCRIPT="$2"
            shift 2
            ;;
        --varnum)
            VARNUM="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# path to your python environment and the compression script
PYTHON=/path/to/py3_env/bin/activate
COMPRESSION_SCRIPT=/path/to/nczip_wrapper/run_compression.py

#run the compression on test directory
source $PYTHON
python $COMPRESSION_SCRIPT --input_directory "$INPUT_DIRECTORY" \
                           --nczip_script "$NCZIP_SCRIPT" \
                           --ncequal_script "$NCEQUAL_SCRIPT" \
                           --varnum "$VARNUM"
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

See requirements.txt for python packages and test_submission.sh for modules needed to run on Eiger

## Notes

The code in this repository is based on https://gitlab.climate.unibe.ch/burger/nczip_wrapper
