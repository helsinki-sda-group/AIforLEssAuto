import json
from scipy.stats import shapiro
import matplotlib.pyplot as plt
from numpy.random import normal
from statsmodels.graphics.gofplots import qqplot
import statsmodels.api as sm
import numpy as np
from scipy import stats
import sys
from datetime import datetime
from typing import Tuple

def main():
    with open('WP4/sumo-hki-cm/calibration/data/road_station_detections_daily.json', 'r') as file:
        data = json.load(file)

    # a = normal(size=50)
    # s, p = shapiro(a)
    # print(s, p)

    # plt.figure(figsize=(10,6))
    # plt.hist(a, bins='auto', color='blue')
    # plt.title(f"Histogram for a")
    # plt.show()

    for detector in data:
        dates_counts = data[detector]
        dir1 = []
        dir2 = []


        for date in dates_counts:
            date_count = dates_counts[date]
            morning_count = date_count["morning"]
            date = date[5:]

            dir1_count = morning_count["dir1"]
            if dir1_count > 0:
                dir1.append((dir1_count, date))

            dir2_count = morning_count["dir2"]
            if dir2_count > 0:
                dir2.append((dir2_count, date))
            
        print(f'\n{detector}')
        
        visualize_counts(dir1, detector, "DIR_1")
        visualize_counts(dir2, detector, "DIR_2")


        # dir1
        

        # # dir2
        # if len(dir2) == 0:
        #     print(f'skipped dir2 for detector {detector}')
        #     continue
        # dir2_stat, dir2_p = shapiro(dir2)
        # dir2_mean = np.mean(dir2)
        # print('DIR_2')
        # print(dir2_stat, dir2_p)

        # date_is_labeled = [False] * len(dir1)
        # fig, ax = plt.subplots(figsize=(10,6))
        # qqplot(np.array(dir2), line='s', ax=ax)
        # plt.title(f"Q-Q Plot for DIR2")
        # xdata, ydata = ax.get_lines()[0].get_data()
        # for i, (x, y) in enumerate(zip(xdata, ydata)):
        #     # find the count associated with the point
        #     for j, (c, d) in enumerate(zip(dir2, dates)):
        #         if c == y and not date_is_labeled[j]:
        #             date_is_labeled[j] = True
        #             ax.annotate(d, (x, y), fontsize=6, ha='right')
    

        # plt.figure(figsize=(10,6))
        # plt.axvline(dir2_mean, color='black', linestyle='dashed', linewidth=1)
        # plt.hist(dir2_counts, bins='auto', color='red')
        # plt.title(f"Histogram for DIR2")
        


def visualize_counts(counts_dates_tuple: Tuple[int, str], detector:str, dir:str):
    
    counts = [x[0] for x in counts_dates_tuple]

    if len(counts) == 0:
        return
    
    dates_strs = [x[1] for x in counts_dates_tuple]
    parsed_dates = [datetime.strptime(date_str, "%m_%d") for date_str in dates_strs]
    min_date = min(parsed_dates)
    date_differences = [(date - min_date).days for date in parsed_dates]

    if len(counts_dates_tuple) == 0:
        print(f'skipped dir for detector {detector}')
        return
    # dir1_stat, dir1_p = shapiro(dir1_counts)
    # dir1_mean = np.mean(dir1_counts)
    # print('DIR_1')
    # print(dir1_stat, dir1_p)

    # plt.figure(figsize=(10,6))
    # plt.axvline(dir1_mean, color='black', linestyle='dashed', linewidth=1)
    # plt.hist(dir1_counts, bins='auto', color='blue')
    # plt.title(f"Histogram for DIR1")

    # q-q plot
    count_is_labeled = dict.fromkeys(dates_strs, False)
    fig, (ax1, ax2) = plt.subplots(1, 2,figsize=(12,6))
    qqplot(np.array(counts), line='s', ax=ax1)
    plt.title(f"Q-Q Plot for {dir}")
    xdata, ydata = ax1.get_lines()[0].get_data()
    for x, y in zip(xdata, ydata):
        # find the count associated with the point
        for dir_info in counts_dates_tuple:
            c = dir_info[0]
            d = dir_info[1]
            if c == y and not count_is_labeled[d]:
                count_is_labeled[d] = True
                ax1.annotate(d, (x, y), fontsize=8, ha='right')
                break

    # scatter plot
    count_is_labeled = dict.fromkeys(dates_strs, False)
    scat = ax2.scatter(date_differences, np.array(counts))
    ax2.set_title(f'Scatter plot for {dir}')
    scat_data = scat.get_offsets()
    xdata = [x[0] for x in scat_data]
    ydata = [x[1] for x in scat_data]
    for x, y in zip(xdata, ydata):
        # find the count associated with the point
        for dir_info in counts_dates_tuple:
            c = dir_info[0]
            d = dir_info[1]
            if c == y and not count_is_labeled[d]:
                count_is_labeled[d] = True
                ax2.annotate(d, (x, y), fontsize=8, ha='right')
                break

    plt.get_current_fig_manager().window.showMaximized()
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    sys.exit(main())