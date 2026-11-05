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

# Directory containing this repository. sbatch runs a copy of this script from
# a spool directory, so its location cannot be derived from $0. Set NCZIP_DIR
# when submitting, otherwise the directory sbatch was called from is used.
NCZIP_DIR="${NCZIP_DIR:-${SLURM_SUBMIT_DIR:-$PWD}}"

# Optional python virtual environment to activate (directory containing bin/activate)
NCZIP_VENV="${NCZIP_VENV:-}"

# Default values for optional arguments
NCZIP_SCRIPT="$NCZIP_DIR/nczip.sh"
NCEQUAL_SCRIPT="$NCZIP_DIR/ncequal.py"
VARNUM=3

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

# path to the compression script
COMPRESSION_SCRIPT="$NCZIP_DIR/run_compression.py"
if [[ ! -f "$COMPRESSION_SCRIPT" ]]; then
    echo "ERROR: $COMPRESSION_SCRIPT not found."
    echo "Submit from the repository directory or set NCZIP_DIR, e.g.:"
    echo "  NCZIP_DIR=/path/to/nczip_wrapper sbatch compress_output.sh <input_directory>"
    exit 1
fi

# activate the python environment, if one is given
if [[ -n "$NCZIP_VENV" ]]; then
    source "$NCZIP_VENV/bin/activate"
fi

#run the compression on test directory
python "$COMPRESSION_SCRIPT" --input_directory "$INPUT_DIRECTORY" \
                           --nczip_script "$NCZIP_SCRIPT" \
                           --ncequal_script "$NCEQUAL_SCRIPT" \
                           --varnum "$VARNUM"
