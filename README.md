Create Classical (like republic era Rome) mosaics out of digital images. Work In Progress; currently uses Python's Matplotlib for visualization, but will eventually be turned into a standalone compiled GUI, probably with qt5.

Beginning with an image

<img src="https://github.com/Valentin-Aslanyan/Mosaic_Maker/blob/master/Examples/Val/OriginalPhoto.png" width="200" height="250">

![Input photograph](https://github.com/Valentin-Aslanyan/Mosaic_Maker/blob/master/Examples/Val/OriginalPhoto.png){:height="250px" width="200px"}

you can split it into pieces by clicking to select vertices and their connections. The algorithm will then split the input image into the pieces; a version with "averaged" colors, which looks more like a typical mosaic is made.

![Natural mosaic pieces](https://github.com/Valentin-Aslanyan/Mosaic_Maker/blob/master/Examples/Val/Mosaic_Natural.png){:height="250px" width="200px"}

![Averaged mosaic pieces](https://github.com/Valentin-Aslanyan/Mosaic_Maker/blob/master/Examples/Val/Mosaic_Averaged.png){:height="250px" width="200px"}

![Piece outlines](https://github.com/Valentin-Aslanyan/Mosaic_Maker/blob/master/Examples/Val/Mosaic_Binary.png){:height="250px" width="200px"}



The algorithm can be used to make a real mosaic, most easily out of plastics (example to follow) with other outputs. The pieces are numbered by the algorithm to assemble the physical copy.

![Numbered pieces](https://github.com/Valentin-Aslanyan/Mosaic_Maker/blob/master/Examples/Val/Mosaic_Numbered.png)

![Pieces spread out](https://github.com/Valentin-Aslanyan/Mosaic_Maker/blob/master/Examples/Val/Mosaic_Pieces.png)

PDF files, which can be printed to scale (on A4 paper, for instance) are generated.
