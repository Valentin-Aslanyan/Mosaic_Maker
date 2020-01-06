"""

"""


min_size=5 #pixels
border_color=(0,0,0)
minimum_piece_size=5
piece_font_size=12
piece_padding=3
reference_line_length=100 #pixels wide
paper_padding=10 #Pixels on each side when outputting to A4 paper

inch_to_mm=25.4
paper_size=[297.0,210.0] #mm
px_per_mm=3.0

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
from PyPDF2 import PdfFileMerger
from copy import deepcopy
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
def pin_click_to_border(new_point_click,input_pixels,input_width,input_height,border_pixels):
	new_point=[0,0]

	#Look for border near click
	current_distance=0
	convergence_reached=False
	while convergence_reached==False and current_distance<=min_size:
		idx_y=new_point_click[1]-current_distance
		if idx_y>=0:
			idx_x=max([0,new_point_click[0]-current_distance+1])
			idx_x_limit=min([input_width,new_point_click[0]+current_distance+1])
			while convergence_reached==False and idx_x<idx_x_limit:
				if border_pixels[idx_x,idx_y]!=0:
					convergence_reached=True
					new_point=[idx_x,idx_y]
				idx_x+=1
		idx_x=new_point_click[0]+current_distance
		if idx_x<input_width:
			idx_y=max([0,new_point_click[1]-current_distance+1])
			idx_y_limit=min([input_height,new_point_click[1]+current_distance+1])
			while convergence_reached==False and idx_y<idx_y_limit:
				if border_pixels[idx_x,idx_y]!=0:
					convergence_reached=True
					new_point=[idx_x,idx_y]
				idx_y+=1
		idx_y=new_point_click[1]+current_distance
		if idx_y<input_height:
			idx_x=min([input_width-1,new_point_click[0]+current_distance-1])
			idx_x_limit=max([0,new_point_click[0]-current_distance-1])
			while convergence_reached==False and idx_x>idx_x_limit:
				if border_pixels[idx_x,idx_y]!=0:
					convergence_reached=True
					new_point=[idx_x,idx_y]
				idx_x-=1
		idx_x=new_point_click[0]-current_distance
		if idx_x>=0:
			idx_y=min([input_height-1,new_point_click[1]+current_distance-1])
			idx_y_limit=max([0,new_point_click[1]-current_distance-1])
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


#Parse the read-in points and connections, remove illegal and reorder index
def check_read_in(points_coordinates_read,points_type_read,points_connections_read,points_idx_read,border_pixels):
	points_coordinates=[]
	points_type=[]
	points_connections=[]
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
			if border_pixels[idx_x,idx_y]!=0 and not near_point:
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


#Draw line between two points, check if inside image TODO - can be refactored for speed if needed
def bresenham_bounded(x0,y0,x1,y1,arr2d):
	limx=len(arr2d[:,0])
	limy=len(arr2d[0,:])
	if x0==x1:  #Vertical
		if x0>=0 and x0<limx:
			if y0>y1:
				y2=y0
				y0=y1
				y1=y2
			for idx_y in range(max(y0,0),min(y1+1,limy)):
				arr2d[x0,idx_y]+=1
	elif abs(x0-x1)>abs(y0-y1):  #gradient below 1
		if x0>x1:  #Swap points if x0>x1
			x2=x0
			y2=y0
			x0=x1
			y0=y1
			x1=x2
			y1=y2
		deltay=y1-y0
		deltax=x1-x0
		deltaerr=abs(deltay/deltax)
		signerr=1
		if deltay/deltax<0.0:
			signerr=-1
		error=0.0
		idx_y=y0
		for idx_x in range(max(x0,0),min(x1+1,limx)):
			if idx_y>=0 and idx_y<limy:
				arr2d[idx_x,idx_y]+=1
			error+=deltaerr
			if error>=0.5:
				idx_y+=signerr
				error-=1.0
	else:  #gradient above 1
		if y0>y1:  #Swap points if y0>y1
			x2=x0
			y2=y0
			x0=x1
			y0=y1
			x1=x2
			y1=y2
		deltay=y1-y0
		deltax=x1-x0
		deltaerr=abs(deltax/deltay)
		signerr=1
		if deltax/deltay<0.0:
			signerr=-1
		error=0.0
		idx_x=x0
		for idx_y in range(max(y0,0),min(y1+1,limy)):
			if idx_x>=0 and idx_x<limx:
				arr2d[idx_x,idx_y]+=1
			error+=deltaerr
			if error>=0.5:
				idx_x+=signerr
				error-=1.0
	return arr2d


#Break image into pieces: each piece bounded by border/connections
#Number pieces, find average color of each piece, bounding box for each piece
def collect_pieces(pix_arr,border_arr):
	checked_arr=np.copy(border_arr)
	piece_arr=np.zeros(np.shape(border_arr),dtype='int32')
	left_to_check=np.zeros(((len(checked_arr[:,0])-2)*(len(checked_arr[0,:])-2),2),dtype='int32')
	num_pieces=0
	piece_colors_all=[]
	size_of_piece=[]
	extent_of_piece=[]
	for idx_x in range(1,len(checked_arr[:,0])-1):
		for idx_y in range(1,len(checked_arr[0,:])-1):
			if checked_arr[idx_x,idx_y]==0:  #New piece found
				size_of_piece.append(1)
				extent_of_piece.append([idx_x,idx_x,idx_y,idx_y])  #min_x,max_x,min_y,max_y
				num_pieces+=1
				num_left_to_check=0
				checked_arr[idx_x,idx_y]=1
				piece_arr[idx_x,idx_y]=num_pieces
				piece_color=[pix_arr[idx_x,idx_y][0],pix_arr[idx_x,idx_y][1],pix_arr[idx_x,idx_y][2]]
				if checked_arr[idx_x-1,idx_y]==0:
					left_to_check[num_left_to_check,0]=idx_x-1
					left_to_check[num_left_to_check,1]=idx_y
					num_left_to_check+=1
					checked_arr[idx_x-1,idx_y]=1
					piece_color[0]+=pix_arr[idx_x-1,idx_y][0]
					piece_color[1]+=pix_arr[idx_x-1,idx_y][1]
					piece_color[2]+=pix_arr[idx_x-1,idx_y][2]
					piece_arr[idx_x-1,idx_y]=num_pieces
					size_of_piece[-1]+=1
					extent_of_piece[-1][0]=idx_x-1
				if checked_arr[idx_x,idx_y-1]==0:
					left_to_check[num_left_to_check,0]=idx_x
					left_to_check[num_left_to_check,1]=idx_y-1
					num_left_to_check+=1
					checked_arr[idx_x,idx_y-1]=1
					piece_color[0]+=pix_arr[idx_x,idx_y-1][0]
					piece_color[1]+=pix_arr[idx_x,idx_y-1][1]
					piece_color[2]+=pix_arr[idx_x,idx_y-1][2]
					piece_arr[idx_x,idx_y-1]=num_pieces
					size_of_piece[-1]+=1
					extent_of_piece[-1][2]=idx_y-1
				if checked_arr[idx_x,idx_y+1]==0:
					left_to_check[num_left_to_check,0]=idx_x
					left_to_check[num_left_to_check,1]=idx_y+1
					num_left_to_check+=1
					checked_arr[idx_x,idx_y+1]=1
					piece_color[0]+=pix_arr[idx_x,idx_y+1][0]
					piece_color[1]+=pix_arr[idx_x,idx_y+1][1]
					piece_color[2]+=pix_arr[idx_x,idx_y+1][2]
					piece_arr[idx_x,idx_y+1]=num_pieces
					size_of_piece[-1]+=1
					extent_of_piece[-1][3]=idx_y+1
				if checked_arr[idx_x+1,idx_y]==0:
					left_to_check[num_left_to_check,0]=idx_x+1
					left_to_check[num_left_to_check,1]=idx_y
					num_left_to_check+=1
					checked_arr[idx_x+1,idx_y]=1
					piece_color[0]+=pix_arr[idx_x+1,idx_y][0]
					piece_color[1]+=pix_arr[idx_x+1,idx_y][1]
					piece_color[2]+=pix_arr[idx_x+1,idx_y][2]
					piece_arr[idx_x+1,idx_y]=num_pieces
					size_of_piece[-1]+=1
					extent_of_piece[-1][1]=idx_x+1
				while num_left_to_check>0:
					idx_x2=int(left_to_check[num_left_to_check-1,0])
					idx_y2=int(left_to_check[num_left_to_check-1,1])
					num_left_to_check-=1
					checked_arr[idx_x2,idx_y2]=1
					piece_color[0]+=pix_arr[idx_x2,idx_y2][0]
					piece_color[1]+=pix_arr[idx_x2,idx_y2][1]
					piece_color[2]+=pix_arr[idx_x2,idx_y2][2]
					piece_arr[idx_x2,idx_y2]=num_pieces
					size_of_piece[-1]+=1
					if checked_arr[idx_x2-1,idx_y2]==0:
						left_to_check[num_left_to_check,0]=idx_x2-1
						left_to_check[num_left_to_check,1]=idx_y2
						num_left_to_check+=1
						checked_arr[idx_x2-1,idx_y2]=1
						piece_color[0]+=pix_arr[idx_x2-1,idx_y2][0]
						piece_color[1]+=pix_arr[idx_x2-1,idx_y2][1]
						piece_color[2]+=pix_arr[idx_x2-1,idx_y2][2]
						piece_arr[idx_x2-1,idx_y2]=num_pieces
						size_of_piece[-1]+=1
						extent_of_piece[-1][0]=min(idx_x2-1,extent_of_piece[-1][0])
					if checked_arr[idx_x2+1,idx_y2]==0:
						left_to_check[num_left_to_check,0]=idx_x2+1
						left_to_check[num_left_to_check,1]=idx_y2
						num_left_to_check+=1
						checked_arr[idx_x2+1,idx_y2]=1
						piece_color[0]+=pix_arr[idx_x2+1,idx_y2][0]
						piece_color[1]+=pix_arr[idx_x2+1,idx_y2][1]
						piece_color[2]+=pix_arr[idx_x2+1,idx_y2][2]
						piece_arr[idx_x2+1,idx_y2]=num_pieces
						size_of_piece[-1]+=1
						extent_of_piece[-1][1]=max(idx_x2+1,extent_of_piece[-1][1])
					if checked_arr[idx_x2,idx_y2-1]==0:
						left_to_check[num_left_to_check,0]=idx_x2
						left_to_check[num_left_to_check,1]=idx_y2-1
						num_left_to_check+=1
						checked_arr[idx_x2,idx_y2-1]=1
						piece_color[0]+=pix_arr[idx_x2,idx_y2-1][0]
						piece_color[1]+=pix_arr[idx_x2,idx_y2-1][1]
						piece_color[2]+=pix_arr[idx_x2,idx_y2-1][2]
						piece_arr[idx_x2,idx_y2-1]=num_pieces
						size_of_piece[-1]+=1
						extent_of_piece[-1][2]=min(idx_y2-1,extent_of_piece[-1][2])
					if checked_arr[idx_x2,idx_y2+1]==0:
						left_to_check[num_left_to_check,0]=idx_x2
						left_to_check[num_left_to_check,1]=idx_y2+1
						num_left_to_check+=1
						checked_arr[idx_x2,idx_y2+1]=1
						piece_color[0]+=pix_arr[idx_x2,idx_y2+1][0]
						piece_color[1]+=pix_arr[idx_x2,idx_y2+1][1]
						piece_color[2]+=pix_arr[idx_x2,idx_y2+1][2]
						piece_arr[idx_x2,idx_y2+1]=num_pieces
						size_of_piece[-1]+=1
						extent_of_piece[-1][3]=max(idx_y2+1,extent_of_piece[-1][3])
				piece_colors_all.append((int(piece_color[0]/size_of_piece[-1]),int(piece_color[1]/size_of_piece[-1]),int(piece_color[2]/size_of_piece[-1])))
	return piece_arr,piece_colors_all,size_of_piece,extent_of_piece


#
def rectangles_overlap():
	...


#Each small mosaic piece is bounded by a rectangle, which may overlap with an adjacent rectangle
#Move bounding boxes of pieces so they don't overlap
def spread_piece_singlecanvas(piece_extent,limx,limy,num_spacing):
	new_extent=deepcopy(piece_extent)
	
	new_limx=limx*4
	new_limy=limy*4

	arr_to_sort=np.zeros((len(piece_extent)),dtype='int32')  #Sort by left x edge first, then top y edge
	for idx in range(len(piece_extent)):
		arr_to_sort[idx]=piece_extent[idx][0]*(limy+1)+piece_extent[idx][2]
	sorted_idx=np.argsort(arr_to_sort)

	#px_above_arr=np.outer(np.ones((new_limx)),np.array(range(new_limy)))
	occupied_px=np.zeros((new_limx,new_limy),dtype='int32')
	for idx in sorted_idx:
		piece_width=piece_extent[idx][1]-piece_extent[idx][0]+num_spacing*2
		piece_height=piece_extent[idx][3]-piece_extent[idx][2]+num_spacing*2
		anchor=[piece_extent[idx][0],piece_extent[idx][2]] #Top left corner
		move_piece=True
		moved_left=False
		moved_up=False
		while move_piece:
			#Extend plot area if piece is poking outside
			while anchor[0]+piece_width>=new_limx and anchor[1]+piece_height>=new_limy:
				new_limx+=limx
				new_limy+=limy
				occupied_px=np.pad(occupied_px,((0,limx),(0,limy)),'constant',constant_values=(0,0))
			while anchor[0]+piece_width>=new_limx:
				new_limx+=limx
				occupied_px=np.pad(occupied_px,((0,limx),(0,0)),'constant',constant_values=(0,0))					
			while anchor[1]+piece_height>=new_limy:
				new_limy+=limy
				occupied_px=np.pad(occupied_px,((0,0),(0,limy)),'constant',constant_values=(0,0))
			#Check to move
			if occupied_px[anchor[0],anchor[1]]!=0:	#Move diagonally down and right if top left corner is in occupied territory
				anchor[0]=anchor[0]+1
				anchor[1]=anchor[1]+1
			else: #Will now attempt to move left (as a priority), then attempt to move up, otherwise stop
				if not moved_left: 
					if not moved_up: #Has NOT moved left or up, must check left edge
						occupation=sum(occupied_px[anchor[0],anchor[1]+1:anchor[1]+1+piece_height])
						if occupation!=0: #Left edge occupied, must move right
							anchor[0]=anchor[0]+1
						else: #Left edge clear, must check top edge
							occupation=sum(occupied_px[anchor[0]+1:anchor[0]+1+piece_width,anchor[1]])
							if occupation!=0: #Top edge occupied, must move down
								anchor[1]=anchor[1]+1
							else: #Both left and top edges are clear; right and bottom assumed to be clear
								if anchor[0]>0: #Check left
									occupation=sum(occupied_px[anchor[0]-1,anchor[1]:anchor[1]+1+piece_height])
									if occupation==0: #Left clear, move left
										moved_left=True
										anchor[0]=anchor[0]-1
									elif anchor[1]>0: #Check above
										occupation=sum(occupied_px[anchor[0]:anchor[0]+1+piece_width,anchor[1]-1])
										if occupation==0: #Above clear, move up
											moved_up=True
											anchor[1]=anchor[1]-1
										else: #top edge is occupied AND left edge is occupied
											move_piece=False
									else: #At extreme top of image AND left edge is occupied
										move_piece=False
								elif anchor[1]>0: #Check above
									occupation=sum(occupied_px[anchor[0]:anchor[0]+1+piece_width,anchor[1]-1])
									if occupation==0: #Above clear, move up
										moved_up=True
										anchor[1]=anchor[1]-1
									else: #top edge is occupied AND at extreme left of image
										move_piece=False
								else: #Piece is in top left corner of image
									move_piece=False
					else: # moved_up==True, i.e. HAS moved up
						if anchor[0]>0: #Check left
							occupation=sum(occupied_px[anchor[0]-1,anchor[1]:anchor[1]+1+piece_height])
							if occupation==0: #Left clear, move left
								moved_up=False
								moved_left=True
								anchor[0]=anchor[0]-1
							elif anchor[1]>0: #Check above
								occupation=sum(occupied_px[anchor[0]:anchor[0]+1+piece_width,anchor[1]-1])
								if occupation==0: #Above clear, continue moving up
									anchor[1]=anchor[1]-1
								else: #top edge is occupied AND left edge is occupied
									move_piece=False
							else: #At extreme top of image AND left edge is occupied
								move_piece=False
						elif anchor[1]>0: #Check above
							occupation=sum(occupied_px[anchor[0]:anchor[0]+1+piece_width,anchor[1]-1])
							if occupation==0: #Above clear, continue moving up
								anchor[1]=anchor[1]-1
							else: #top edge is occupied AND at extreme left of image
								move_piece=False
						else: #Piece is in top left corner of image
							move_piece=False
				else: # moved_left==True, i.e. HAS moved left
					if anchor[0]>0: #Check left
						occupation=sum(occupied_px[anchor[0]-1,anchor[1]:anchor[1]+1+piece_height])
						if occupation==0: #Left clear, continue moving left
							anchor[0]=anchor[0]-1
						elif anchor[1]>0: #Check above
							occupation=sum(occupied_px[anchor[0]:anchor[0]+1+piece_width,anchor[1]-1])
							if occupation==0: #Above clear, move up
								moved_up=True
								moved_left=False
								anchor[1]=anchor[1]-1
							else: #top edge is occupied AND left edge is occupied
								move_piece=False
						else: #At extreme top of image AND left edge is occupied
							move_piece=False
					elif anchor[1]>0: #Check above
						occupation=sum(occupied_px[anchor[0]:anchor[0]+1+piece_width,anchor[1]-1])
						if occupation==0: #Above clear, move up
							moved_up=True
							moved_left=False
							anchor[1]=anchor[1]-1
						else: #top edge is occupied AND at extreme left of image
							move_piece=False
					else: #Piece is in top left corner of image
						move_piece=False
		#Piece now moved
		occupied_px[anchor[0]:anchor[0]+1+piece_width,anchor[1]:anchor[1]+1+piece_height]=idx+1
		new_extent[idx][0]=anchor[0]+num_spacing
		new_extent[idx][1]=anchor[0]+piece_width-num_spacing
		new_extent[idx][2]=anchor[1]+num_spacing
		new_extent[idx][3]=anchor[1]+piece_height-num_spacing
	new_width=0
	new_height=0
	for idx in range(len(new_extent)):
		new_width=max(new_width,new_extent[idx][1]+num_spacing)
		new_height=max(new_height,new_extent[idx][3]+num_spacing)
	return new_extent,new_width,new_height


#Move bounding boxes of pieces so they don't overlap
def spread_piece_multicanvas(piece_extent,limx,limy):
	num_spacing=2
	canvas_size=[400,400]

	new_extent=piece_extent.copy()

	arr_to_sort=np.zeros((len(piece_extent)),dtype='int32')  #Sort by left x edge first, then top y edge
	for idx in range(len(piece_extent)):
		arr_to_sort[idx]=piece_extent[idx][0]*(limy+1)+piece_extent[idx][2]
	sorted_idx=np.argsort(arr_to_sort)

	canvas_list=[]
	canvas_list.append(np.array())
	idx_can=0

	px_above_arr=np.outer(np.ones((new_limx)),np.array(range(new_limy)))
	for idx in range(sorted_idx):
		piece_width=piece_extent[idx][1]-piece_extent[idx][0]+num_spacing*2
		piece_height=piece_extent[idx][3]-piece_extent[idx][2]+num_spacing*2


#Use matplotlib to save a PNG image in a PDF of precise dimension
def save_scale_PDF(PDF_size,in_image,PDF_name): #PDF_size in inches >.<
	fig1=plt.figure(figsize=(PDF_size[0],PDF_size[1]))
	ax1=fig1.gca()
	plt.imshow(in_image)
	ax1.get_xaxis().set_ticks([])
	ax1.get_yaxis().set_ticks([])
	ax1.axis('off')

	#Fudge the size to make the plot 
	size_adjust_wd=PDF_size[0]/(ax1.get_window_extent().transformed(fig1.dpi_scale_trans.inverted())).width
	size_adjust_ht=PDF_size[1]/(ax1.get_window_extent().transformed(fig1.dpi_scale_trans.inverted())).height
	fig1.set_size_inches(PDF_size[0]*size_adjust_wd,PDF_size[1]*size_adjust_ht)

	plt.savefig(PDF_name+'.pdf', format="pdf", dpi=300,bbox_inches='tight',pad_inches=0.0)


#Find .png files with name made of digits only
def file_is_target(infilename):
	is_target=False
	valid_characters=['0','1','2','3','4','5','6','7','8','9']
	if len(infilename)>4 and infilename[-4:]=='.png':
		is_target=True
		for char in infilename[:-4]:
			if char not in valid_characters:
				is_target=False
	return is_target



if __name__ == '__main__':
	directory_path=dirname(realpath(__file__))
	directory_files=[f for f in listdir(directory_path) if isfile(join(directory_path, f))]
	target_files=[f for f in listdir(directory_path) if isfile(join(directory_path, f)) and file_is_target(f)]
	if len(target_files)==0:
		print("No files found!")
	
	else:
		#Get maximum size of images
		max_width=1
		max_height=1
		for im_file in target_files:
			raw_image=Image.open(im_file)
			raw_width,raw_height=raw_image.size
			max_width=max(max_width,raw_width)
			max_height=max(max_height,raw_height)

		final_width=max_width+2
		final_height=max_height+2
		final_image=Image.new('RGBA',(final_width,final_height),(0, 0, 0, 0))
		final_pixels=final_image.load()
		BW_image=Image.new('RGBA',(final_width,final_height),(255, 255, 255, 255))
		BW_pixels=BW_image.load()
		border_pixels_all=np.zeros((final_width,final_height),dtype='int32')
		averaged_image=Image.new('RGBA',(final_width,final_height),(0, 0, 0, 0))
		averaged_pixels=averaged_image.load()
		holecheck_image=Image.new('RGB',(max_width,max_height),(255,0,247))
		holecheck_pixels=holecheck_image.load()

		for im_file in target_files:
			print(im_file)
			raw_image=Image.open(im_file)
			raw_pixels=raw_image.load()
			padded_width=raw_width+2
			padded_height=raw_height+2
			padded_image=Image.new('RGBA',(padded_width,padded_height),(0, 0, 0, 0))
			padded_pixels=padded_image.load()
			for idx_x in range(raw_width):
				for idx_y in range(raw_height):
					padded_pixels[idx_x+1,idx_y+1]=raw_pixels[idx_x,idx_y]
					if not pixel_is_background(raw_pixels[idx_x,idx_y]):
						final_pixels[idx_x+1,idx_y+1]=raw_pixels[idx_x,idx_y]
						if holecheck_pixels[idx_x,idx_y]==(0,0,0):
							holecheck_pixels[idx_x,idx_y]=(255,255,0)
						else:
							holecheck_pixels[idx_x,idx_y]=(0,0,0)

			#Set up border
			for idx_x in range(1,padded_width-1):
				for idx_y in range(1,padded_height-1):
					if pixel_is_edge(padded_pixels,idx_x,idx_y,padded_width,padded_height):
						border_pixels_all[idx_x,idx_y]=1

			#Read in previous points and connections
			filename_base=im_file[:-4]
			if filename_base+'.txt' in directory_files:
				points_coordinates_read,points_type_read,points_connections_read,points_idx_read=read_in_saved(filename_base)

				#Check over read-in points
				points_coordinates,points_type,points_connections=check_read_in(points_coordinates_read,points_type_read,points_connections_read, points_idx_read,border_pixels_all)
				#for idx in range(len(points_coordinates)):
				#	border_pixels_all[points_coordinates[idx][0],points_coordinates[idx][1]]+=1
				for idx in range(len(points_connections)):
					for idx2 in points_connections[idx]:
						border_pixels_all=bresenham_bounded(points_coordinates[idx][0], points_coordinates[idx][1], points_coordinates[idx2][0], points_coordinates[idx2][1],border_pixels_all)

		holecheck_image.save("Hole_Check.png")

		for idx_x in range(final_width):
			for idx_y in range(final_height):
				if pixel_is_background(final_pixels[idx_x,idx_y]):
					border_pixels_all[idx_x,idx_y]=1
				if border_pixels_all[idx_x,idx_y]!=0:
					final_pixels[idx_x,idx_y]=border_color
					averaged_pixels[idx_x,idx_y]=border_color
					BW_pixels[idx_x,idx_y]=border_color
		piece_pixels,piece_colors,piece_sizes,piece_limits=collect_pieces(final_pixels,border_pixels_all)
		for idx_x in range(final_width):
			for idx_y in range(final_height):
				piece_num=piece_pixels[idx_x,idx_y]
				if piece_num!=0:
					if piece_sizes[piece_num-1]>=minimum_piece_size:
						averaged_pixels[idx_x,idx_y]=piece_colors[piece_num-1]
					else:
						averaged_pixels[idx_x,idx_y]=border_color
						BW_pixels[idx_x,idx_y]=border_color
		num_full_pieces=0
		for sz in piece_sizes:
			if sz>=minimum_piece_size:
				num_full_pieces+=1
		print("Number of pieces: ",num_full_pieces)


		singlecanvas_limits,singlecanvas_width,singlecanvas_height=spread_piece_singlecanvas(piece_limits,final_width,final_height,piece_padding)
		singlecanvas_image=Image.new('RGBA',(singlecanvas_width,singlecanvas_height),(0, 0, 0, 0))
		singlecanvas_pixels=singlecanvas_image.load()
		
		for idx in range(len(piece_limits)):
			for idx_x in range(piece_limits[idx][1]-piece_limits[idx][0]+1):
				for idx_y in range(piece_limits[idx][3]-piece_limits[idx][2]+1):
					if piece_pixels[piece_limits[idx][0]+idx_x,piece_limits[idx][2]+idx_y]==idx+1:
						singlecanvas_pixels[singlecanvas_limits[idx][0]+idx_x,singlecanvas_limits[idx][2]+idx_y]=averaged_pixels[piece_limits[idx][0]+idx_x,piece_limits[idx][2]+idx_y]

		fig1=plt.figure()
		ax1=fig1.gca()
		plt.imshow(final_image)
		final_image.save("Mosaic_Natural.png")
		BW_image.save("Mosaic_Binary.png")

		px_paper_x=int(paper_size[0]*px_per_mm)-2*paper_padding #Image pixels to be printed, horizontal
		px_paper_y=int(paper_size[1]*px_per_mm)-2*paper_padding #Image pixels to be printed, vertical

		num_paper_x=int(np.ceil(final_width/px_paper_x))
		num_paper_y=int(np.ceil(final_height/px_paper_y))
		BW_paper_merger=PdfFileMerger()
		Natural_paper_merger=PdfFileMerger()
		for idx_pa_y in range(num_paper_y):
			start_px_y=px_paper_y*idx_pa_y
			for idx_pa_x in range(num_paper_x):
				start_px_x=px_paper_x*idx_pa_x
				BW_paper_image=Image.new('RGBA',(int(paper_size[0]*px_per_mm),int(paper_size[1]*px_per_mm)),(0, 0, 0, 0))
				BW_paper_pixels=BW_paper_image.load()
				Natural_paper_image=Image.new('RGBA',(int(paper_size[0]*px_per_mm),int(paper_size[1]*px_per_mm)),(0, 0, 0, 0))
				Natural_paper_pixels=Natural_paper_image.load()
				for idx_x in range(start_px_x,min(start_px_x+px_paper_x,final_width)):
					for idx_y in range(start_px_y,min(start_px_y+px_paper_y,final_height)):
						BW_paper_pixels[idx_x-start_px_x+paper_padding,idx_y-start_px_y+paper_padding]=BW_pixels[idx_x,idx_y]
						Natural_paper_pixels[idx_x-start_px_x+paper_padding,idx_y-start_px_y+paper_padding]=final_pixels[idx_x,idx_y]
				BW_paper_image.save("Mosaic_Binary_Piece"+str(idx_pa_y*num_paper_x+idx_pa_x+1)+".png")
				save_scale_PDF([paper_size[0]/inch_to_mm,paper_size[1]/inch_to_mm],BW_paper_image,"Mosaic_Binary_Piece"+str(idx_pa_y*num_paper_x+idx_pa_x+1))
				BW_paper_merger.append("Mosaic_Binary_Piece"+str(idx_pa_y*num_paper_x+idx_pa_x+1)+".pdf")
				Natural_paper_image.save("Mosaic_Natural_Piece"+str(idx_pa_y*num_paper_x+idx_pa_x+1)+".png")
				save_scale_PDF([paper_size[0]/inch_to_mm,paper_size[1]/inch_to_mm],Natural_paper_image,"Mosaic_Natural_Piece"+str(idx_pa_y*num_paper_x+idx_pa_x+1))
				Natural_paper_merger.append("Mosaic_Natural_Piece"+str(idx_pa_y*num_paper_x+idx_pa_x+1)+".pdf")

		BW_paper_merger.write("Mosaic_Binary_Piece_All.pdf")
		BW_paper_merger.close()
		Natural_paper_merger.write("Mosaic_Natural_Piece_All.pdf")
		Natural_paper_merger.close()

		fig2=plt.figure()
		ax2=fig2.gca()
		plt.imshow(averaged_image)
		averaged_image.save("Mosaic_Averaged.png")

		font=ImageFont.truetype(join(directory_path,'OpenSans-Regular.ttf'),piece_font_size)

		averaged_draw=ImageDraw.Draw(averaged_image)
		for idx in range(len(piece_limits)):
			txt_x,txt_y=averaged_draw.textsize(str(idx+1),font=font)
			averaged_draw.text(((piece_limits[idx][0]+piece_limits[idx][1]-txt_x)//2,(piece_limits[idx][2]+piece_limits[idx][3]-txt_y)//2),str(idx+1),(255,0,0),font)
		averaged_image.save("Mosaic_Numbered.png")

		singlecanvas_draw=ImageDraw.Draw(singlecanvas_image)
		for idx in range(len(singlecanvas_limits)):
			txt_x,txt_y=averaged_draw.textsize(str(idx+1),font=font)
			singlecanvas_draw.text(((singlecanvas_limits[idx][0]+singlecanvas_limits[idx][1]-txt_x)//2,(singlecanvas_limits[idx][2]+singlecanvas_limits[idx][3]-txt_y)//2),str(idx+1),(255,0,0),font)
		singlecanvas_image.save("Mosaic_Pieces.png")

		#plt.show()




