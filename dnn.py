# coding: utf-8

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pandas as pd
import pickle
import numpy as np
import os
import math

from feature.data import *

from keras.layers import Concatenate, Conv1D, LocallyConnected1D, Dense, Dropout, Input, Embedding, concatenate
from keras.models import Sequential, Model
from keras.metrics import binary_accuracy
from keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import ModelCheckpoint, EarlyStopping, TensorBoard, ReduceLROnPlateau, Callback
from keras.utils import to_categorical

import tensorflow as tf
import loss

real_cvt_feats = []

real_cnt_feats = []

real_other = []

cate_low_dim = [
    'age',
    'appCategory',
    'appPlatform',
    'clickTime_day',
    'clickTime_hour',
    'clickTime_minute',
    'clickTime_week',
    'clickTime_seconds',
    'connectionType',
    'education',
    'gender',
    'haveBaby',
    'hometown_c',
    'hometown_p',
    'marriageStatus',
    'positionType',
    'telecomsOperator',
    'residence_c',
    'residence_p',
    'appID',
    'sitesetID',
]

cate_high_dim = [
    'adID',
    'advertiserID',
    'camgaignID',
    'creativeID',
    'positionID',
    'userID',
]

cate_feats = cate_high_dim + cate_low_dim
real_feats = real_cnt_feats + real_cvt_feats + real_other
drop_feats = []


class ColumnInfo(object):
    """
    每列信息类
    """

    def __init__(self, name, type, unique_size=None, dtype='int64'):
        """
        :param name: 列名
        :param type:  category or real
        :param max_value: 最大值
        :param dtype: 数据类型
        """
        self.name = name
        self.type = type
        self.unique_size = unique_size
        self.dtype = dtype

    def __str__(self):
        return 'name: {}, type: {}, max value: {}, dtype: {}'.format(
            self.name, self.type, self.max_value, self.dtype)


class PandasGenerator(object):
    """
    """

    def __init__(self, df_x, df_y, batch_size, infos):
        self.column_list = []
        for info in infos:
            self.column_list.append(info.name)

        self.df_x = pd.read_csv(df_x).loc[:, self.column_list]
        self.df_y = pd.read_csv(df_y)
        self.batch_size = batch_size

        self.length = self.df_x.shape[0]
        self.idx = 0

        if batch_size == 'all':
            self.batch_size = self.length

        if batch_size == 'auto':
            self.batch_size = self.max_batch_size()

        print(self.df_x.shape)
        print(self.df_y.shape)
        print(self.df_x.clickTime_day.unique())
        print(self.df_y.label.unique())

    def next(self):

        if self.idx + self.batch_size <= self.length:
            x = self.df_x.iloc[self.idx:(self.idx + self.batch_size), :].values
            y = self.df_y.iloc[self.idx:(self.idx + self.batch_size), :].values
            self.idx = self.idx + self.batch_size

        else:
            x1 = self.df_x.iloc[self.idx:self.length, :]
            y1 = self.df_y.iloc[self.idx:self.length, :]
            left = self.idx + self.batch_size - self.length
            _x = self.df_x.iloc[:left]
            _y = self.df_y.iloc[:left]

            x = pd.concat([x1, _x], axis=0).values
            y = pd.concat([y1, _y], axis=0).values
            self.idx = left

        print(np.max(y))
        print(x.shape)
        print(y.shape)
        inputs = np.split(x, x.shape[1], axis=1)
        outputs = to_categorical(y, 2)
        outputs = outputs[:, np.newaxis, :]

        weights = np.squeeze(y)
        weights[weights == 1] = 1 / 0.026  # sample weight
        weights[weights == 0] = 1

        return inputs, outputs, weights

    def __iter__(self):
        return self

    def __len__(self):
        return self.length

    def n_per_epoch(self):
        return np.ceil(self.length / float(self.batch_size))

    def label(self):
        return self.df_y.values

    def max_batch_size(self):
        i = 2
        for i in range(2, 100):
            if self.length % i == 0:
                break

        return self.length // i


class EvalCallback(Callback):
    def __init__(self, model, generator):
        super(EvalCallback, self).__init__()
        self.model = model
        self.generator = generator

    def on_epoch_end(self, epoch, logs=None):
        pred = self.model.predict_generator(self.generator, 1)
        print(pred.shape)
        ppred = np.squeeze(pred[:, :, 1])
        loss.logloss(np.squeeze(self.generator.label()), ppred)


def get_model(column_info_list,
              hidden_layers=[512, 256, 128],
              batch_size=10000):
    inputs = []
    real_inputs = []
    cate_inputs = []
    embeddings = []

    for column in column_info_list:
        if column.type == 'category':
            input = Input(
                shape=(1, ),
                dtype=column.dtype,
                name='input_{}'.format(column.name))
            emb = Embedding(
                output_dim=10,
                input_dim=column.unique_size + 1,
                input_length=1)(input)
            embeddings.append(emb)
            cate_inputs.append(input)

        elif column.type == 'real':
            input = Input(
                shape=(1, ),
                dtype=column.dtype,
                name='input_{}'.format(column.name))
            real_inputs.append(input)

        inputs.append(input)

    x = concatenate(embeddings + real_inputs)
    for layer_size in hidden_layers:
        x = Dense(layer_size, activation='sigmoid')(x)

    output = Dense(2, activation='softmax', name='output')(x)

    model = Model(inputs=inputs, outputs=output)

    model.summary()

    model.compile(
        optimizer='rmsprop',
        loss='binary_crossentropy',
        metrics=['accuracy', tf.losses.log_loss])

    gen_train = PandasGenerator('df_trainx.csv', 'df_trainy.csv', batch_size,
                                column_info_list)
    gen_test = PandasGenerator('df_testx.csv', 'df_testy.csv', 'auto',
                               column_info_list)

    callbacks = []
    callbacks.append(
        ModelCheckpoint(
            filepath='weights.{epoch:02d}-{val_loss:.2f}.hdf5',
            monitor='val_loss',
            period=1))

    callbacks.append(TensorBoard(log_dir='./logs', histogram_freq=1))
    callbacks.append(
        ReduceLROnPlateau(
            monitor='val_loss', factor=0.2, patience=5, min_lr=0.001))
    # callbacks.append(EvalCallback(model, gen_test))
    model.fit_generator(
        generator=gen_train,
        validation_data=gen_test,
        validation_steps=gen_test.n_per_epoch(),
        steps_per_epoch=10,
        callbacks=callbacks, )


def gen_column_list(df, save=True, save_name='column_list.pkl'):
    columns = df.columns.values
    infos = []
    for c in columns:
        print(c)
        if c in cate_feats and c not in drop_feats:
            df[c] = df[c].astype('int64')
            info = ColumnInfo(
                name=c,
                type='category',
                unique_size=df[c].max(),
                dtype='int64')

            infos.append(info)

        elif c in real_feats and c not in drop_feats:
            info = ColumnInfo(
                name=c,
                type='real',
                dtype=str(df[c].dtype),
                unique_size=None, )
            infos.append(info)

        else:
            print('unknow column')

    if save:
        pickle.dump(infos, open(save_name, 'wb'))

    return infos


def main():
    if os.path.exists('column_list.pkl'):
        infos = pickle.load(open('column_list.pkl', 'rb'))

    else:
        print("generate column list")
        df = pd.read_csv('df_basic_train.csv')
        del df['label']
        infos = gen_column_list(df)

    print('train....')
    get_model(infos, hidden_layers=[512, 256, 128], batch_size=10000)


# 31419479, 27)
# (31419479, 1)
# (6493437, 27)
# (6493437, 1)

if __name__ == '__main__':
    main()