<a name="readme-top"></a>

<h3 align="center">Kamppi mini demo</h3>

  <p align="center">
    "A simulation demo for the AIForLEssAuto project"
  </p>
</div>


<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#structure">Structure</a></li>
    <li><a href="#license">License</a></li>
  </ol>
</details>

## About The Project

* Title: Kamppi mini demo
* Description: A simulation mini demo for the AIForLEssAuto project. AIForLEssAuto is a multi-disciplinary project funded by the Research Council of Finland that investigates novel city planning strategies aiming to minimize carbon dioxide emissions. In this demo, Simulation For Urban MObility (SUMO) software is used to simulate traffic and carbon dioxide emissions in Kamppi, Helsinki.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Getting started

### Installation

1. Check the prerequisites
2. Clone the repository
3. Run `sh commands.sh` in the command line in the root folder and follow the instructions
4. Success!

### Prerequisites

* #### Python 3.9.x or later and sumolib tools

Download the latest Python from [Python's official website](https://www.python.org/downloads/). Anaconda or Pip are both fine as package installers. Then, install [the sumolib tools](https://sumo.dlr.de/docs/Tools/Sumolib.html) in the Python packages using your preferred package installer.

* #### Simulation for Urban MObility (SUMO)

Follow the installation instructions from [SUMO's official website.](https://www.eclipse.org/sumo/)

* #### Git for Windows, if using Windows

Download the latest Git for Windows from [Git's official website](https://gitforwindows.org/).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Structure

The repository is partitioned into the following files:

* The `simulation_output` folder contains the excerpted outputs from the simulation: observed emissions and teleports per timestep and a plot of the road network used in the simulation.
* `commands.sh` contains the command line script used to run the pipeline as a whole.
* `LICENSE` contains the info about the license this project is distributed under.
* `confirmContinue.py` is a script used to modidy the parameters for different scenarios while running the demo.
* `test_fcdresults.xml` is the full vehicle-level output of the simulation.
* `emissionOutputSwitcher.py` is the script that calculates emissions according to the modified vehicle parameters without running the simulation anew.
* `kamppi.net.xml` is the road network used in the simulation.
* `outputPlots.py` is used to plot the results of the simulation.
* `trafficCreator.py` is used to create traffic inside the simulation. The file takes as an argument the number of simulated vehicles.
* The files with `Traci_demo` -prefix are used to configure TraCI to run SUMO and produce the results of the simulation. The `TraCI_demo.py` takes as arguments the option to run SUMO via GUI and the suffix of the teleport output file.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage

The picture `Kamppi_demo.png` in the repository shows the plots produced by the pipeline.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## License

Distributed under the MIT License. See the `LICENSE` -file for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>
