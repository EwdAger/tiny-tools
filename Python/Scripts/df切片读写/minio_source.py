# -*- coding: utf-8 -*-
import json
import logging
import os
import pickle
import shutil
from typing import List

import pandas as pd

from app.config import common
from app.config import setting
from app.models.base import db
from multi_analysis_tasks import celery_app
from tools.tick_tock import time_it


class MfaSourceSplit:
    def __init__(self, user_name, file_name, file_type='csv'):
        self.user_name = user_name
        self.file_name = file_name
        self.file_type = file_type

    @property
    def save_path(self):
        if self.file_type == 'csv':
            return 'data/mfa-source/{}/csv/{}'.format(self.user_name, self.file_name)
        else:
            return 'data/mfa-source/{}/xls/{}'.format(self.user_name, self.file_name)

    @property
    def dict_file(self):
        return self.save_path + '/dict.pkl'

    def delete_data(self):
        shutil.rmtree(self.save_path)

    def save_dict_data(self, data):
        with open(self.dict_file, 'wb') as f:
            f.write(pickle.dumps(data))

    def read_dict_data(self):
        with open(self.dict_file, 'rb') as f:
            data = f.read()
        return pickle.loads(data)

    def df_path(self, rows_split_count=0):
        result = self.save_path + '/{}'.format(rows_split_count)
        if not os.path.exists(result):
            os.makedirs(result)
        return result

    def df_file(self, rows_split_count=0, columns_split_count=0):
        return self.save_path + '/{}/{}_df.pkl'.format(rows_split_count, columns_split_count)

    @staticmethod
    def cal_start_end(total_size, chunk_size, start=0, end=None):
        if end is None or end >= total_size:
            end = total_size
        chunk_start = int(start / chunk_size)
        chunk_end = int(end / chunk_size)

        result_start = int(start) % int(chunk_size)
        result_end = (chunk_end - chunk_start) * chunk_size + int(end) % int(chunk_size)
        if int(end) % int(chunk_size) != 0:
            chunk_end += 1
        return chunk_start, chunk_end, result_start, result_end

    def csv_write_to_split(self, origin_path):
        data = pd.read_csv(origin_path, chunksize=10)
        chunk_num = 20000 * 500
        columns_count = 10
        rows_count = 0
        split_count = 0

        columns_list = []
        for chunk in data:
            columns_list = chunk.columns.to_list()
            columns_count = chunk.shape[1]
            break

        chunk_size = int(chunk_num / columns_count)

        data = pd.read_csv(origin_path, chunksize=chunk_size, na_values=common.NAN_LIST)

        path = self.save_path
        if not os.path.exists(path):
            os.makedirs(path)
        for chunk in data:
            rows_count += chunk.shape[0]
            self.df_path(split_count)

            # for i in range(int(columns_count / 500)):
            i = 0
            while i * 500 < columns_count:
                end_columns_num = (i + 1) * 500
                if end_columns_num > columns_count:
                    end_columns_num = columns_count
                chunk.iloc[:, i * 500:end_columns_num].to_pickle(self.df_file(split_count, i))
                i += 1
            split_count += 1

        self.save_dict_data({'columns_list': columns_list,  # 列头
                             'rows_count': rows_count,  # 总行数
                             'columns_count': columns_count,  # 总列数
                             'rows_chunk_size': chunk_size,  # 块行数
                             'columns_chunk_size': int(500)  # 块列数
                             })

        return rows_count, columns_count, split_count

    @time_it
    def read_csv_split_pkl(self, rows_start: int = 0, rows_end: int = None,
                           column_start: int = 0, column_end: int = None):

        dict_data = self.read_dict_data()

        r_chunk_start, r_chunk_end, r_result_start, r_result_end = MfaSourceSplit.cal_start_end(
            dict_data['rows_count'],
            dict_data['rows_chunk_size'],
            rows_start,
            rows_end)
        c_chunk_start, c_chunk_end, c_result_start, c_result_end = MfaSourceSplit.cal_start_end(
            dict_data['columns_count'],
            dict_data['columns_chunk_size'],
            column_start,
            column_end)
        rows_df = []
        for rows_num in range(r_chunk_start, r_chunk_end):
            columns_df = [pd.read_pickle(self.df_file(rows_num, x)) for x in range(c_chunk_start, c_chunk_end)]
            rows_df.append(pd.concat(columns_df, axis=1))
        result_df = pd.concat(rows_df)

        return result_df.iloc[r_result_start:r_result_end, c_result_start:c_result_end]

    def read_csv_pkl_rows_index(self, rows_list: List):

        if not isinstance(rows_list, list):
            raise TypeError('rows_list 为列表')
        rows_list = list(set(rows_list))
        rows_list.sort()
        dict_data = self.read_dict_data()
        rows_data = {}
        c_chunk_start, c_chunk_end, c_result_start, c_result_end = MfaSourceSplit.cal_start_end(
            dict_data['columns_count'],
            dict_data['columns_chunk_size'])

        for row in rows_list:
            r_chunk_start, r_chunk_end, r_result_start, r_result_end = MfaSourceSplit.cal_start_end(
                dict_data['rows_count'],
                dict_data['rows_chunk_size'],
                row,
                row + 1)
            if not rows_data.get(r_chunk_start):
                rows_data[r_chunk_start] = []
            rows_data[r_chunk_start].append(r_result_start)

        rows_df = []
        for rows_num, index_list in rows_data.items():
            columns_df = [pd.read_pickle(self.df_file(rows_num, x)) for x in range(c_chunk_start, c_chunk_end)]
            rows_df.append(pd.concat(columns_df, axis=1).iloc[index_list, :])
        result_df = pd.concat(rows_df)

        return result_df

    def xls_write_to_split(self, origin_path):
        sheet_columns = {}
        df = pd.read_excel(origin_path, sheet_name=None, engine='xlrd', convert_float=False, na_values=common.NAN_LIST)
        sheet_names = list(df.keys())
        for i in range(len(sheet_names)):
            sheet_columns.update({sheet_names[i].replace(".", ""): list(df[sheet_names[i]].columns)})
            if "." in sheet_names[i]:
                df[sheet_names[i].replace(".", "")] = df[sheet_names[i]]
                df.pop(sheet_names[i])
            sheet_names[i] = sheet_names[i].replace(".", "")

        path = self.save_path
        if not os.path.exists(path):
            os.makedirs(path)

        self.df_path()
        with open(self.df_file(), 'wb') as f:
            f.write(pickle.dumps(df))

        self.save_dict_data(sheet_columns)

        return sheet_columns, df[sheet_names[0]].shape[0]

    def read_xls_split_pkl(self):
        dict_data = self.read_dict_data()
        with open(self.df_file(), 'rb') as f:
            df_data = f.read()
        df_data = pickle.loads(df_data)
        return dict_data, df_data


@celery_app.task(queue='source_data', ignore_result=True)
def task_spit_save(data_id: int):
    from app.models.user_basic_data import UserMinioData

    mini_data = UserMinioData.query.get(data_id)
    if not mini_data:
        raise ValueError('data_id: {}'.format(data_id))

    try:
        mfa_source = MfaSourceSplit(mini_data.user.username, mini_data.id, mini_data.file_type)
        if mini_data.file_type == 'csv':
            rows_count, columns_count, split_count = mfa_source.csv_write_to_split(mini_data.data_file)
            mini_data.rows = rows_count
            mini_data.cols = columns_count
            mini_data.split_num = split_count
        else:
            sheet_columns, rows = mfa_source.xls_write_to_split(mini_data.data_file)
            mini_data.sheet_name = json.dumps([x[0] for x in sheet_columns.items()])
            mini_data.cols = sum([len(x[1]) for x in sheet_columns.items()])
            mini_data.rows = rows
        mini_data.status = 1
    except Exception as e:
        logging.exception('task_spit_save:')
        mini_data.status = 8

    db.session.commit()
