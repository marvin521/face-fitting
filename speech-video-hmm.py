#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  4 15:02:36 2017

@author: leon
"""
from vol2mesh import Bunch, generateFace, exportObj
import os
import numpy as np
import librosa
from sklearn.neighbors import NearestNeighbors
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
from sklearn import metrics
from mayavi import mlab
from hmmlearn import hmm

os.chdir('/home/leon/f2f-fitting/trump2/')
numFrames = 3744 #2260
fps = 24

# Load audio tracks, pre-emphasize, and create feature vectors from mfcc, rmse, and deltas of mfcc
nfft = 1024
hopSamples = 512

wav_kuro, fs_kuro = librosa.load('kuro.wav', sr=44100)
wav_kuro = np.r_[wav_kuro[0], wav_kuro[1:] - 0.97 * wav_kuro[:-1]]
mfcc_kuro = librosa.feature.mfcc(y = wav_kuro, sr = fs_kuro, n_mfcc = 13, n_fft = nfft, hop_length = hopSamples)
mfcc_kuro[0, :] = librosa.feature.rmse(y = wav_kuro, n_fft = nfft, hop_length = hopSamples)
delta_kuro = librosa.feature.delta(mfcc_kuro)
mfcc_kuro = np.r_[mfcc_kuro, delta_kuro]

wav_siro, fs_siro = librosa.load('siro.wav', sr=44100)
wav_siro = np.r_[wav_siro[0], wav_siro[1:] - 0.97 * wav_siro[:-1]]
mfcc_siro = librosa.feature.mfcc(y = wav_siro, sr = fs_siro, n_mfcc = 13, n_fft = nfft, hop_length = hopSamples)
mfcc_siro[0, :] = librosa.feature.rmse(y = wav_siro, n_fft = nfft, hop_length = hopSamples)
delta_siro = librosa.feature.delta(mfcc_siro)
mfcc_siro = np.r_[mfcc_siro, delta_siro]

# Find mfccs that are nearest to video frames in time
t_video = np.linspace(0, numFrames / fps, numFrames)

t_audio_siro = np.linspace(0, mfcc_siro.shape[1] * hopSamples / fs_siro, mfcc_siro.shape[1])
t_audio_kuro = np.linspace(0, mfcc_kuro.shape[1] * hopSamples / fs_kuro, mfcc_kuro.shape[1])

NN = NearestNeighbors(n_neighbors = 1, metric = 'l1')

NN.fit(t_audio_siro.reshape(-1, 1))
distance, ind = NN.kneighbors(t_video.reshape(-1, 1))
mfcc_siro_sampled = mfcc_siro[:, ind.squeeze()]

NN.fit(t_audio_kuro.reshape(-1, 1))
distance, ind = NN.kneighbors(t_video[:2041].reshape(-1, 1))
mfcc_kuro_sampled = mfcc_kuro[:, ind.squeeze()]

# Cluster mfccs. Use 40 clusters -- 39 clusterable phonemes in American English
M = 40
#X = np.c_[mfcc_siro, mfcc_kuro].T
X = mfcc_siro.T
gmmObs = GaussianMixture(n_components = M, covariance_type = 'diag')
gmmObs.fit(X)
mfcc_classes = gmmObs.means_

obsLabels_siro = gmmObs.predict(mfcc_siro_sampled.T)
obsLabels_kuro = gmmObs.predict(mfcc_kuro_sampled.T)

# Find and cluster the features of the video in model-space
m = Bunch(np.load('../models/bfm2017.npz'))
m.idEvec = m.idEvec[:, :, :80]
m.idEval = m.idEval[:80]
m.expEvec = m.expEvec[:, :, :76]
m.expEval = m.expEval[:76]
m.texEvec = m.texEvec[:, :, :80]
m.texEval = m.texEval[:80]

param = np.load('paramWithoutRTS.npy')
#for frame in np.arange(1, numFrames + 1):
#    shape = generateFace(np.r_[param[frame, :-7], np.zeros(6), 1], m)

#tmesh = mlab.triangular_mesh(shape[0, :], shape[1, :], shape[2, :], m.face, scalars = np.arange(m.numVertices), color = (1, 1, 1))
#view = mlab.view()

N = 150
X = param[:, 80: -7]
kShapes = KMeans(n_clusters = N)
kShapes.fit(X)

stateShapes = kShapes.cluster_centers_
stateLabels = kShapes.labels_

# Calculate initial state probabilities for states
states, stateCounts = np.unique(stateLabels, return_counts = True)
pi = stateCounts / stateLabels.size

# Calculate transition probabilities using known clusters
transition, transitionCounts = np.unique(np.c_[stateLabels[:-1], stateLabels[1:]], return_counts = True, axis = 0)
A = np.zeros((N, N))
A[transition[:, 0], transition[:, 1]] = transitionCounts
A /= A.sum(1)[:, np.newaxis]

# Calculate emission probabilities using known clusters
B = np.zeros((N, M))
for state in range(N):
    obsClass, classCount = np.unique(obsLabels_siro[stateLabels == state], return_counts = True)
    B[state, obsClass] = classCount
B /= B.sum(1)[:, np.newaxis]

# HMM stuff
model = hmm.MultinomialHMM(n_components = N)
model.startprob_ = pi
model.transmat_ = A
model.emissionprob_ = B

# Try to reproduce siro
stateSeq_siro = model.predict(obsLabels_siro.reshape(-1, 1))

# Kuro
stateSeq_kuro = model.predict(obsLabels_kuro.reshape(-1, 1))

# Filter through the state sequences to filter the shape renderings


# Render and save pics
if not os.path.exists('stateShapes'):
    os.makedirs('stateShapes')
np.save('siroStateSequence', stateSeq_siro)
np.save('kuroStateSequence', stateSeq_kuro)
for shape in range(N):
    fName = '{:0>5}'.format(shape + 1)
    exportObj(generateFace(np.r_[param[-1, :80], stateShapes[stateSeq_siro[shape], :], np.zeros(6), 1], m), f = m.face, fNameOut = 'stateShapes/' + fName)


#dir_siro = 'obama/hmm_siro_N' + str(N) + 'M' + str(M)
#dir_kuro = 'obama/hmm_kuro_N' + str(N) + 'M' + str(M)
#if not os.path.exists(dir_siro):
#    os.makedirs(dir_siro)
#if not os.path.exists(dir_kuro):
#    os.makedirs(dir_kuro)
#
#for frame in range(400):
#    fName = '{:0>5}'.format(frame + 1)
#    shape = generateFace(np.r_[param[frame, :80], stateShapes[stateSeq_siro[frame], :], np.zeros(6), 1], m)
#    
#    mlab.options.offscreen = True
#    tmesh = mlab.triangular_mesh(shape[0, :], shape[1, :], shape[2, :], m.face, scalars = np.arange(m.numVertices), color = (1, 1, 1))
#    mlab.view(view[0], view[1], view[2], view[3])
#    mlab.savefig(dir_siro + '/' + fName + '.png', figure = mlab.gcf())
#    mlab.close(all = True)
#    
#for frame in range(400):
#    fName = '{:0>5}'.format(frame + 1)
#    shape = generateFace(np.r_[param[frame, :80], stateShapes[stateSeq_kuro[frame], :], np.zeros(6), 1], m)
#    
#    mlab.options.offscreen = True
#    tmesh = mlab.triangular_mesh(shape[0, :], shape[1, :], shape[2, :], m.face, scalars = np.arange(m.numVertices), color = (1, 1, 1))
#    mlab.view(view[0], view[1], view[2], view[3])
#    mlab.savefig(dir_kuro + '/' + fName + '.png', figure = mlab.gcf())
#    mlab.close(all = True)