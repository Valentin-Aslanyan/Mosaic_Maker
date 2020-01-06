"""

background - not part of the mosaic piece, currently transparency
bulk       - part of the mosaic piece, has defined color
border     - background, adjacent to a bulk point 
point      - node on a border or bulk pixel, which are linked together to create the mosaic

"""

filename_base='39'
max_size=15 #pixels
min_size=5
max_connections=4
border_color=(0,0,0)

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from os import listdir
from os.path import isfile, join, realpath, dirname

def pixels_are_equal(pixel1,pixel2):
	if pixel1[0]==pixel2[0] and pixel1[1]==pixel2[1] and pixel1[2]==pixel2[2]:
		return True
	else:
		return False


#TODO - make more general
def pixel_is_background(pixel1):
	if pixel1[3]==0:
		return True
	else:
		return False


#Pixel itself IS NOT background and is either on the edge of the whole image, or is adjacent to background (including diagonal connections) 
def pixel_is_edge(input_pixels,idx_x,idx_y,img_size_x,img_size_y):
	is_edge=False
	if not pixel_is_background(input_pixels[idx_x,idx_y]):
		if idx_x==0 or idx_y==0 or idx_x>=img_size_x-1 or idx_y>=img_size_y-1:
			is_edge=True
		elif pixel_is_background(input_pixels[idx_x-1,idx_y-1]) or pixel_is_background(input_pixels[idx_x-1,idx_y]) or pixel_is_background(input_pixels[idx_x-1,idx_y+1]) or pixel_is_background(input_pixels[idx_x,idx_y-1]) or pixel_is_background(input_pixels[idx_x,idx_y+1]) or pixel_is_background(input_pixels[idx_x+1,idx_y-1]) or pixel_is_background(input_pixels[idx_x+1,idx_y]) or pixel_is_background(input_pixels[idx_x+1,idx_y+1]):
			is_edge=True
	return is_edge


#Check if the target pixel is near an existing (not deleted) point
def pixel_near_point(idx_x,idx_y,points_c,points_t):
	near_other_point=False
	idx=None
	for idx in range(len(points_c)):
		if abs(points_c[idx][0]-idx_x)<=min_size and abs(points_c[idx][1]-idx_y)<=min_size and points_t[idx]!=2:
			near_other_point=True
			break
	return near_other_point,idx


#Must have image bordered by background; should pad raw image with background border beforehand
#Create an ordered list of background pixels adjacent to a bulk pixel; list should be a closed path
def border_to_array(input_pixels,input_width,input_height):
	border_pixels=np.zeros((input_width,input_height),dtype='int32')

	for idx_x in range(1,input_width-1):
		for idx_y in range(1,input_height-1):
			if pixel_is_edge(input_pixels,idx_x,idx_y,input_width,input_height):
				border_pixels[idx_x,idx_y]=1

	return border_pixels
	

#Search around the coordinates of a click for a border pixel
#If pixel found, return convergence_reached=True and the pixel coordinates
def pin_click_to_border(point_click,input_pixels,input_width,input_height,border_pixels):
	new_point=[0,0]

	#Look for border near click
	current_distance=0
	convergence_reached=False
	while convergence_reached==False and current_distance<=min_size:
		idx_y=point_click[1]-current_distance
		if idx_y>=0:
			idx_x=max([0,point_click[0]-current_distance+1])
			idx_x_limit=min([input_width,point_click[0]+current_distance+1])
			while convergence_reached==False and idx_x<idx_x_limit:
				if border_pixels[idx_x,idx_y]!=0:
					convergence_reached=True
					new_point=[idx_x,idx_y]
				idx_x+=1
		idx_x=point_click[0]+current_distance
		if idx_x<input_width:
			idx_y=max([0,point_click[1]-current_distance+1])
			idx_y_limit=min([input_height,point_click[1]+current_distance+1])
			while convergence_reached==False and idx_y<idx_y_limit:
				if border_pixels[idx_x,idx_y]!=0:
					convergence_reached=True
					new_point=[idx_x,idx_y]
				idx_y+=1
		idx_y=point_click[1]+current_distance
		if idx_y<input_height:
			idx_x=min([input_width-1,point_click[0]+current_distance-1])
			idx_x_limit=max([0,point_click[0]-current_distance-1])
			while convergence_reached==False and idx_x>idx_x_limit:
				if border_pixels[idx_x,idx_y]!=0:
					convergence_reached=True
					new_point=[idx_x,idx_y]
				idx_x-=1
		idx_x=point_click[0]-current_distance
		if idx_x>=0:
			idx_y=min([input_height-1,point_click[1]+current_distance-1])
			idx_y_limit=max([0,point_click[1]-current_distance-1])
			while convergence_reached==False and idx_y>idx_y_limit:
				if border_pixels[idx_x,idx_y]!=0:
					convergence_reached=True
					new_point=[idx_x,idx_y]
				idx_y-=1
		current_distance+=1
	return convergence_reached,new_point


#Open txt file and read in the points
def read_in_saved(filename_base):
	points_coordinates_read=[]
	points_type_read=[]
	points_idx_read=[]
	points_connections_read=[]
	reading_points=0
	reading_connections=0
	infile=open(filename_base+'.txt','r')
	for line in infile:
		if line=="\n":
			reading_points=0
			reading_connections=0
		elif "Points" in line:
			reading_points=1
			reading_connections=0
		elif reading_points==1:
			reading_points=2
		elif reading_points==2:
			line_split=line.replace(",","").split()
			if len(line_split)>3:
				points_idx_read.append(int(line_split[0]))
				points_type_read.append(int(line_split[1]))
				points_coordinates_read.append([int(line_split[2]),int(line_split[3])])
		elif "Connections" in line:
			reading_points=0
			reading_connections=1
		elif reading_connections==1:
			line_split=line.replace("-","").replace(">","").split()
			if len(line_split)>1:
				points_connections_read.append([int(line_split[0]),int(line_split[1])])
	infile.close()
	return points_coordinates_read,points_type_read,points_connections_read,points_idx_read


#Remove all deleted points and resolve connections
def clean_points_connections(points_coords_in,points_type_in,points_connections_in):
	points_coords_out=[]
	points_type_out=[]
	points_connections_out=[]
	idx_old_to_new=[]
	idx_new_to_old=[]
	for idx_old in range(len(points_coords_in)):
		if points_type_in[idx_old]==2:	#point deleted
			idx_old_to_new.append(0)
		else:				#point not deleted
			points_coords_out.append(points_coords_in[idx_old])
			points_type_out.append(points_type_in[idx_old])
			idx_old_to_new.append(len(points_coords_out)-1)
			idx_new_to_old.append(idx_old)
			points_connections_out.append([])
	for idx_new in range(len(points_coords_out)):
		idx_old=idx_new_to_old[idx_new]
		for idx2_old in points_connections_in[idx_old]:
			if points_type_in[idx2_old]!=2:	#connection exists
				idx2_new=idx_old_to_new[idx2_old]
				if idx_new not in points_connections_out[idx2_new] and idx2_new not in points_connections_out[idx_new]:
					points_connections_out[idx_new].append(idx2_new)
	return points_coords_out, points_type_out, points_connections_out


#Plot the main image, then connections, then points
def draw_full_figure(image_in):
	global points_coordinates
	global points_type
	global points_connections
	global selected_point_idx
	plt.imshow(image_in)
	for idx in range(len(points_coordinates)):
		for idx2 in points_connections[idx]:
			if points_type[idx]!=2 and points_type[idx2]!=2:
				x_points=[points_coordinates[idx][0],points_coordinates[idx2][0]]
				y_points=[points_coordinates[idx][1],points_coordinates[idx2][1]]
				plt.plot(x_points,y_points,color="blue")
	for idx in range(len(points_coordinates)):
		if idx==selected_point_idx[0]:
			plt.plot([points_coordinates[idx][0]],[points_coordinates[idx][1]],"o",ms=4,color="red",mec="black")
		elif points_type[idx]==0:
			plt.plot([points_coordinates[idx][0]],[points_coordinates[idx][1]],"o",ms=4,color="green",mec="black")
		elif points_type[idx]==1:
			plt.plot([points_coordinates[idx][0]],[points_coordinates[idx][1]],"o",ms=4,color="black",mec="black")


#Parse the read-in points and connections, remove illegal and reorder index
def check_read_in(points_coordinates_read,points_type_read,points_connections_read,points_idx_read):
	if len(points_idx_read)>0:
		read_to_old=[0 for idx in range(max(points_idx_read)+1)]
	old_to_new=[]
	for idx in range(len(points_coordinates_read)):
		read_to_old[points_idx_read[idx]]=idx
		old_to_new.append(None)
		idx_x=points_coordinates_read[idx][0]
		idx_y=points_coordinates_read[idx][1]
		near_point,idx_near=pixel_near_point(points_coordinates_read[idx][0], points_coordinates_read[idx][1], points_coordinates, points_type)
		if points_type_read[idx]==0:
			if border_pixels[idx_x,idx_y]==1 and not near_point:
				points_coordinates.append(points_coordinates_read[idx])
				points_type.append(0)
				points_connections.append([])
				old_to_new[-1]=len(points_coordinates)-1
		elif points_type_read[idx]==1:
			if not pixel_is_background(padded_pixels[idx_x,idx_y]) and not near_point:
				points_coordinates.append(points_coordinates_read[idx])
				points_type.append(1)
				points_connections.append([])
				old_to_new[-1]=len(points_coordinates)-1
	for idx in range(len(points_connections_read)):
		idx1=old_to_new[read_to_old[points_connections_read[idx][0]]]
		idx2=old_to_new[read_to_old[points_connections_read[idx][1]]]
		if idx1!=None and idx2!=None:
			if idx1>idx2:
				points_connections[idx2].append(idx1)
			else:
				points_connections[idx1].append(idx2)
	return points_coordinates,points_type,points_connections


#Main GUI loop, using Matplotlib's event loop
points_coordinates=[]
points_type=[]		#0 - border, 1 - bulk, 2 - deleted
points_connections=[]
border_pixels=[]
old_point_click=[0,0]
def Click_Loop(event):
	global points_coordinates
	global points_type
	global points_connections
	global selected_point_idx
	global border_pixels
	global old_point_click
	new_point_click=[0,0]
	if event.dblclick==True: #Double click
		new_point_click[0]=int(event.xdata)#TODO
		new_point_click[1]=int(event.ydata)
		if event.button==1 and old_point_click[0]!=None and old_point_click[1]!=None:	#Double left click (not outside plot)

			near_other_point=False
			for idx in range(len(points_coordinates)): #Check if near other point
				if abs(points_coordinates[idx][0]-old_point_click[0])<=min_size and abs(points_coordinates[idx][1]-old_point_click[1])<=min_size and points_type[idx]!=2:
					near_other_point=True
					break
			if not near_other_point: #Double left click, not near other point
				convergence_reached,new_point_border=pin_click_to_border(old_point_click,padded_pixels,padded_width,padded_height,border_pixels)
				if convergence_reached: #Point is near border
					if len(points_coordinates)==0: #No points, need to create new list
						points_coordinates=[new_point_border]
						points_type=[0]
						points_connections=[[]]
						selected_point_idx[0]=0
					else: #Some points exist, need to update list
						points_coordinates.append(new_point_border)
						points_type.append(0)
						points_connections.append([])
						selected_point_idx[1]=selected_point_idx[0]
						selected_point_idx[0]=len(points_coordinates)-1
				else: #Double right click, not near border
					if not pixel_is_background(padded_pixels[old_point_click[0],old_point_click[1]]):
						if len(points_coordinates)==0:
							points_coordinates=[old_point_click[:]]
							points_type=[1]
							points_connections=[[]]
							selected_point_idx[0]=0
						else:
							points_coordinates.append(old_point_click[:])
							points_type.append(1)
							points_connections.append([])
							selected_point_idx[1]=selected_point_idx[0]
							selected_point_idx[0]=len(points_coordinates)-1
			else: #Left click near existing point - select point
				if selected_point_idx[0]!=None and selected_point_idx[1]!=None:#TODO
					if selected_point_idx[0]<selected_point_idx[1]:
						if selected_point_idx[1] not in points_connections[selected_point_idx[0]]:
							points_connections[selected_point_idx[0]].append(selected_point_idx[1])			
					else:
						if selected_point_idx[0] not in points_connections[selected_point_idx[1]]:
							points_connections[selected_point_idx[1]].append(selected_point_idx[0])
				selected_point_idx[0]=selected_point_idx[1]
				selected_point_idx[1]=None
		if event.button==3 and event.xdata!=None and event.ydata!=None:	#Right click
			for idx in range(len(points_coordinates)-1,-1,-1): #Go through points and delete any nearby
				if abs(points_coordinates[idx][0]-old_point_click[0])<=min_size and abs(points_coordinates[idx][1]-old_point_click[1])<=min_size:
					points_type[idx]=2
					selected_point_idx=[None,None]

	if event.dblclick==False: #Single click
		new_point_click[0]=int(event.xdata)
		new_point_click[1]=int(event.ydata)
		if event.button==1 and new_point_click[0]!=None and new_point_click[1]!=None:	#Left click

			near_other_point=False
			for idx in range(len(points_coordinates)):
				if abs(points_coordinates[idx][0]-new_point_click[0])<=min_size and abs(points_coordinates[idx][1]-new_point_click[1])<=min_size and points_type[idx]!=2:
					near_other_point=True
					selected_point_idx[1]=selected_point_idx[0]
					selected_point_idx[0]=idx
					break
	if selected_point_idx[0]!=None:
		selected_points_coordinates=points_coordinates[selected_point_idx[0]]

	print(event.dblclick,event.button,event.x,event.y,event.xdata,event.ydata,old_point_click,selected_point_idx)
	old_point_click[0]=new_point_click[0] #When double clicking, use the first click's coords - otherwise messes up due to some sort of matplotlib error(?)
	old_point_click[1]=new_point_click[1]
					
	plt.clf()
	draw_full_figure(padded_image)
	plt.draw()


if __name__ == '__main__':
	directory_path=dirname(realpath(__file__))
	directory_files=[f for f in listdir(directory_path) if isfile(join(directory_path, f))]
	if filename_base+'.png' not in directory_files:
		print("File not found!")
	else:
		#Read in and pad the image file
		raw_image=Image.open(filename_base+'.png')
		raw_width,raw_height=raw_image.size
		raw_pixels=raw_image.load()
		padded_width=raw_width+2
		padded_height=raw_height+2
		padded_image=Image.new('RGBA',(padded_width,padded_height),(0, 0, 0, 0))
		padded_pixels=padded_image.load()
		for idx_x in range(raw_width):
			for idx_y in range(raw_height):
				padded_pixels[idx_x+1,idx_y+1]=raw_pixels[idx_x,idx_y]

		#Set up border
		border_pixels=border_to_array(padded_pixels,padded_width,padded_height)
		for idx_x in range(padded_width):
			for idx_y in range(padded_height):
				if border_pixels[idx_x,idx_y]!=0:
					padded_pixels[idx_x,idx_y]=border_color

		#Read in previous points and connections
		if filename_base+'.txt' in directory_files:
			points_coordinates_read,points_type_read,points_connections_read,points_idx_read=read_in_saved(filename_base)

			#Check over read-in points
			points_coordinates,points_type,points_connections=check_read_in(points_coordinates_read,points_type_read,points_connections_read,points_idx_read)

		#Create image and run the GUI mode
		selected_point_idx=[None,None]
		fig1=plt.figure()
		ax1=fig1.gca()
		draw_full_figure(padded_image)
		cid_up = fig1.canvas.mpl_connect('button_press_event', Click_Loop)
		plt.show()

		#Clean up points and connections (i.e. remove deleted etc)
		points_coordinates, points_type, points_connections=clean_points_connections(points_coordinates,points_type,points_connections)

		#Output latest
		outfile=open(filename_base+'.txt','w')
		print("Points",file=outfile)
		print("Number | Type | Coordinates",file=outfile)
		for idx in range(len(points_coordinates)):
			print(idx,points_type[idx],points_coordinates[idx][0],",",points_coordinates[idx][1],file=outfile)
		print("",file=outfile)
		print("Connections",file=outfile)
		for idx in range(len(points_connections)):
			for idx2 in points_connections[idx]:
				print(idx," -> ",idx2,file=outfile)
		outfile.close()


