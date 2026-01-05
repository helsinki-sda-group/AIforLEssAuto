# MAHTI Batch Experiment Launcher

This directory contains scripts for running RL ridepooling experiments on the MAHTI supercomputer at CSC.

## Files

| File | Description |
|------|-------------|
| `run_experiments.sh` | Master launcher that submits all parameter combinations as separate Slurm jobs |
| `job_template.sh` | Parameterized job template executed by each Slurm job |

## Quick Start

```bash
# On MAHTI, navigate to project directory
cd /projappl/project_2016787/AIforLEssAuto/WP4/rl-ridepooling

# Preview all jobs without submitting (recommended first step)
./configs/Slurm/MAHTI/run_experiments.sh --dry-run

# Submit all 127 experiment jobs
./configs/Slurm/MAHTI/run_experiments.sh
```

## Configuration

### Before First Use

Edit `run_experiments.sh` and update the following settings:

```bash
# SLURM CONFIGURATION section (around line 44)
ACCOUNT="project_2016787"           # Your CSC billing project
MAIL_USER="your.email@helsinki.fi"  # Your email for notifications
PROJECT_DIR="/projappl/..."         # Path to your project on MAHTI
```

### Experiment Parameters

Edit the arrays at the top of `run_experiments.sh` to customize which experiments to run:

```bash
# Network areas: "toy" (small test network) or "area3" (Helsinki area 3)
AREAS=("toy" "area3")

# Demand levels: fraction of trips as taxi passengers
# Note: "toy" only supports 1.0; toy+0.2 combinations are automatically skipped
DEMANDS=("0.2" "1.0")

# Delta: RL decision step duration in SUMO simulation steps
DELTAS=(1 30)

# Number of parallel SUMO environments
# 1 env -> 3 CPUs
# 126 envs -> 128 CPUs
NUM_ENVS_LIST=(1 126)

# DQN training frequency: update model every N steps
TRAIN_FREQS=(4 100)

# Gradient steps per update: -1 = num_envs, 1 = single step
GRADIENT_STEPS_LIST=(-1 1)

# Episode scaling coefficient: 0 = no scaling, 1 = full scaling for delta
SCALING_COEFS=(0 1)
```

## Dry Run Mode

Always use `--dry-run` first to verify the job configuration:

```bash
./configs/Slurm/MAHTI/run_experiments.sh --dry-run
```

This prints all `sbatch` commands that would be executed without actually submitting jobs.

### Resource Allocation

Resources are automatically determined based on parameters:

| Configuration | CPUs | Partition | Time Limit |
|---------------|------|-----------|------------|
| `toy`, 1 env | 3 | small | 30 min |
| `toy`, 126 envs | 128 | small | 2 hours |
| `area3`, 1 env | 3 | small | 10 hours |
| `area3`, 126 envs | 128 | small | 10 hours |

Memory is auto-allocated by MAHTI: 1 CPU = 1.875 GiB.

## Output

### Slurm Logs

Job output is written to `slurm_output/` in the project root:
- `<job_id>-<job_name>-stdout.log` - Standard output
- `<job_id>-<job_name>-stderr.log` - Standard error

### Training Results

Each experiment saves results to `src/tests/output/<timestamp>_<job_id>_<params>/`:
- `config.yaml` - Full configuration used
- `stdout.txt` - Training output
- `time.txt` - Training duration
- `train/` - Training logs (monitor CSV)
- `eval/` - Evaluation logs
- `test/` - Test results
- `best_model/` - Best model checkpoint
- `ridepooling_DQN.zip` - Final trained model

### Result Naming Convention

Job names encode all parameters for easy identification:

```
<area>_d<demand>_delta<delta>_env<num_envs>_tf<train_freq>_gs<gradient_steps>_sc<scaling_coef>
```

Example: `area3_d0.2_delta30_env126_tf4_gs-1_sc0`

## Email Notifications

The script configures Slurm to send email notifications for:
- **FAIL** - Job failed (non-zero exit code)
- **TIME_LIMIT** - Job exceeded time limit

No email is sent for successful completions (to avoid inbox flooding with 127 emails).

## Total Combinations

With default parameters:
- 2 areas × 2 demands = 4 (minus 1 invalid: toy+0.2) = **3 area-demand pairs**
- × 2 deltas × 2 envs × 2 train_freqs × 2 gradient_steps × 2 scaling_coefs = **× 32**
- **Total: 96 jobs** (if using both areas) or **127 jobs** (calculation varies by parameter count)

The summary at the end of `run_experiments.sh` will show exact counts.

## Customizing for Subset of Experiments

To run only specific combinations, edit the parameter arrays. For example, to run only `area3` with `delta=30`:

```bash
AREAS=("area3")
DELTAS=(30)
# ... keep other arrays as-is
```

## Troubleshooting

### Job Failed Immediately
Check `slurm_output/<job_id>-*-stderr.log` for error messages. Common issues:
- Missing SUMO config file (wrong path)
- Module not loaded
- Virtual environment activation failed

### Out of Memory
Increase `--cpus-per-task` in `run_experiments.sh` (memory scales with CPUs on MAHTI).

### Job Timeout
Increase `TIME_LIMIT` for the relevant area/env combination in `run_experiments.sh`.

## Dependencies

The template script expects:
- PyTorch module (`module load pytorch`)
- Singularity container with SUMO and Python environment
- Virtual environment at `ridepool-venv/`
- Base config at `configs/policy_training/base.yaml`
