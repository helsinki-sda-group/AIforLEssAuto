# AIforLEssAuto

This repository contains the code of the algorithms and tools developed in Work Package 4 of Artificial Intelligence for Urban Low-Emission Autonomous Traffic (AIForLEssAuto) project.

[The webpage of the project](https://www.helsinki.fi/en/researchgroups/spatiotemporal-data-analysis/research/aiforlessauto)

Repositories:

[SUMO Helsinki traffic model](https://github.com/helsinki-sda-group/AIforLEssAuto/tree/main/WP4/sumo-hki-cm) — pipeline of demand estimation and calibration for SUMO micro-simulation traffic model of Helsinki city area. 

The input data are: (i) origin-destination (OD) matrices for traffic assignment zones (TAZs) covering whole Finland from [HSL Helmet model](https://github.com/HSLdevcom/helmet-ui), <br>(ii) Digitraffic traffic counts from traffic counting stations located within Helsinki. The pipeline consists of two steps: (i) OD matrix reduction (for smaller area, for example, Helsinki metropolitan area), (ii) route calibration with traffic counts as ground-truth data ([manuscript](https://helda.helsinki.fi/server/api/core/bitstreams/d4c94679-10e3-48e8-aa50-ade838cb2ab6/content), please cite as <i>Bochenina, K., Taleiko, A., & Ruotsalainen, L. (2023, June). Simulation-based origin-destination matrix reduction: a case study of Helsinki city area. In SUMO User Conference (pp. 1-13)</i>). SUMO network and route files for Helsinki and three (nested within each other) smaller areas, resulting from the pipeline, are available at [demo folder](https://github.com/helsinki-sda-group/AIforLEssAuto/tree/main/WP4/sumo-hki-cm/demo). 
