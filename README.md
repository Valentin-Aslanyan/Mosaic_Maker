Create Classical (like republic era Rome) mosaics out of digital images. Work In Progress; currently uses Python's Matplotlib for visualization, but will eventually be turned into a standalone compiled GUI, probably with qt5.

The code and this guide are still works in progress, so please report any problems or improvements. I intend to 

## What the code does

Beginning with an image

<img src="https://github.com/Valentin-Aslanyan/Mosaic_Maker/blob/master/Examples/Val/OriginalPhoto.png" width="200" height="250">

you can split it into pieces by clicking to select vertices and their connections. The algorithm will then split the input image into the pieces; a version with "averaged" colors, which looks more like a typical mosaic is made.

<img src="https://github.com/Valentin-Aslanyan/Mosaic_Maker/blob/master/Examples/Val/Mosaic_Natural.png" width="200" height="250">  <img src="https://github.com/Valentin-Aslanyan/Mosaic_Maker/blob/master/Examples/Val/Mosaic_Averaged.png" width="200" height="250">  <img src="https://github.com/Valentin-Aslanyan/Mosaic_Maker/blob/master/Examples/Val/Mosaic_Binary.png" width="200" height="250">


The algorithm can be used to make a real mosaic, most easily out of plastics (example to follow) with other outputs. The pieces are numbered by the algorithm to assemble the physical copy.

<img src="https://github.com/Valentin-Aslanyan/Mosaic_Maker/blob/master/Examples/Val/Mosaic_Numbered.png" width="200" height="250">  <img src="https://github.com/Valentin-Aslanyan/Mosaic_Maker/blob/master/Examples/Val/Mosaic_Pieces.png" width="200" height="250">

PDF files, which can be printed to scale (on A4 paper, for instance) are generated.


## What you will need

To use this, you must first install `Python3` with the `numpy`, `matplotlib` and `Image` libraries. You will also need a Photoshop or a similar image editing application, though I recommend the GNU Image Manipulation Program.

1. Install Python version 3 or later for your Operating System by [downloading here](https://www.python.org/downloads/).

2. To install the Python libraries:

- On Windows, search for `cmd`, right click and run Command Prompt as administrator. Then type

     `pip3 install numpy`

     `pip3 install matplotlib`

     `pip3 install Image`
     
     `pip3 install PyPDF2`

- On Linux, open a terminal and use the commands above, either beginning with `sudo` or adding `-u`.

3. Install Adobe Photoshop or download and install the open source [GNU Image Manipulation Program](https://www.gimp.org/).


## What to do

- Clone (download) this repository.

- Choose the image you wish to edit.

- Open the image in the image editing program you have selected and cut out different regions of the image and paste each one to a transparent layer.

     (Extended explanation coming later)

- Save each layer as an independent image, with the same dimensions as the original. Save these images in the same folder as this repository. Number each image name, 1.png, 2.png etc. See the Examples folder in this repository.

- Run the `Process_Images.py` script, editing the variable `filename_base` to be the number of each image in turn, for instance for 1.png set `filename_base=1`.

- You will want to cover the image which comes up with points and then connect them to make the mosaic pieces. Double left click to create a point and double right click on one to delete it. 

- Click on a point to select it and then double click on another point to connect them. Delete a point if you are unhappy with its connections.

- Points on the edge of the region are automatically connected.

- Close the window to save the connections. Repeat this for each image you have processed in turn.

- Run the `Assemble_Mosaic.py` script.

