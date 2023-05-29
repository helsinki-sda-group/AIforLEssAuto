# UH HPC SUMO manual

## Explanation of the title

UH = University of Helsinki

HPC = High Performance Computing service

SUMO = Simulation of Urban MObility

## Intro

This manual guides the user through setting up the traffic simulator SUMO in the HPC cluster at the University of Helsinki. It will involve importing the needed modules and compiling SUMO in the HPC cluster. The steps in this guide roughly follow the instructions on the [HPC instruction page](https://wiki.helsinki.fi/pages/viewpage.action?pageId=250101610#FAQ&ScientificSoftwareUseCases-7.0SUMO).

## The guide

First, log into the HPC cluster.

```
ssh -YA <USER>@turso.cs.helsinki.fi
```

Then, export some environment variables.
```
export WORK=/wrk-vakka/users/<USER>
export SUMO_HOME="$PROJ/sumo"
```

Load the needed modules. The version that was used in 2023 was 11.2.0 to avoid conflicts between the modules.
```
module purge
module load Python/3.9.6-GCCcore-11.2.0
module load GDAL/3.3.2-foss-2021b
module load X11/20210802-GCCcore-11.2.0
module load Mesa/21.1.7-GCCcore-11.2.0
module load libGLU/9.0.2-GCCcore-11.2.0
module load cmake/3.21.3
module load Xerces-C++/3.2.3-GCCcore-11.2.0
```

Create a Python virtual environment.
```
cd $PROJ
python -m venv my_venv
source $WORK/my_venv/bin/activate
pip install -U pip
```

Reserve resources. This step might not be necessary and compiling the programs may work just fine on the login nodes.
```
srun --interactive -c4 --mem=4G -t4:00:00 -pshort -Mukko --pty bash
```
You can always (and SHOULD!) free up the resources when you don't need them by using the command
```
exit
```

Install Foxtools (a tool needed for compiling SUMO)
```
wget http://fox-toolkit.org/ftp/fox-1.7.81.tar.gz
tar xvf fox-1.7.81.tar.gz
cd fox-1.7.81/
mkdir $PROJ/executables
./configure --prefix $PROJ/executables
make install
# (OR make ?)
```

Install SUMO
```
cd $PROJ
git clone https://github.com/eclipse/sumo
cd sumo
git fetch origin refs/replace/*:refs/replace/*
export SUMO_HOME="$PROJ/sumo"
mkdir build/cmake-build
cd sumo/build/cmake-build
cmake ../..
make -f Makefile
make install
```

Create a SUMO module
```
cd $PROJ
mkdir $PROJ/MyModules
mkdir $PROJ/SUMO
mkdir $PROJ/SUMO/1.15.0
mkdir $PROJ/SUMO/1.15.0/bin
cp $PROJ/sumo/bin/sumo $PROJ/SUMO/1.15.0/bin
mkdir MyModules
```


In $PROJ/MyModules, paste the following into a file named sumo.lua:
```
help ([[For detailed instructions, go to:
 https://wiki.helsinki.fi/pages/viewpage.action?pageId=250101610#FAQ&ScientificSoftwareUseCases-7.0SUMO
]])

whatis("Version: 1.15.0")
whatis("Keywords: Traffic simulation")
whatis("URL: https://www.eclipse.org/sumo/")
whatis("Description: SUMO (Simulation of Urban MObility) is an open source traffic simulator. This is a custom module created in November 2022 by Anton Taleiko for use in the research group Spatiotemporal Data Analysis at the University of Helsinki.")

setenv(       "HELLOPATH",        "/proj/<USER>/SUMO/1.0.0/bin")
prepend_path( "PATH",           "/proj/<USER>/SUMO/1.0.0/bin")
prepend_path( "LD_LIBRARY_PATH","/proj/<USER>/SUMO/1.0.0/lib")
```

Then, to use the module (or rather, all your own modules)
```
module use $PROJ/MyModules
# After that your own SUMO module should show up with
module --ignore_cache avail
# and can be loaded with
module load sumo
```

## Creating modules for shared use

If you install modules in your research group's shared directory you can create a directory there and include it in places to look for modules in. The process would be the same, but instead of installing the modules in `$PROJ/MyModules` you should create an environment variable

```
export GROUP=/proj/group/<YOUR_GROUP>
```
and create the module in that directory. Then everyone in your group can load the module with

```
module use $GROUP/HPCModules
```

## Note about parallell pathfinding

For some reason SUMO's pathfinding tool Duarouter complains about that parallell computing is only available when SUMO is compiled with Fox. This can lead to bottlenecks when doing pathfinding and it could be good to find out why this happens.

# Links and other things that might be of help

The path to your research group's directory

`/proj/group/<YOUR_GROUP>`

Show info about a module
```
module show MODULE_NAME
```

Creating modules:\
https://wiki.helsinki.fi/display/it4sci/Module+System

VDI Turso (graphical user interface for the HPC service)\
https://vdi.helsinki.fi/

Saving subsets of modules
```
module save sumo
module purge
module restore sumo
````

For refreshing when searching for new modules:
```
module spider --ignore-cache
```

GDAL 3.3.2-foss-2021b

Show available modules and ignore cache
```
module --ignore_cache avail
```

parallel computing: xtht

Useful links:

Modules:\
https://wiki.helsinki.fi/display/it4sci/Module+System

HPC environment user guide:\
https://wiki.helsinki.fi/display/it4sci/HPC+Environment+User+Guide