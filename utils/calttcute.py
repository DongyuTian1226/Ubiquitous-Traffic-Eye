# -*- encoding: utf-8 -*-
'''
Filename         :calttcute.py
Description      :
Time             :2024/05/16 18:58:26
Author           :Ku-Buqi
Version          :1.0
'''


import pandas as pd
import os


class CalTTC:
    def __init__(self, file_path, out_path, minttc_path, param_dict):
        self.file_dir = file_path
        self.out_file_dir = out_path
        self.minttc_dir = minttc_path
        self.laneid = param_dict[laneid]
        self.carid = param_dict[carid]
        self.time = param_dict[time]
        self.longitude = param_dict[longitude]
        self.carlength = param_dict[carlength]
        self.speed = param_dict[speed]

    def addttc(self, file_path, out_file_path):
        """

        Arguments
        ---------
        file_path : str
        out_file_path : str


        """

        datax = pd.read_csv(file_path)
        results = []
        datax.sort_values(by=[self.laneid, self.time, self.longitude], inplace=True)
        for lane, data_lane in datax.groupby(datax[self.laneid]):
            logo_car = data_lane.iloc[0][carid]
            logo_data_1 = data_lane.loc[data_lane[self.carid] == logo_car,
                                        self.longitude].iloc[0]
            logo_data_2 = data_lane.loc[data_lane[self.carid] == logo_car,
                                        self.longitude].iloc[-1]
            logo = logo_data_1 - logo_data_2
            for frame, data_frame in data_lane.groupby(data_lane[self.time]):
                ttc_sequence, followid = self.cal_ttc(
                    data_frame[self.longitude].values, data_frame[self.speed].values,
                    data_frame[self.carid].values, data_frame[self.carlength].values,
                    logo)
                data_frame["TTC"] = ttc_sequence
                data_frame["Followid"] = followid
                results.append(data_frame)
        modified_datax = pd.concat(results)
        modified_datax.to_csv(out_file_path, index=False)

    def cal_ttc(self, centerx, speed, id, carlength, logo):
        """

        Arguments
        ---------
        centerx : list
        speed : list
        ID : list
        carlength : list

        Returns
        -------
        ttc_sequence : list
        followid : list
        """

        if logo < 0:
            ttc_sequence = [10000]
            followid = [None]
            for i in range(1, len(centerx)):
                if speed[i] == 0 or speed[i - 1] <= speed[i]:
                    ttc_sequence.append(10000)
                else:
                    distance_to_clip = (centerx[i] - centerx[i - 1] -
                                        (carlength[i] + carlength[i - 1]) / 2)
                    speed_gap = speed[i - 1] - speed[i]
                    ttc = distance_to_clip / speed_gap
                    ttc_sequence.append(ttc)
                followid.append(id[i - 1])
        else:
            ttc_sequence = []
            followid = []
            for i in range(len(centerx) - 1):
                if speed[i] == 0 or speed[i] >= speed[i + 1]:
                    ttc_sequence.append(10000)
                else:
                    distance_to_clip = (centerx[i + 1] - centerx[i] -
                                        (carlength[i] + carlength[i + 1]) / 2)
                    speed_gap = speed[i + 1] - speed[i]
                    ttc = distance_to_clip / speed_gap
                    ttc_sequence.append(ttc)
                followid.append(id[i + 1])
            ttc_sequence.append(10000)
            followid.append(None)

        return ttc_sequence, followid

    def be_afttc(self, file_path, out_file_path):
        """

        Arguments
        ---------
        file_path : str
        out_file_path : str


        """

        before_ttc = []
        after_ttc = []

        df = pd.read_csv(file_path)
        for ID, grouped in df.groupby(self.carid):
            grouped.sort_values(by=[self.time])
            for i in range(len(grouped) - 1):
                if grouped.iloc[i][self.laneid] != grouped.iloc[i + 1][self.laneid]:
                    before_followid = grouped.iloc[i]['Followid']
                    after_followid = grouped.iloc[i + 1]['Followid']
                    before_min = grouped.loc[grouped['Followid']
                                             == before_followid, 'TTC'].min()
                    before_ttc.append(before_min)
                    after_min = grouped.loc[grouped['Followid']
                                            == after_followid, 'TTC'].min()
                    after_ttc.append(after_min)

        df_result = pd.DataFrame({'before_ttc': before_ttc,
                                  'after_ttc': after_ttc})
        df_result.to_csv(out_file_path, index=False)

    def traverse_folder(self):
        """

        Arguments
        ---------
        folder_path : str
        output_dir : str
        minttc_dir : str


        """

        # add 'TTC' column to the original data
        for root, dirs, files in os.walk(self.file_dir):
            for file in files:
                if file.endswith('.csv'):
                    file_path = os.path.join(root, file)
                    filename, extension = os.path.splitext(
                        os.path.basename(file_path))
                    out_file_path = os.path.join(self.out_file_dir,
                                                 f"{filename}_out.csv")
                    self.addttc(file_path, out_file_path)

        # calculate minTTC before and after lane change
        for root, dirs, files in os.walk(self.out_file_dir):
            for file in files:
                if file.endswith('.csv'):
                    file_path = os.path.join(root, file)
                    filename, extension = os.path.splitext(
                        os.path.basename(file_path))
                    min_file_path = os.path.join(self.minttc_dir,
                                                 f"{filename}_min.csv")
                    self.be_afttc(out_file_path, min_file_path)


if __name__ == '__main__':
    folder_path = r'E://UTEdata//alldata3'
    output_dir = r'E://UTEdata//try'
    minttc_dir = r'E://UTEdata//tryttc'
    param_dict = {
        'laneid': 'LaneID',
        'carid': 'VehicleID',
        'time': 'Time(s)',
        'longitude': 'x-axis position(m)',
        'carlength': 'VehicleLength(meter)',
        'speed': 'Speed(m/s)'
    }
    calttcute = CalTTC(folder_path, output_dir, minttc_dir, param_dict)
    calttcute.traverse_folder()
