#import scipy as sp
import numpy as np
np.set_printoptions(threshold=np.nan)
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import csv
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import GridSearchCV, PredefinedSplit
from sklearn.model_selection import ParameterGrid
import pandas as pd

if __name__ == '__main__':
    datafile = open('1kdata/1k_data.txt', 'r')
    samples = []
    for line in datafile:
        samples.append([float(i) for i in line.split()])
    del(samples[85])

    labelfile = open('1kdata/1k_labels.txt', 'r')
    pitch = []
    for line in labelfile:
        pitch.append([float(i) for i in line.split()])

    indicesToKeep = []
    #del(pitch[85])
    for i in range(0, len(pitch), 1):
        if pitch[i][2] == 1:
            if len(samples[i]) > 3:
                indicesToKeep.append(i)

    X = []
    y = []
    for i in indicesToKeep:
        X.append(samples[i])
        y.append(pitch[i][0])

    #print(len(max(X, key=len)))
    for i in range(0, len(X), 1):
        '''if len(X[i]) < 143:
            length = 143 - len(X[i])
            zeros = [0] * length
            X[i].extend(zeros)'''
        obs_height = -200
        obs_dist = 0
        for j in range(3, len(X[i]), 2):
            if obs_height < X[i][j+1]:
                obs_height = X[i][j+1]
                obs_dist = X[i][j]
        X[i] = [X[i][1], np.sqrt(((X[i][0])**2)+((X[i][2])**2)), obs_dist, obs_height]

    splitsize = int(len(X)*0.9)
    X_test = np.asarray(X[splitsize:])
    X_train = np.asarray(X[0:splitsize])
    y_test = np.asarray(y[splitsize:])
    y_train = np.asarray(y[0:splitsize])

    X = np.asarray(X)
    y = np.asarray(y)

    #print(X_train)
    #print(X_test)
    #X_train = np.delete(X_train,np.argmax(y_train),0)
    #y_train = np.delete(y_train, np.argmax(y_train), 0)
    '''
    fig0 = plt.figure()
    ax = fig0.add_subplot(111, projection='3d')
    ax.scatter(X[:,2], X[:,3], y, c='r')
    ax.set_xlabel('Target Distance')
    ax.set_ylabel('Target Height')
    ax.set_zlabel('Pitch')
    fig1 = plt.figure()
    ax2 = fig1.add_subplot(111, projection='3d')
    ax2.scatter(X[:, 2], X[:, 3], y, c='r')
    ax2.set_xlabel('Obs Distance')
    ax2.set_ylabel('Obs Height')
    ax2.set_zlabel('Pitch')
    plt.show()

    
    alphas = np.logspace(-2,3,24)
    for a in alphas:
        rlf = MLPRegressor(solver='lbfgs', hidden_layer_sizes=(100,100), activation='logistic', random_state=1, alpha=a, tol=1e-6)
        rlf.fit(X_train, y_train)
        pred = rlf.predict(X_test)
        res = np.stack((y_test, pred), axis=0)
        print('a: ' + str(np.log10(a)))
        print(rlf.score(X_test, y_test))

    
    tuples = []
    for i in range(1,10,1):
        tuples.append((i,))
        for j in range(1, 10, 1):
            tuples.append((i,j))
    alphas = []
    for i in np.arange(-2, 3, 0.2):
        alphas.append(10**i)

    #test_fold = [-1] * len(X_train) + [0] * len(X_test)  # 0 corresponds to test, -1 to train
    #predefined_split = PredefinedSplit(test_fold=test_fold)
    param_grid = [{
        'hidden_layer_sizes': tuples,
        'alpha': alphas
    }]

    gs = GridSearchCV(estimator=MLPRegressor(activation='logistic', tol=1e-6, solver='lbfgs', random_state=1), param_grid=param_grid)
    X = np.asarray(X)
    y = np.asarray(y)
    #print(X)
    #print(y)
    gs.fit(X, y)

    df = pd.DataFrame(gs.cv_results_)
    df.to_pickle('grid_search_results.pkl')
    
    '''
    rlf = MLPRegressor(solver='lbfgs', hidden_layer_sizes=(100,100), activation='logistic', random_state=1, alpha=10**(1.9130434782608696), tol=1e-6)
    #rlf = MLPRegressor(solver='lbfgs', hidden_layer_sizes=(9, 8), activation='logistic', random_state=1, alpha=0.0630957344480193, tol=1e-6)
    rlf.fit(X_train, y_train)
    pred = rlf.predict(X_test)
    score = []
    for i in range(0, len(y_test), 1):
        score.append((y_test[i] - pred[i])**2)
    score = np.asarray(score)
    res = np.stack((y_test.T, pred.T, score.T), axis=1)
    print('Actual pitch, Predicted pitch, Sq Loss')
    print(res)
    print('Score of model')
    print(rlf.score(X_test, y_test))
    print('Avg. Sq Loss')
    print(np.sum(score)/len(score))

