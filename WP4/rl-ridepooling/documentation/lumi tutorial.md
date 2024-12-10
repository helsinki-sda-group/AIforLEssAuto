# LUMI ridepooling manual

## Logging into LUMI

Before running the installation script, log into LUMI. Please refer to the following guide for setting up an SSH key pair:

https://docs.lumi-supercomputer.eu/firststeps/SSH-keys/

Then you should be able to log into LUMI.

```
ssh -i <path-to-private-key> <username>@lumi.csc.fi
```

The following manual may also be of use:

https://docs.lumi-supercomputer.eu/firststeps/loggingin/

More guides for getting started with using LUMI can be found here:

https://docs.lumi-supercomputer.eu/firststeps/getstarted/

## PyTorch and SUMO installation

Even though LUMI already has Python installed on a system, this is a stock Python 3.6 that LUMI uses internally, so packages should not be installed directly using Conda, pip, or similar package management tools. For better alternatives, read this guide:

https://docs.lumi-supercomputer.eu/software/installing/python/

In our case, we chose to use an existing prebuilt PyTorch singularity container provided by the LUMI support team. More information about this container can be found here:

https://lumi-supercomputer.github.io/LUMI-EasyBuild-docs/p/PyTorch/


To extend the container with all the pip packages needed to launch the training, we first need to copy the EasyBuild recipe for the container to our local filesystem with these commands:

```
module load LUMI partition/container EasyBuild-user
eb --copy-ec PyTorch-2.2.2-rocm-5.6.1-python-3.10-vllm-0.4.0.post1-singularity-20240617.eb .
```

For our experiments we used the container `20240617` as the base container. You can find the full easybuild config here:

https://lumi-supercomputer.github.io/LUMI-EasyBuild-docs/p/PyTorch/PyTorch-2.2.2-rocm-5.6.1-python-3.10-vllm-0.4.0.post1-singularity-20240617/

It is generally recommended to use the latest version available on the [LUMI Software Library PyTorch page](https://lumi-supercomputer.github.io/LUMI-EasyBuild-docs/p/PyTorch/)


To setup the container with our environment, we modified the `local_pip_requirements` variable inside the EasyBuild recipe used for building the container (the empty line at the end of the variable is required):

```
local_pip_requirements = """
torchmetrics
pytorch-lightning
beautifulsoup4>=4.12.2
gymnasium>=0.29.1
libsumo>=1.19.0
matplotlib>=3.8.2
networkx>=3.2.1
numpy>=1.26.3
omegaconf>=2.3.0
pandas>=2.1.4
stable_baselines3>=2.2.1
sumolib>=1.19.0
eclipse-sumo>=1.19.0
lxml>=5.1.0

"""
```

From the `local_pip_requirements` variable, you can see that `eclipse-sumo` package, which contains SUMO binaries is already included in the python environment that we create. This way, we don't need to install SUMO manually.

Next, build the container with the EasyBuild-user module in `partition/container`:

```
module load LUMI partition/container EasyBuild-user
eb <easyconfig>
```

The module will be available in all versions of the LUMI stack and in the CrayEnv stack.
To access module help after installation use `module spider PyTorch/<version>`.


## Using the container

Once the container is installed, we can load the PyTorch module with `module load LUMI partition/C PyTorch/2.2.2-rocm-5.6.1-python-3.10-vllm-0.4.0.post1-singularity-20240617` after logging into LUMI.

We can now enter the container with `singularity shell --bind /usr/lib64 $SIF`. Binding `/usr/lib64` ensures proper linking of dynamic libraries required for SUMO to operate inside the container.

Running `sumo --version` and `python --version` inside the container should print the correct sumo and python versions.

## Installing rl-ridepooling

In this tutorial we are using the `performance-model` branch of the rl-ridepooling algorithm (https://github.com/helsinki-sda-group/AIforLEssAuto/tree/main/WP4/rl-ridepooling)

To install it, run:

```
git clone https://github.com/helsinki-sda-group/AIforLEssAuto.git
cd AIforLEssAuto
git checkout performance-model
```

## Example script

Let's take a look at an example script for testing different combinations of training parameters for our script for area1 of Helsinki:

```
#!/bin/bash
#SBATCH --array=0-79
#SBATCH --job-name="area1_grid_search"
#SBATCH --output="output/%A_%a_%x/main.log"
#SBATCH --account=project_462000655
#SBATCH --time=30
#SBATCH --nodes=1
#SBATCH --mem=0
#SBATCH --partition=standard
#SBATCH --exclusive

# load modules
module --force purge
module load LUMI/24.03
module load lumi-CPEtools
module load partition/C
module load PyTorch/2.2.2-rocm-5.6.1-python-3.10-vllm-0.4.0.post1-singularity-20240617

# list all modules
module list

# declare env variables for SUMO
export LIBSUMO_AS_TRACI=1
export SUMO_HOME=/user-software/venv/pytorch/bin

export OMP_DYNAMIC=TRUE

cpu_mask="1"
cpu_mask="${cpu_mask},c"
cpu_mask="${cpu_mask},f0"
cpu_mask="${cpu_mask},ff00"
cpu_mask="${cpu_mask},FFFF0000"
cpu_mask="${cpu_mask},FFFFFFFF00000000"
cpu_mask="${cpu_mask},FFFFFFFFFFFFFFFF0000000000000000"
cpu_bind="--cpu-bind=verbose,mask_cpu:${cpu_mask}"

# Define hyperparameters
export NUM_ENVS_STR="1:2:4:8:16:32:64"
export AREAS_STR="area1"
export PERCENTAGE_SAMPLED_STR="0.1:0.2:0.3:0.4:0.5"
export TRAIN_FREQS_STR="1:2:4:8"
export DELTAS_STR="1:60:300:1800"

# Read arrays
IFS=":" read -r -a AREAS <<< "$AREAS_STR"
IFS=":" read -r -a PERCENTAGES <<< "$PERCENTAGE_SAMPLED_STR"
IFS=":" read -r -a TRAIN_FREQS <<< "$TRAIN_FREQS_STR"
IFS=":" read -r -a DELTAS <<< "$DELTAS_STR"

# Generate all combinations
declare -a COMBINATIONS
index=0
for area in "${AREAS[@]}"; do
    for percent in "${PERCENTAGES[@]}"; do
        for train_freq in "${TRAIN_FREQS[@]}"; do
            for delta in "${DELTAS[@]}"; do
                COMBINATIONS[$index]="$area:$percent:$train_freq:$delta"
                ((index++))
            done
        done
    done
done

# Get the combination for this task
combo=${COMBINATIONS[$SLURM_ARRAY_TASK_ID]}
IFS=":" read -r AREA PERCENTAGE_SAMPLED TRAIN_FREQ DELTA <<< "$combo"

# Export hyperparameters
export AREA
export PERCENTAGE_SAMPLED
export TRAIN_FREQ
export DELTA

# Print hyperparameters
echo "Selected AREA: $AREA"
echo "Selected PERCENTAGE_SAMPLED: $PERCENTAGE_SAMPLED"
echo "Selected TRAIN_FREQ: $TRAIN_FREQ"
echo "Selected DELTA: $DELTA"

output_file_dir="output/${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}_${SLURM_JOB_NAME}_${AREA}_sampled${PERCENTAGE_SAMPLED}_trainfreq${TRAIN_FREQ}_delta${DELTA}"

srun --ntasks=7 --kill-on-bad-exit=0 --output="${output_file_dir}/task_%t.log" --error="${output_file_dir}/task_%t.err" ${cpu_bind} bash -c '
    cd ~/prj/AIforLEssAuto/WP4/rl-ridepooling
    pwd
    IFS=":" read -r -a NUM_ENVS <<< "$NUM_ENVS_STR"
    NUM=${NUM_ENVS[$SLURM_PROCID]}
    echo -n "task $SLURM_PROCID num_envs: $NUM "
    taskset -cp $$
    hybrid_check -n -r
    singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/${AREA}_sampled_${PERCENTAGE_SAMPLED}.yaml --total-iters $NUM --num-envs $NUM --train-freq $TRAIN_FREQ --delta $DELTA --prefix ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}_${SLURM_PROCID}_e${NUM}_${AREA}_${PERCENTAGE_SAMPLED}_tf${TRAIN_FREQ}_dlt${DELTA}_${SLURM_JOB_NAME}

'

wait
```

Let's go over the script section by section and see what it does

### SLURM directives
```
#SBATCH --array=0-79
#SBATCH --job-name="area1_grid_search"
#SBATCH --output="output/%A_%a_%x/main.log"
#SBATCH --account=project_462000655
#SBATCH --time=30
#SBATCH --nodes=1
#SBATCH --mem=0
#SBATCH --partition=standard
#SBATCH --exclusive
```

The directives create a job array where each job will test a different combination of hyperparameters defined later. More information about Array Jobs can be found in [LUMI documentation](https://docs.lumi-supercomputer.eu/runjobs/scheduled-jobs/throughput/)

The output name is specified using a filename pattern in slurm, which you can read more on the [sbatch documentation](https://slurm.schedmd.com/sbatch.html) in the Filename Pattern section

One job reserves the node in an exclusive mode with `--exclusive` option and reserves all the memory available on the node using `--mem=0`. Setting `--mem=0` allocates all available memory on the node to the job.

### Module loading
```
module --force purge
module load LUMI/24.03
module load lumi-CPEtools
module load partition/C
module load PyTorch/2.2.2-rocm-5.6.1-python-3.10-vllm-0.4.0.post1-singularity-20240617
module list
```

The script first unloads any previously loaded modules (`module purge`), loads required software modules and prints them to the output file


### Environment setup

```
export LIBSUMO_AS_TRACI=1
export SUMO_HOME=/user-software/venv/pytorch/bin
export OMP_DYNAMIC=TRUE
```

1. `SUMO_HOME`: SUMO requires SUMO_HOME environment variable to be set up. We set this variable to point to bin directory inside the PyTorch container
2. `LIBSUMO_AS_TRACI`: this variable specifies that we use a faster libsumo library for communication with SUMO compared to traCI used by default
3. `OMP_DYNAMIC`: enables dynamic adjustment of the number of OpenMP threads. We found that it speeds up the training for setups that use up to 64 cores/environments. However, for 128 cores, setting this variable worsens the performance

### CPU Mask setup
```
cpu_mask="1"
cpu_mask="${cpu_mask},c"
cpu_mask="${cpu_mask},f0"
cpu_mask="${cpu_mask},ff00"
cpu_mask="${cpu_mask},FFFF0000"
cpu_mask="${cpu_mask},FFFFFFFF00000000"
cpu_mask="${cpu_mask},FFFFFFFFFFFFFFFF0000000000000000"
cpu_bind="--cpu-bind=verbose,mask_cpu:${cpu_mask}"
```

This part of the script specifies custom binding of tasks to CPU-cores using CPU masks in a hexadecimal format. 

All jobs are executed on LUMI-C nodes, which has 128 physical cores and 256 logical cores. Each job inside a job array will launch 7 tasks, and each of those tasks will have a different number of cores attached to them. This way we tested the performance of the algorithm when increasing the number of cores.

This binding specifies that:
1. Task 1 will run on 1 core (the first one, core 0)
2. Task 2 will run on 2 cores (cores 2,3)
3. Task 3 will run on 4 cores (4-7)
4. Task 4 will run on 8 cores (8-15)
5. Task 5 will run on 16 cores (16-31)
6. Task 6 will run on 32 cores (32-63)
7. Task 7 will run on 64 cores (64-127)

The last line will set the final `cpu_bind` variable that we will append to the script parameters. We use verbose mode to get more information about the binding that happens.

For more information about Slurm binding, read this LUMI guide: https://docs.lumi-supercomputer.eu/runjobs/scheduled-jobs/distribution-binding/

For testing on 128 cores, we use a separate shell script in which we declare the `cpu_bind` variable as follows:

```
cpu_mask="FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
cpu_bind="--cpu-bind=verbose,mask_cpu:${cpu_mask}"
```

which means that we're assigning every core to the first launched task.


### Hyperparameter setup

To perform multiple experiments, we define a set of hyperparameters inside the script for launching the job array. We generate a list of all possible combinations of parameters in the `COMBINATIONS` array. Each job accesses its parameters via the SLURM array task ID (`$SLURM_ARRAY_TASK_ID`).

Hyperparameter descriptions:
* `NUM_ENVS_STR`: determines the number of parallel environments that each individual SLURM task will launch, depending on the SLURM process ID (`$SLURM_PROCID`).
* `AREAS_STR`: Specifies the geographical area for which the RL training will be conducted. Is set to either `area1`, `area2`, or `area3`. `area1` is the smallest, `area3` is the largest
* `PERCENTAGE_SAMPLED_STR`: Fraction of the total route dataset to sample for training. Lower values use less routes.
* `TRAIN_FREQS_STR`: The frequency of updates of the reinforcement learning model (DQN). The model is updated every train_freq steps of the RL algorithm.
* `DELTAS_STR`: The length of one step of the RL algorithm in SUMO steps. The action is applied to a SUMO environment every delta steps.

```
# Define hyperparameters
export NUM_ENVS_STR="1:2:4:8:16:32:64"

export AREAS_STR="area1"
export PERCENTAGE_SAMPLED_STR="0.1:0.2:0.3:0.4:0.5"
export TRAIN_FREQS_STR="1:2:4:8"
export DELTAS_STR="1:60:300:1800"

# Read arrays
IFS=":" read -r -a AREAS <<< "$AREAS_STR"
IFS=":" read -r -a PERCENTAGES <<< "$PERCENTAGE_SAMPLED_STR"
IFS=":" read -r -a TRAIN_FREQS <<< "$TRAIN_FREQS_STR"
IFS=":" read -r -a DELTAS <<< "$DELTAS_STR"

# Generate all combinations
declare -a COMBINATIONS
index=0
for area in "${AREAS[@]}"; do
    for percent in "${PERCENTAGES[@]}"; do
        for train_freq in "${TRAIN_FREQS[@]}"; do
            for delta in "${DELTAS[@]}"; do
                COMBINATIONS[$index]="$area:$percent:$train_freq:$delta"
                ((index++))
            done
        done
    done
done

# Get the combination for this task
combo=${COMBINATIONS[$SLURM_ARRAY_TASK_ID]}
IFS=":" read -r AREA PERCENTAGE_SAMPLED TRAIN_FREQ DELTA <<< "$combo"

# Export hyperparameters
export AREA
export PERCENTAGE_SAMPLED
export TRAIN_FREQ
export DELTA

# Print values
echo "Selected AREA: $AREA"
echo "Selected PERCENTAGE_SAMPLED: $PERCENTAGE_SAMPLED"
echo "Selected TRAIN_FREQ: $TRAIN_FREQ"
echo "Selected DELTA: $DELTA"
```

This part of the script:

1. Defines all possible values for hyperparameters in a string separated by `:` 
2. Generates all combinations of hyperparameters.
3. Selects the specific combination for each task based on its ID.
4. Exports those values as environment variables
5. Prints the values of selected hyperparameters to the output file

### Job execution
```
output_file_dir="output/${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}_${SLURM_JOB_NAME}_${AREA}_sampled${PERCENTAGE_SAMPLED}_trainfreq${TRAIN_FREQ}_delta${DELTA}"

srun --ntasks=7 --kill-on-bad-exit=0 --output="${output_file_dir}/task_%t.log" --error="${output_file_dir}/task_%t.err" ${cpu_bind} bash -c '
    cd ~/prj/AIforLEssAuto/WP4/rl-ridepooling
    pwd
    IFS=":" read -r -a NUM_ENVS <<< "$NUM_ENVS_STR"
    NUM=${NUM_ENVS[$SLURM_PROCID]}
    echo -n "task $SLURM_PROCID num_envs: $NUM "
    taskset -cp $$
    hybrid_check -n -r
    singularity exec --bind /usr/lib64 $SIF python src/tests/gym_test-rs.py --config configs/policy_training/helsinki_updated_areas/${AREA}_sampled_${PERCENTAGE_SAMPLED}.yaml --total-iters $NUM --num-envs $NUM --train-freq $TRAIN_FREQ --delta $DELTA --prefix ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}_${SLURM_PROCID}_e${NUM}_${AREA}_${PERCENTAGE_SAMPLED}_tf${TRAIN_FREQ}_dlt${DELTA}_${SLURM_JOB_NAME}

'

wait
```

First, this part defines a unique output directory for each task based on the job and task IDs, as well as the selected hyperparameters.

The next step uses `srun` to run the task on a compute node. It specifies `ntasks=7` (7 tasks per job) and uses `cpu_bind` to bind tasks to specific CPUs and different files for stdout and stderr streams.

Inside the bash -c block, the script:
1. Changes the directory to the project folder.
2. Reads the number of environments to run based on the task ID (`$SLURM_PROCID`).
3. Prints current task affinity using `taskset -cp $$`
4. Prints resource allocation and mapping report using `hybrid_check`. This output will be available in the .log file for task 0 
5. Launches the singularity container with `singularity exec` command, which executes the `gym_test-rs.py` script. It determines the config file from `configs/policy_training/helsinki_updated_areas` using `$AREA` and `$PERCENTAGE_SAMPLED` variables and sets the following variables:
    * `--total-iters`: The total number of iterations for training the reinforcement learning algorithm. This is set to the number of environments (`$NUM`). This means that we are only launching one batch of environments for training. 
    * `--num-envs`: The number of environments to launch in parallel and is also set to the `$NUM` variable.
    * `--train-freq`: The frequency of updates of the reinforcement learning model (DQN). The model is updated every train_freq steps of the RL algorithm. This is set to the `$TRAIN_FREQ` hyperparameter.
    * `--delta`: The length of one step of the RL algorithm in SUMO steps. The action is applied to a SUMO environment every delta steps. Set to `$DELTA`.
    * `--prefix`: Sets the prefix name of the output directory to contain all the information about the hyperparameters. (This is done for easier access to output)
6. Waits for all tasks to execute before finishing the job