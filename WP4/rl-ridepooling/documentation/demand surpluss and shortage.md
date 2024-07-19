## AREA 1
Surplus and shortage of taxis for each config file

### area1_sampled_0.2.yaml (-pp 50 -pt 15)
surplus: till about 1200
shortage: till the end

### area1_sampled_0.4.yaml (-pp 50 -pt 15)
surplus: till about 1800
shortage: till the end

### area1_sampled_0.4.yaml (-pp 50 -pt 10)
surplus: till about 1400
shortage: till the end


I decided to make it 30 percent of taxis to speed up the simulation
Ratio taxis/passengers is the most important metric probably

area1 0.2 - smallest case
pp pt ratio result
30 15 7 clearly too much taxis
30 5 20 shortage from 800, shortage might be too big for the small number of taxis
30 5 10 shortage from 1800, seems to be fine

area1 0.4
rato 10 (pp 30 pt 10) seems a bit too much, shortage from 2000

area1 0.6 pp30 pt10 shortage from 1600

