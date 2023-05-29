# LUMI SUMO manual

## Installation script
If everything still works as it did in the spring of 2023, then the following bottom-up installation script should install SUMO with all things needed. The only thing that needs to be changed is the project ID when setting the environment variable `START_DIR`. Just replace `<PROJECT_ID>` with the current LUMI project's ID.

```
# Creating an environment variable that will serve as a "home directory"
export START_DIR="/scratch/<PROJECT_ID>"

# Compiling Xerces and creating a custom module
cd $START_DIR

# Loading the C partition (for CPU jobs) and Easybuild
module purge
module load LUMI/22.08 partition/C
module load EasyBuild-user

# Creating a configuration file for building Xerces with Easybuild
echo "easyblock = 'ConfigureMake'

name = 'Xerces-C++'
version = '3.2.4'

homepage = 'http://xerces.apache.org/xerces-c/'
description = 'Xerces-C++ is a validating XML parser written in a portable subset of C++. Xerces-C++ makes it easy to give your application the ability to read and write XML data. A shared library is provided for parsing, generating, manipulating, and validating XML documents using the DOM, SAX, and SAX2 APIs. Custom module created in March 2023 for compiling the traffic simulator SUMO in CSCs HPC service.'

toolchain = {'name': 'cpeGNU', 'version': '22.08'}

sources = ['xerces-c-%(version)s.tar.gz']
source_urls = [
    'https://downloads.apache.org/xerces/c/3/sources/',
    'https://archive.apache.org/dist/xerces/c/3/sources/'
]

dependencies = [
    ('cURL', '7.83.1'),
]

moduleclass = 'lib'" > Xerces.eb
# Downloading Xerces
wget https://downloads.apache.org/xerces/c/3/sources/xerces-c-3.2.4.tar.gz
# Building Xerces
eb Xerces.eb


# Compiling SUMO
cd $START_DIR
module purge
module use $HOME/Easybuild/modules/all
module load LUMI/22.08 partition/C
module load EasyBuild-user
module load cray-python/3.9.13.1
module load Xerces-C++/3.2.4-cpeGNU-22.08
git clone https://github.com/eclipse/sumo
export SUMO_HOME="$START_DIR/sumo"
mkdir sumo/build/cmake-build
cd sumo/build/cmake-build
cmake ../..
make -f Makefile


# Creating SUMO modules
cd $START_DIR
mkdir SUMO_modules
cd SUMO_modules

# SUMO .lua file
echo "help ([[For instructions on how to compile SUMO in Linux, go to:
 https://sumo.dlr.de/docs/Installing/Linux_Build.html
]])

whatis('Version: 1.16.0')
whatis('Keywords: Traffic simulation')
whatis('URL: https://www.eclipse.org/sumo/')
whatis('Description: SUMO (Simulation of Urban MObility) is an open source traffic simulator. This is a custom LUMI module created in April 2023 by Anton Taleiko for the research group Spatiotemporal Data Analysis at the University of Helsinki for their project AI4LEssAuto.')

setenv(       'HELLOPATH',      '/scratch/<PROJECT_ID>/ModuleBin/SUMO/1.16.0/bin')
prepend_path( 'PATH',           '/scratch/<PROJECT_ID>/ModuleBin/SUMO/1.16.0/bin')" > sumo.lua

# od2trips .lua file
echo "help ([[For instructions on how to compile SUMO in Linux (and od2trips with it), go to:
 https://sumo.dlr.de/docs/Installing/Linux_Build.html
]])

whatis('Version: 1.0.0')
whatis('Keywords: Vehicle generation')
whatis('URL: https://sumo.dlr.de/docs/od2trips.html')
whatis('Description: od2trips is a tool used for generating trips (vehicles) for the traffic simulation software SUMO (Simulation of Urban MObility). It takes origin-destination matrices as input and outputs an xml file. This is a custom LUMI module created in April 2023 by Anton Taleiko for the research group Spatiotemporal Data Analysis at the University of Helsinki for their project AI4LEssAuto.')

setenv(       'HELLOPATH',      '/scratch/<PROJECT_ID>/ModuleBin/od2trips/1.0.0/bin')
prepend_path( 'PATH',           '/scratch/<PROJECT_ID>/ModuleBin/od2trips/1.0.0/bin')" > od2trips.lua

# Duarouter .lua file
echo "help ([[For instructions on how to compile SUMO in Linux (and Duarouter with it), go to:
 https://sumo.dlr.de/docs/Installing/Linux_Build.html
]])

whatis('Version: 1.0.0')
whatis('Keywords: Pathfinding, SUMO')
whatis('URL: https://sumo.dlr.de/docs/duarouter.html')
whatis('Description: Duarouter is a tool used for pathdinding that comes with the traffic simulation software SUMO (Simulation of Urban MObility). This is a custom LUMI module created in April 2023 by Anton Taleiko for the research group Spatiotemporal Data Analysis at the University of Helsinki for their project AI4LEssAuto.')

setenv(       'HELLOPATH',      '/scratch/<PROJECT_ID>/ModuleBin/duarouter/1.0.0/bin')
prepend_path( 'PATH',           '/scratch/<PROJECT_ID>/ModuleBin/duarouter/1.0.0/bin')" > duarouter.lua

# Creating directories containing the binary files
cd ..
mkdir ModuleBin
cd ModuleBin

mkdir SUMO
mkdir SUMO/1.16.0
mkdir SUMO/1.16.0/bin
cp $SUMO_HOME/bin/sumo SUMO/1.16.0/bin

mkdir od2trips
mkdir od2trips/1.0.0
mkdir od2trips/1.0.0/bin
cp $SUMO_HOME/bin/od2trips od2trips/1.0.0/bin

mkdir duarouter
mkdir duarouter/1.0.0
mkdir duarouter/1.0.0/bin
cp $SUMO_HOME/bin/duarouter duarouter/1.0.0/bin
```

## Notes

### LUMI partitions
One important part of the script is when the C partition is loaded. If the user does not know about the architecture in LUMI running batch jobs can be quite a headache. For modules to be detected during batch jobs, they should always installed in the correct partition. The two common alternatives would be the C and G partitions. C stands for CPU (serial) jobs and G for GPU (parallell computing) jobs. Since SUMO does not support parallell computing (except for its pathfinding processes) the C partition is a suitable alternative. When running batch jobs, the same partition that SUMO has been installed in should always be loaded.

## Example batch job
The following batch job can be used to test if SUMO has been installed correctly and works in LUMI, assuming there is a directory called `sumo_simulation` containing a .sumocfg file with the needed files.

```
#!/bin/bash
#SBATCH --job-name=loading_sumo
#SBATCH --account=<PROJECT_ID>
#SBATCH --time=00:01:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --partition=small
#SBATCH -o loading_sumo.txt

export START_DIR="/scratch/<PROJECT_ID>/sumo_simulation"
cd $START_DIR

# rm -r ~/.lmod.d
module load LUMI/22.08 partition/C
# module load LUMI/22.08
# module load EasyBuild-user
# module spider python
module load cray-python/3.9.13.1
module spider Xerces
module load Xerces-C++/3.2.4-cpeGNU-22.08
module use /scratch/<PROJECT_ID>/SUMO_modules/
# module spider sumo
module load sumo
# module load Xerces-C++/3.2.4-cpeGNU-22.08
sumo LUMI_test.sumocfg
```