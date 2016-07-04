# -*- coding: utf-8 -*-
"""
Created on Mon Jul  4 14:05:06 2016

@author: yash
"""

from __future__ import print_function

import os

from PyQt4 import QtCore, QtGui
from PyQt4.uic import loadUiType
from PyQt4.QtGui import QGraphicsScene, QFileDialog, QPixmap

from heapq import nsmallest
import pickle
import cv2

Ui_MainWindow, QMainWindow = loadUiType('CBIR_gui.ui')

class ImgWidget(QtGui.QLabel):
    ##IMP: IF using QtDesigner to make tables, make sure to set default row, column to non zero values
    ##otherwise it doesn't seem to work [Weird Bug]
    def __init__(self, parent=None, imagePath = '', size = 50):
        super(ImgWidget, self).__init__(parent)        
        pic = QtGui.QPixmap(imagePath)
        if pic.height()>pic.width(): pic=pic.scaledToWidth(size)
        else: pic=pic.scaledToHeight(size)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setPixmap(pic)


class CBIR(QMainWindow, Ui_MainWindow):
    flag = True
    categories = {}
    valid_images = ["jpg","png","tga", "pgm", "jpeg"]
    valid_videos = ["mp4", "avi"]
    edge_threshold = 100
    topk = 10
    to_disp = [] 
    stop = False
    database_path = ''
    thumbnail_size = 256
    spacing = 40
    images_per_row = 2 
    cached_db = []
    cached_db_path = ''
    
    def __init__(self, ):
        super(CBIR, self).__init__()        #initialise from the ui designed by Designer App
        self.setupUi(self)
        self.setupUi_custom()
        
        path = '/home/yash/Project/dataset/Pascal VOC 2012/samples'
        pictures = []
        for f in os.listdir(path):              #list all the files in the folder
            ext = f.split('.')[1]        #get the file extension
            if ext.lower() not in self.valid_images: continue#check if the extension is valid for the image
            pictures.append(path+'/'+f )
        self.show_similar(pictures)
   
    def setupUi_custom(self,):    
        self.scene = QGraphicsScene()
        self.scene2 = QGraphicsScene()
        self.pushButton.clicked.connect(self.select_image)
        self.pushButton_2.clicked.connect(self.find_similar)
        self.pushButton_3.clicked.connect(self.select_database)
        self.horizontalSlider.valueChanged.connect(self.update_LCD)
        #TODO [WEIRD PROBLEM] QPixmap needs to be called at least once with JPG image before tensorFlow, otherwise program crashes
        self.scene.addPixmap(QPixmap(os.getcwd()+"/demo.jpg").scaled(self.graphicsView.size(), QtCore.Qt.KeepAspectRatio))
        self.graphicsView.setScene(self.scene)  
        
    def show_similar(self, pictures):
        self.tableWidget.setMinimumWidth((self.thumbnail_size+self.spacing)*self.images_per_row+(self.spacing*2))
        
        rowCount=len(pictures)//self.images_per_row
        if len(pictures)%self.images_per_row: rowCount+=1
        self.tableWidget.setRowCount(rowCount)
    
        row=-1
        for i,picture in enumerate(pictures):
            col=i%self.images_per_row
            if not col: row+=1
            self.tableWidget.setCellWidget(row, col,  ImgWidget(imagePath = picture, size=self.thumbnail_size))            
    
    def find_similar(self, results):
        #do pattern matching on the images in retrieved cached_db
        #keep top 10
        #display the top 10 imags on right
        if self.database_path == '':
            print("Database file not selected")
            self.select_database()
        
        
        found = False        
        if self.cached_db_path == self.database_path:
            #No need to re-read from cPickle if it's re-run on the same db
            found = True
        
        else:
            self.cached_db_path = self.database_path
            for f in os.listdir(self.database_path):              #list all the files in the folder
                ext = f.split('.')[1]        #get the file extension
                if ext.lower() == 'p':      #check for pickled cached_db file
                    self.cached_db = pickle.load(self.database_path+'/'+f)
                    found = True
                    break
        
        if not found:
            self.cached_db = self.make_db()
            
        best_matches = nsmallest(self.topk, self.cached_db.keys(), \
                                key = lambda e: self.difference(self.cached_db[e], results))
        
        self.show_similar(best_matches)
    
    def difference(self, g1, g2):
        #compute weighted sum of square diff
        #or
        #compute cross entropy diff from normalised vectors
        #or
        #using some other function which involves the graph edge weights also
        print("TODO")
        return #difference measure
    
    
    def make_db(self):
        #stor entire image paths
        #store class vectors
        #store the other results also, including the graph edge weights
        print("Todo")
        
    def select_database(self):
        #Read all the images in the folder
        path = QFileDialog.getExistingDirectory(None, 'Select a folder:', '/home/yash/Downloads/Pascal VOC 2012', QtGui.QFileDialog.ShowDirsOnly)
        self.lineEdit_2.setText(path)   
        self.database_path = path
    
    def update_categories(self):
        #update selected categories
        for radiobox in self.findChildren(QtGui.QRadioButton):
            self.categories[radiobox.text()] = radiobox.isChecked()

    def update_LCD(self):
        #update edge_threshold variable based on slider
        self.edge_threshold = self.horizontalSlider.value()
        self.lcdNumber.display(self.edge_threshold)        
        
    def tag_image(self, filename = None, batch = False, image = None ):
        #importing TensorFlow on top causes segmentation fault (official bug #2034)
        #importing here helps in working around the problem
        #Python modules could be con)sidered as singletons... so no matter how many times they are imported, they get initialized only once
        import Yolo_module as yolo
        
        if(self.flag):
            #initialise the model, only once
            self.classifier = yolo.YOLO_TF()
            self.flag = False            
            
        self.classifier.batch = batch
        
        if not image == None:
            self.classifier.detect_from_cvmat(image)
        else:
            self.classifier.detect_from_file(filename)      #execute Yolo on the image 
        
        return self.classifier.tagged_image
        
    def disp_img(self, filename = None, img = None):
        if not img == None:
            img_rgb = img.copy()
            cv2.cvtColor(img, cv2.COLOR_BGR2RGB, img_rgb)
            img_rgb = QtGui.QImage(img_rgb, img_rgb.shape[1], img_rgb.shape[0], img_rgb.shape[1] * 3,QtGui.QImage.Format_RGB888) 
            self.scene.addPixmap(QPixmap(img_rgb).scaled(self.graphicsView.size(), QtCore.Qt.KeepAspectRatio))
            image = self.tag_image(image = img)
        
        else:
            #DO this step before calling tensorflow
            self.scene.addPixmap(QPixmap(filename).scaled(self.graphicsView.size(), QtCore.Qt.KeepAspectRatio))
                          
            #Dislplay tagged image        
            image = self.tag_image(filename = filename)      
            
        image = QtGui.QImage(image, image.shape[1], image.shape[0], image.shape[1] * 3,QtGui.QImage.Format_RGB888)  #convert to Qt image format      
        self.scene2.addPixmap(QPixmap(image).scaled(self.graphicsView_3.size(), QtCore.Qt.KeepAspectRatio))

        self.graphicsView.setScene(self.scene) 
        self.graphicsView_3.setScene(self.scene2)        

    
    def select_image(self):  
        #Clear previous image displays        
        self.scene.clear()
        self.scene2.clear()
        self.update_categories()
             
        filename = QFileDialog.getOpenFileName(directory = '/home/yash/Downloads/Pascal VOC 2012/samples')
        self.lineEdit.setText(filename)
        
        if filename.split('.')[1] in self.valid_images:
            self.disp_img(filename = filename) 
            self.show_similar([self.classifier.result])
        else:
            print("Invalid file format")


if __name__ == '__main__':
    import sys 
    app = QtGui.QApplication(sys.argv)
    cbir = CBIR()
    cbir.show()
    app.exec()
