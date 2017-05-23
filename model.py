# coding: utf-8
# pylint: disable=C0103, C0111,C0326
import scipy as sp
# import lightgbm as lgb
import pandas as pd
import numpy as np
import xgboost as xgb
import time

from sklearn.preprocessing import StandardScaler
from sklearn.utils import shuffle
from sklearn import grid_search
<<<<<<< HEAD
from sklearn.ensemble import RandomForestClassifier,RandomForestRegressor, GradientBoostingRegressor
from sklearn.cross_validation import train_test_split
from sklearn.linear_model import LogisticRegression
=======
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
>>>>>>> cf7614174911050901aae414c1a33f6bf3eaddcf

from data import *
from feature import *
import os

submit_flag = True


def logloss(act, pred):
    epsilon = 1e-15
    pred = sp.maximum(epsilon, pred)
    pred = sp.minimum(1 - epsilon, pred)
    ll = sum(act * sp.log(pred) + sp.subtract(1, act) * sp.log(
        sp.subtract(1, pred)))
    ll = ll * -1.0 / len(act)
    print '-------------logloss-----------', ll
    return ll


def feature_select(x, y, pre_x, rate=0.2):
<<<<<<< HEAD
    # RF(x, y, pre_x)
=======
    if not os.path.exists('importances.csv'):
        RF(x, y, pre_x)
>>>>>>> cf7614174911050901aae414c1a33f6bf3eaddcf
    df = pd.read_csv('importances.csv')
    importances = df.imp
    indices = np.argsort(importances)[::-1]
    print 'select indices: '
    print indices
    n = int(len(indices) * rate)
    x = x[:, indices[0:n]]
    pre_x = pre_x[:, indices[0:n]]
    return x,  pre_x


def threshold(y, thresh=0.005, val = 1e-6):
    y[y<=thresh] = val
    return y


def submit(y, inst):
    y[y < 0] = 0
    now = time.strftime('%Y%m%d%H%M%S')
    data = pd.DataFrame(inst, columns=['instanceID'])
    data['prob'] = y
    data.instanceID = np.round(data.instanceID).astype(int)
    data = data.sort(['instanceID'], ascending = True)
    data.to_csv('../res/'+now+'.csv', index=False)



def RF(x, y, pred_x):
    """
    随机森林，计算特征重要性
    """
    print '----rf-----'
    print x.shape
    print pred_x.shape

    posnum = y[y == 1].shape[0]
    negnum = y[y == 0].shape[0]
    print 'pos:', posnum, ' neg:', negnum
    weight = float(posnum) / (posnum + negnum)
    print 'weight:', weight

    xtrain, xvalid, ytrain, yvalid = train_test_split(
        x, y, test_size=0.2, random_state=0)

    clf = RandomForestClassifier(n_estimators=500,
                                 max_depth=6,
                                 random_state=500,
                                 class_weight={1: weight},
                                 n_jobs=8)\
        .fit(xtrain, ytrain)

    importances = clf.feature_importances_
    indices = np.argsort(importances)[::-1]
    print indices
    print importances[indices]

    imp = pd.DataFrame(importances, columns=['imp'])
    imp.to_csv('importances.csv', index=False)

    test_pred = clf.predict_proba(xvalid)
    logloss(yvalid, test_pred[:, 1])
    pred = clf.predict_proba(pred_x)
    return pred[:, 1], indices


def XGB(x, y, pre_x):
    print '----xgb-----'
<<<<<<< HEAD
    p_x = pre_x
    x, pre_x = feature_select(x, y, p_x, rate=0.1)
=======
    x, pre_x = feature_select(x, y, pre_x, rate=0.8)
>>>>>>> cf7614174911050901aae414c1a33f6bf3eaddcf
    print x.shape
    print pre_x.shape

    posnum = y[y == 1].shape[0]
    negnum = y[y == 0].shape[0]
    print 'pos:', posnum, ' neg:', negnum

    weight = float(posnum) / (posnum + negnum)
    print 'weight:', weight

    xtrain, xvalid, ytrain, yvalid = train_test_split(
        x, y, test_size=0.2, random_state=0, stratify=y)

    if not submit_flag:
        xtrain, xtest, ytrain, ytest = train_test_split(
            xtrain, ytrain, test_size=0.2, random_state=0)
        dtest = xgb.DMatrix(xtest, label=ytest, missing=-1)

    dtrain = xgb.DMatrix(xtrain, label=ytrain, missing=-1)
    dvalid = xgb.DMatrix(xvalid, label=yvalid, missing=-1)

    dpre = xgb.DMatrix(pre_x)
    param = {
        'booster': 'gbtree',
        'objective': 'binary:logistic',
        'early_stopping_rounds': 100,
        'eval_metric': 'logloss',
        'max_depth': 6,
        'silent': 1,
        'eta': 0.05,
        'nthread': 16,
        'scale_pos_weight': weight
    }
    watchlist = [(dtrain, 'train'), (dvalid, 'val')]
    model = xgb.train(param, dtrain, num_boost_round=200, evals=watchlist)

    # valid
    valid_pre = model.predict(dvalid, ntree_limit=model.best_iteration)
    logloss(yvalid, valid_pre)

    if not submit_flag:
        test_pre = model.predict(dtest, ntree_limit=model.best_iteration)
        logloss(ytest, test_pre)

    # predict
    pre_y = model.predict(dpre, ntree_limit=model.best_iteration)

    return pre_y


def deep_and_wide(X, y):
    pass

def save_pred(ypre, inst):
    df = pd.DataFrame({'instanceID':inst, 'prob':ypre})
    df.to_csv('submission.csv', index=False)

def LR(x, y, pre_x):
    print '----LR-----'
    p_x = pre_x
    x, pre_x = feature_select(x, y, p_x, rate=0.1)
    print x.shape
    print pre_x.shape

    posnum = y[y == 1].shape[0]
    negnum = y[y == 0].shape[0]
    print 'pos:', posnum, ' neg:', negnum

    weight = float(posnum) / (posnum + negnum)
    print 'weight:', weight

    xtrain, xvalid, ytrain, yvalid = train_test_split(
        x, y, test_size=0.2, random_state=0)

    if not submit_flag:
        xtrain, xtest, ytrain, ytest = train_test_split(
            xtrain, ytrain, test_size=0.2, random_state=0)
        dtest = xgb.DMatrix(xtest, label=ytest, missing=-1)

    sc = StandardScaler()
    sc.fit(xtrain)  # 估算每个特征的平均值和标准差
    X_train_std = sc.transform(xtrain)
    # 注意：这里我们要用同样的参数来标准化测试集，使得测试集和训练集之间有可比性
    X_valid_std = sc.transform(xvalid)

    model = LogisticRegression()
    model.fit(X_train_std, ytrain)

    # valid
    valid_pre = model.predict_proba(X_valid_std)
    logloss(yvalid, valid_pre[:, 1])

    if not submit_flag:
        test_pre = model.predict(dtest)
        logloss(ytest, test_pre)

    # predict
    pre_y = model.predict(pre_x)

    return pre_y


def LGB(x, y, pre_x):
    x, pre_x = feature_select(x, y, pre_x, rate=0.1)
    print '----lightgbm-----'
    print x.shape
    print pre_x.shape

    posnum = y[y == 1].shape[0]
    negnum = y[y == 0].shape[0]

    print 'pos:', posnum, ' neg:', negnum
    weight = float(posnum) / (posnum + negnum)
    print 'weight:', weight

    xtrain, xvalid, ytrain, yvalid = train_test_split(
        x, y, test_size=0.2, random_state=0)

    if not submit_flag:
        xtrain, xtest, ytrain, ytest = train_test_split(
            xtrain, ytrain, test_size=0.2, random_state=0)

    lgb_train = lgb.Dataset(xtrain, ytrain)
    lgb_eval = lgb.Dataset(xvalid, yvalid, reference=lgb_train)

    params = {
        'boosting_type': 'gbdt',
        'objective': 'binary',
        'metric': 'binary_logloss',
        'learning_rate': 0.05,
        'feature_fraction': 0.5,
        'is_unbalance': True,
        'scale_pos_weight': weight,
        'max_depth': 6,
        'verbose': -1,
        'num_threads': 16
    }

    #feature_name = ['feature_' + str(col) for col in range(num_feature)]

    print '----start training----'

    gbm = lgb.train(params,
                    lgb_train,
                    num_boost_round=500,
                    valid_sets=lgb_eval)

    # gbm.save_model('gbm_model.txt')

    #bst = lgb.Booster(model_file='gbm_model.txt')

    valid_pre = gbm.predict(xvalid, num_iteration=gbm.best_iteration)
    print '-----valid-----'
    valid_pre = threshold(valid_pre)
    logloss(yvalid, valid_pre)

    if not submit_flag:
        print '-----------test----------'
        test_pre = gbm.predict(xtest, num_iteration=gbm.best_iteration)
        logloss(ytest, test_pre)
        #logloss(ytest, threshold(test_pre, thresh=0.0005, val = 0))
        '''
        print test_pre[test_pre < 0.001].shape
        print '-----test-----'
        logloss(ytest, threshold(test_pre, val = 1e-4))
        logloss(ytest, threshold(test_pre, val = 1e-3))
        logloss(ytest, threshold(test_pre, val = 0.0005))
        logloss(ytest, threshold(test_pre, val = 0.001))
        logloss(ytest, threshold(test_pre, val = 0.001))
        logloss(ytest, threshold(test_pre, val = 1e-5))
        logloss(ytest, threshold(test_pre, val = 1e-6))
        logloss(ytest, threshold(test_pre, val = 1e-7))
        logloss(ytest, threshold(test_pre, val = 1e-8))
        logloss(ytest, threshold(test_pre, val = 1e-5))
        logloss(ytest, threshold(test_pre, thresh=0.004, val = 1e-5))
        logloss(ytest, threshold(test_pre, thresh=0.004, val = 1e-5))
        logloss(ytest, threshold(test_pre, thresh=0.003, val = 1e-5))
        logloss(ytest, threshold(test_pre, thresh=0.003, val = 1e-6))
        logloss(ytest, threshold(test_pre, thresh=0.003, val = 1e-7))
        '''

    y_pre = gbm.predict(pre_x, num_iteration=gbm.best_iteration)

    return y_pre

def save_pred(ypre, inst):
    df = pd.DataFrame({'instanceID':inst, 'prob':ypre})
    df.to_csv('submission.csv', index=False)

if __name__ == '__main__':
    x, y, xpre, inst = load_feature(from_file=True, with_ohe=False)
    # xgboost
    ypre = LGB(x, y, xpre)
    save_pred(ypre, inst)
    # ypre = XGB(x, y, xpre)

    # random forest
    # ypre = rfpredict(x, y, xpre)
