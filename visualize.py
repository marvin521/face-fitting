#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 22 18:43:01 2017

@author: leon
"""

from mm import Bunch, generateFace, exportObj, importObj
import os
import numpy as np
import librosa
import librosa.display
from sklearn.neighbors import NearestNeighbors
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
from sklearn import metrics
from mayavi import mlab
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pylab import savefig
from tvtk.api import tvtk

def mlab_imshowColor(im, alpha = 255, **kwargs):
    """
    Plot a color image with mayavi.mlab.imshow.
    im is a ndarray with dim (n, m, 3) and scale (0->255]
    alpha is a single number or a ndarray with dim (n*m) and scale (0->255]
    **kwargs is passed onto mayavi.mlab.imshow(..., **kwargs)
    """
    im = np.concatenate((im, alpha * np.ones((im.shape[0], im.shape[1], 1), dtype = np.uint8)), axis = -1)
    colors = tvtk.UnsignedCharArray()
    colors.from_array(im.reshape(-1, 4))
    m_image = mlab.imshow(np.ones(im.shape[:2][::-1]))
    m_image.actor.input.point_data.scalars = colors
    
    mlab.draw()
    mlab.show()

    return

m = Bunch(np.load('./models/bfm2017.npz'))
m.idEvec = m.idEvec[:, :, :80]
m.idEval = m.idEval[:80]
m.expEvec = m.expEvec[:, :, :76]
m.expEval = m.expEval[:76]
m.texEvec = m.texEvec[:, :, :80]
m.texEval = m.texEval[:80]

sourceLandmarkInds = np.array([16203, 16235, 16260, 16290, 27061, 22481, 22451, 22426, 22394, 8134, 8143, 8151, 8156, 6986, 7695, 8167, 8639, 9346, 2345, 4146, 5180, 6214, 4932, 4158, 10009, 11032, 12061, 13872, 12073, 11299, 5264, 6280, 7472, 8180, 8888, 10075, 11115, 9260, 8553, 8199, 7845, 7136, 7600, 8190, 8780, 8545, 8191, 7837, 4538, 11679])

os.chdir('/home/leon/f2f-fitting/obama/')
numFrames = 2882

# Landmarks
#param = np.load('param.npy')
#plt.ioff()
#for i in range(numFrames):
#    fName = '{:0>5}'.format(i + 1)
#    imgScaled = mpimg.imread('scaled/' + fName + '.png')
#    
#    source = generateFace(param[i, :], m)
#    plt.figure()
#    plt.imshow(imgScaled)
#    plt.scatter(source[0, sourceLandmarkInds], source[1, sourceLandmarkInds], s = 1)
#
#    plt.title(fName)
#    if not os.path.exists('landmarkOptPic'):
#        os.makedirs('landmarkOptPic')
#    savefig('landmarkOptPic/' + fName + '.png', bbox_inches='tight')
#    plt.close('all')

# State shape pics
view = np.load('view.npz')
for i in range(150):
    fName = '{:0>5}'.format(i + 1)
    shape = importObj('stateShapes/' + fName + '.obj', dataToImport = ['v'])[0].T
    
    mlab.figure(bgcolor = (1, 1, 1))
    tmesh = mlab.triangular_mesh(shape[0, :], shape[1, :], shape[2, :], m.face, scalars = np.arange(m.numVertices), color = (0.8, 0.8, 0.8))
    mlab.view(view['v0'], view['v1'], view['v2'], view['v3'])
    mlab.gcf().scene.parallel_projection = True
    
#    break
    if not os.path.exists('stateShapePics'):
        os.makedirs('stateShapePics')
    mlab.savefig('stateShapePics/' + fName + '.png', figure = mlab.gcf())
    mlab.close(all = True)
#
## Original
#param = np.load('paramRTS2Orig.npy')
#view = np.load('viewInFrame.npz')
#for i in range(numFrames):
#    fName = '{:0>5}'.format(i + 1)
#    im = (mpimg.imread('orig/' + fName + '.png') * 255).astype(np.uint8)
#    mlab_imshowColor(im)
#    
#    shape = generateFace(param[i, :], m)
#    tmesh = mlab.triangular_mesh(shape[0, :]-640, shape[1, :]-360, shape[2, :], m.face, scalars = np.arange(m.numVertices), color = (1, 1, 1), opacity = 0.55)
#    mlab.view(view['v0'], view['v1'], view['v2'], view['v3'])
#    mlab.gcf().scene.parallel_projection = True
#    
#    mlab.gcf().scene.camera.zoom(3.5)
#    mlab.move(up = 100)
##    break
#    
#    if not os.path.exists('fitPic'):
#        os.makedirs('fitPic')
#    mlab.savefig('fitPic/' + fName + '.png', figure = mlab.gcf())
#    mlab.close(all = True)
#
#param = np.load('paramWithoutRTS.npy')
#view = np.load('view.npz')
#for i in range(numFrames):
#    fName = '{:0>5}'.format(i + 1)
#    
#    shape = generateFace(param[i, :], m)
#    tmesh = mlab.triangular_mesh(shape[0, :], shape[1, :], shape[2, :], m.face, scalars = np.arange(m.numVertices), color = (1, 1, 1), opacity = 1)
#    mlab.view(view['v0'], view['v1'], view['v2'], view['v3'])
#    mlab.gcf().scene.parallel_projection = True
#    
#    if not os.path.exists('fitPicWithoutFrame'):
#        os.makedirs('fitPicWithoutFrame')
#    mlab.savefig('fitPicWithoutFrame/' + fName + '.png', figure = mlab.gcf())
#    mlab.close(all = True)
#
## Siro reproduction
view = np.load('view.npz')
stateSeq_siro = np.load('siroStateSequence.npy')
for i in range(numFrames):
    fName = '{:0>5}'.format(i + 1)
    
    shape = importObj('stateShapes/' + '{:0>5}'.format(stateSeq_siro[i] + 1) + '.obj', dataToImport = ['v'])[0].T
    tmesh = mlab.triangular_mesh(shape[0, :], shape[1, :], shape[2, :], m.face, scalars = np.arange(m.numVertices), color = (1, 1, 1), opacity = 1)
    mlab.view(view['v0'], view['v1'], view['v2'], view['v3'])
    mlab.gcf().scene.parallel_projection = True
    
#    break
    if not os.path.exists('siro'):
        os.makedirs('siro')
    mlab.savefig('siro/' + fName + '.png', figure = mlab.gcf())
    mlab.close(all = True)

#param = np.load('paramRTS2Orig.npy')
#im = (mpimg.imread('orig/00001.png') * 255).astype(np.uint8)
#mlab_imshowColor(im)
#shape = generateFace(param[0, :], m)
#tmesh = mlab.triangular_mesh(shape[0, :]-640, shape[1, :]-360, shape[2, :], m.face, scalars = np.arange(m.numVertices), color = (1, 1, 1), opacity = 0.55)
#
#view = mlab.view()
#mlab.view(180, view[1], view[2], view[3])
#mlab.gcf().scene.parallel_projection = True
#np.savez('viewInFrame', v0 = view[0], v1 = view[1], v2 = view[2], v3 = view[3])