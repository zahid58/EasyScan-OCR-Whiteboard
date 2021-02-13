<h1 align="center">
<p>EasyScan OCR Whiteboard
</h1>
<h3 align="center">
<p>A python GUI digital whiteboard with handwriting recognition (OCR)
</h3>

*Digital Whiteboards* are quite common for conducting online meetings or teaching sessions. What if your digital whiteboard could understand what you are writing? Then, you would be able to save your whiteboard sessions as texts or convert it into a doc file. This may also come in handy to improve the understandibility of the handwriting. 

<p align="center">
 <img alt="cover" src="https://github.com/Zedd1558/EasyScan-OCR-Whiteboard/blob/master/demo/cover.jpg" height="50%" width="50%">
</p>


### Implementation
The frontend GUI is developed using PyQt. The backend OCR operations are done using *PyTesseract* library. That means, you need to have Tesseract OCR installed in your computer. 

Text Recognition Performance is very limited i.e. OCR makes a lot of mistakes which may improve a lot by using a graphics tablet for writing. Better OCR engines or pipelines can be incorporated by changing *recognizeText()* function of *editor.py*

<h4 align="center">
<p>let's see an exmaple
</h4>
<p align="center">
 <img alt="editing" src="https://github.com/Zedd1558/EasyScan-OCR-Whiteboard/blob/master/demo/editpage.jpg" height="50%" width="50%">
</p>
<h4 align="center">
<p>recognized correctly for this example!
</h4>

### Required libraries
PyQt, Numpy, OpenCV3, PyTesseract

### How to run
open up console in the project directory and enter this 
```
python main.py
```
Go to EditPage. 
On the EditPage, press Left click for drawing and Right click for recognizing text.   

<p align="center">
 <img alt="editing" src="https://github.com/Zedd1558/EasyScan-OCR-Whiteboard/blob/master/demo/demo3.gif">
</p>


### Contribute
Feel free to fork the project and contribute. You can incorporate recent and better OCR methods, make the GUI more easy to use, include drawing shapes, tables, diagrams etc.

