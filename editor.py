from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QSizePolicy, QGraphicsView, QGraphicsScene, QSlider, QFileDialog, QShortcut
from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QT_VERSION_STR, QPoint
from PyQt5.QtGui import QImage, QPixmap, QPainterPath, QPen, QPainter,  QActionEvent, QKeySequence, QColor, QFont
import numpy as np
import backend
from qimage2ndarray import rgb_view, array2qimage
import cv2
import pytesseract as tess
tess.pytesseract.tesseract_cmd = r'E:\Program Files\Tesseract-OCR\tesseract.exe'
from PIL import Image

class Editor(QtWidgets.QGraphicsView):

    def __init__(self, scene = None, parent = None, slider = None):
        super(Editor, self).__init__(parent)
        self._zoom = 0
        self._empty = True
        if scene is not None:
            self._scene = scene
        else:
            self._scene = QtWidgets.QGraphicsScene(self)
        
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

        self.drawMode = True
        self.drawing = False
        self.brushColor = "red"
        self.brushSlider = slider
        self.lastPoint = QPoint()
        self.color_index = {"red":0, "green":1, "blue":2}
        self.x  = 0
        self.y = 0

        self._method = "Sentence"
        self._mask = None
        self._current_image = None
        self._previous_mask = None
        self._unmarkedImage = None
        self.set_mask = False
        self.first_time = True
        self.tessConfig = {"Sentence":7, "Word":8}
        self.ocrSc = QShortcut(QKeySequence('Ctrl+X'), self)
        self.ocrSc.activated.connect(self.recognizeText)
        self.saveSc = QShortcut(QKeySequence('Ctrl+S'), self)
        self.saveSc.activated.connect(self.save)
        self.resetSc = QShortcut(QKeySequence('Ctrl+Z'), self)
        self.resetSc.activated.connect(self.reset)        

    def setTesseractConfig(self, method):
        self._method = method

    def hasPhoto(self):
        return not self._empty

    def fit(self, scale=True):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0


    def setMask(self):
        # print("in setMask()")
        self._mask = QImage(self._photo.pixmap().size(), QImage.Format_RGB32)
        self._mask.fill(Qt.black)

    def setPhoto(self, pixmap=None):
        if pixmap.height() > 720 or pixmap.width() > 1280:
            pixmap = pixmap.scaled(1280, 720, Qt.KeepAspectRatio)
        self._zoom = 0
        self._unmarkedImage = QPixmap(pixmap)
        self._current_image = rgb_view(pixmap.toImage())
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self._photo.setPixmap(QtGui.QPixmap())  
        self.setMask()


    def wheelEvent(self, event):

        if self.hasPhoto():
            if event.angleDelta().y() > 0:
                factor = 1.25
                self._zoom += 1
            else:
                factor = 0.8
                self._zoom -= 1
            if self._zoom > 0:
                self.scale(factor, factor)
            elif self._zoom == 0:
                self.fit()
            else:
                self._zoom = 0
        super(Editor, self).wheelEvent(event)            
    
    
    def mouseMoveEvent(self, event):

        if(event.buttons() and Qt.LeftButton) and self.drawing:
            if self.set_mask:
                self.setMask()
                self.set_mask = False
            painter = QPainter (self._mask)
            if not painter.isActive():
                painter.begin(self)
            painter.setRenderHint(QPainter.Antialiasing, True)
            if self.drawMode:
                painter.setPen(QPen(Qt.white, self.brushSlider.value(), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            else:
                painter.setPen(QPen(Qt.black, self.brushSlider.value(), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(self.lastPoint, self.mapToScene(event.pos()))
            painter.end()
            self.lastPoint = self.mapToScene(event.pos())
            img = np.array(self._current_image, dtype = np.float32)
            mask = rgb_view(self._mask)
            channel = self.color_index[self.brushColor]
            ind = np.all(mask != [0,0,0], axis=-1)
            color = np.array([50,50,50], dtype = np.float32)
            color[channel] = 250
            img[ind] = img[ind]*0.45 + color*0.55
            self._photo.setPixmap(QPixmap(array2qimage(img))) #


        super(Editor, self).mouseMoveEvent(event)        


    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:            
            self.drawing = True
            self.lastPoint = self.mapToScene(event.pos())

        elif event.button() == Qt.RightButton:
            self.recognizeText() 
            


    def mouseReleaseEvent(self, event):

        if self.drawMode:
            if event.button() == Qt.LeftButton:
                self.drawing = False
                self.x = event.x()
                self.y = event.y()

        super(Editor, self).mouseReleaseEvent(event)    


    def recognizeText(self):

        # print('in inpaint function')
        img = np.array(self._current_image)              
        mask = rgb_view(self._mask)
        mask = cv2.bitwise_not(mask)

        gray = cv2.cvtColor(mask, cv2.COLOR_RGB2GRAY)
        (_, bw) = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        # print('mask.shape:',bw.shape)
        # print('mask dtype:', bw.dtype)
        cv2.imwrite('mask.png', bw)
        if self.first_time:
            self._previous_mask = bw
            self.first_time = not self.first_time
        else:
            current =  cv2.bitwise_not(self._previous_mask - bw)
            self._previous_mask = np.array(bw)
            bw = current

        invert = cv2.bitwise_not(bw)
        kernel = np.ones((15,15),np.uint8)
        # bw = cv2.dilate(invert,kernel,iterations = 5)
        closed = cv2.morphologyEx(invert, cv2.MORPH_CLOSE, kernel, iterations = 15)
        
        cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(cnts) == 0:
            return
        
        try:
            cnts = sorted(cnts, key=lambda x: cv2.contourArea(x))
            c = cnts[-1]
            x,y,w,h = cv2.boundingRect(c)

            x -= 8; y -= 8
            w += 16; h += 16
            # cv2.rectangle(mask, (x, y), (x + w, y + h), (36,255,12), 2)
            bw = bw[y:y+h,x:x+w]

            # print('mask.shape:',bw.shape)
            # print('mask dtype:', bw.dtype)
            cv2.imwrite('current_mask.png', bw)
            tess_img = Image.fromarray(bw)
            tc = self.tessConfig[self._method]
            custom_config = "-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ!?1234567890abcdefghijklmnopqrstuvwxyz., --psm " + str(tc)
            text = tess.image_to_string(tess_img, lang = 'eng', config = custom_config)
            text = text[:-2]
            
            print("Converted Text\n--------------\n",text)

            cv2.putText(img, text, (x,y), fontFace=cv2.FONT_HERSHEY_SIMPLEX,fontScale=2, color = (10,110,10), thickness=4)
            # qp = QPainter (self._mask)
            # if not qp.isActive():
            #     qp.begin(self)
            # qp.setPen(QColor(0, 150, 30))
            # qp.setFont(QFont('Decorative', 40))
            # # qp.drawText(QPoint(self.x+30, self.y+30),   text)
            # qp.drawText(QPoint(x,y), text)
            # qp.end()


            self.set_mask = False # True
            # self.setMask()
            self._current_image = img
            img = np.array(self._current_image, dtype = np.float32)
            mask = rgb_view(self._mask)
            channel = self.color_index[self.brushColor]
            ind = np.all(mask == [255,255,255], axis=-1)
            color = np.array([50,50,50], dtype = np.float32)
            color[channel] = 250
            img[ind] = img[ind]*0.45 + color*0.55

            # ind = np.all(mask == [0, 150, 30], axis=-1)
            # img[ind] = img[ind]*0.15 + mask[ind]*0.85

            self._photo.setPixmap(QPixmap(array2qimage(img))) #
            # self._photo.setPixmap(QPixmap(output))
        
        except:
            pass


    def save(self):
        try:
            image_path, _ = QFileDialog.getSaveFileName() 
            img = self._photo.pixmap().toImage()
            if not image_path.endswith(".png"):
                image_path += ".png"
            img.save(image_path, "PNG")
        except:
            pass

    def reset(self):
        self._photo.setPixmap(self._unmarkedImage) 
        self.first_time = True
        self.set_mask = True
        self.setMask()
        self._current_image = rgb_view(self._unmarkedImage.toImage())      


class Window(QtWidgets.QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.viewer = Editor(self)

        self.btnLoad = QtWidgets.QToolButton(self)
        self.btnLoad.setText('Load image')
        self.btnLoad.clicked.connect(self.loadImage)

        VBlayout = QtWidgets.QVBoxLayout(self)
        VBlayout.addWidget(self.viewer)
        HBlayout = QtWidgets.QHBoxLayout()
        HBlayout.setAlignment(QtCore.Qt.AlignLeft)
        HBlayout.addWidget(self.btnLoad)
        VBlayout.addLayout(HBlayout)

    def loadImage(self):
        fileName, dummy = QFileDialog.getOpenFileName(self, "Open image file.")
        self.viewer.setPhoto(QPixmap(fileName))

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.setGeometry(500, 300, 800, 600)
    window.show()
    sys.exit(app.exec_())


