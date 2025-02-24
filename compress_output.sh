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

# path to your python environment and the compression script
PYTHON=/path/to/py3_env/bin/activate
COMPRESSION_SCRIPT=/path/to/nczip_wrapper/run_compression.py

#run the compression on test directory
source $PYTHON
python $COMPRESSION_SCRIPT --input_directory "$INPUT_DIRECTORY" \
                           --nczip_script "$NCZIP_SCRIPT" \
                           --ncequal_script "$NCEQUAL_SCRIPT" \
                           --varnum "$VARNUM"
