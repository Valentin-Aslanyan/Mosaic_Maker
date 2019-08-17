"""

"""


max_size=15 #pixels
min_size=5
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
def border_to_list(input_pixels,input_width,input_height):
	border_pixels=np.zeros((input_width,input_height),dtype='int32')

	for idx_x in range(1,input_width-1):
		for idx_y in range(1,input_height-1):
			if not pixel_is_background(input_pixels[idx_x,idx_y]):
				if pixel_is_background(input_pixels[idx_x-1,idx_y-1]):
					border_pixels[idx_x-1,idx_y-1]=1
				if pixel_is_background(input_pixels[idx_x-1,idx_y]):
					border_pixels[idx_x-1,idx_y]=1
				if pixel_is_background(input_pixels[idx_x-1,idx_y+1]):
					border_pixels[idx_x-1,idx_y+1]=1
				if pixel_is_background(input_pixels[idx_x,idx_y-1]):
					border_pixels[idx_x,idx_y-1]=1
				if pixel_is_background(input_pixels[idx_x,idx_y+1]):
					border_pixels[idx_x,idx_y+1]=1
				if pixel_is_background(input_pixels[idx_x+1,idx_y-1]):
					border_pixels[idx_x+1,idx_y-1]=1
				if pixel_is_background(input_pixels[idx_x+1,idx_y]):
					border_pixels[idx_x+1,idx_y]=1
				if pixel_is_background(input_pixels[idx_x+1,idx_y+1]):
					border_pixels[idx_x+1,idx_y+1]=1
	total_border_pixels=sum(border_pixels.flatten())

	border_list=[]
	border_located=False
	idx_x=0
	while border_located==False and idx_x<input_width:
		idx_y=0
		while border_located==False and idx_y<input_height:
			if border_pixels[idx_x,idx_y]==1:
					border_list.append([idx_x,idx_y])
					labelled_pixels=1
					border_located=True
			idx_y+=1
		idx_x+=1


	start_not_reached=True
	idx_x=border_list[-1][0]
	idx_y=border_list[-1][1]
	if idx_x+1<input_width and border_pixels[idx_x+1,idx_y]==1:
		border_list.append([idx_x+1,idx_y])
		labelled_pixels+=1
	elif idx_y+1<input_height and border_pixels[idx_x,idx_y+1]==1:
		border_list.append([idx_x,idx_y+1])
		labelled_pixels+=1
	elif idx_x>0 and border_pixels[idx_x-1,idx_y]==1:
		border_list.append([idx_x-1,idx_y])
		labelled_pixels+=1
	elif idx_y>0 and border_pixels[idx_x,idx_y-1]==1:
		border_list.append([idx_x,idx_y-1])
		labelled_pixels+=1
	else:
		start_not_reached=False
	while total_border_pixels>labelled_pixels and start_not_reached:
		idx_x=border_list[-1][0]
		idx_y=border_list[-1][1]
		if border_list[-1][0]-border_list[-2][0]==0:
			if border_list[-1][1]-border_list[-2][1]>0:	#moving up
				if idx_x+1<input_width and border_pixels[idx_x+1,idx_y]==1:
					border_list.append([idx_x+1,idx_y])
					labelled_pixels+=1
				elif idx_y+1<input_height and border_pixels[idx_x,idx_y+1]==1:
					border_list.append([idx_x,idx_y+1])
					labelled_pixels+=1
				elif idx_x>0 and border_pixels[idx_x-1,idx_y]==1:
					border_list.append([idx_x-1,idx_y])
					labelled_pixels+=1
				elif idx_y>0 and border_pixels[idx_x,idx_y-1]==1:
					border_list.append([idx_x,idx_y-1])
					labelled_pixels+=1
			else:						#moving down
				if idx_x>0 and border_pixels[idx_x-1,idx_y]==1:
					border_list.append([idx_x-1,idx_y])
					labelled_pixels+=1
				elif idx_y>0 and border_pixels[idx_x,idx_y-1]==1:
					border_list.append([idx_x,idx_y-1])
					labelled_pixels+=1
				elif idx_x+1<input_width and border_pixels[idx_x+1,idx_y]==1:
					border_list.append([idx_x+1,idx_y])
					labelled_pixels+=1
				elif idx_y+1<input_height and border_pixels[idx_x,idx_y+1]==1:
					border_list.append([idx_x,idx_y+1])
					labelled_pixels+=1
		else:
			if border_list[-1][0]-border_list[-2][0]>0:	#moving right
				if idx_y>0 and border_pixels[idx_x,idx_y-1]==1:
					border_list.append([idx_x,idx_y-1])
					labelled_pixels+=1
				elif idx_x+1<input_width and border_pixels[idx_x+1,idx_y]==1:
					border_list.append([idx_x+1,idx_y])
					labelled_pixels+=1
				elif idx_y+1<input_height and border_pixels[idx_x,idx_y+1]==1:
					border_list.append([idx_x,idx_y+1])
					labelled_pixels+=1
				elif idx_x>0 and border_pixels[idx_x-1,idx_y]==1:
					border_list.append([idx_x-1,idx_y])
					labelled_pixels+=1
			else:						#moving left
				if idx_y+1<input_height and border_pixels[idx_x,idx_y+1]==1:
					border_list.append([idx_x,idx_y+1])
					labelled_pixels+=1
				elif idx_x>0 and border_pixels[idx_x-1,idx_y]==1:
					border_list.append([idx_x-1,idx_y])
					labelled_pixels+=1
				elif idx_y>0 and border_pixels[idx_x,idx_y-1]==1:
					border_list.append([idx_x,idx_y-1])
					labelled_pixels+=1
				elif idx_x+1<input_width and border_pixels[idx_x+1,idx_y]==1:
					border_list.append([idx_x+1,idx_y])
					labelled_pixels+=1
		if border_list[-1][0]==border_list[0][0] and border_list[-1][1]==border_list[0][1]:
			start_not_reached=False

	return border_list,border_pixels
	

#Search around the coordinates of a click for a border pixel
#If pixel found, return convergence_reached=True and the pixel coordinates
def pin_click_to_border(new_point_click,input_pixels,input_width,input_height):
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
				if pixels_are_equal(input_pixels[idx_x,idx_y],border_color):
					convergence_reached=True
					new_point=[idx_x,idx_y]
				idx_x+=1
		idx_x=new_point_click[0]+current_distance
		if idx_x<input_width:
			idx_y=max([0,new_point_click[1]-current_distance+1])
			idx_y_limit=min([input_height,new_point_click[1]+current_distance+1])
			while convergence_reached==False and idx_y<idx_y_limit:
				if pixels_are_equal(input_pixels[idx_x,idx_y],border_color):
					convergence_reached=True
					new_point=[idx_x,idx_y]
				idx_y+=1
		idx_y=new_point_click[1]+current_distance
		if idx_y<input_height:
			idx_x=min([input_width-1,new_point_click[0]+current_distance-1])
			idx_x_limit=max([0,new_point_click[0]-current_distance-1])
			while convergence_reached==False and idx_x>idx_x_limit:
				if pixels_are_equal(input_pixels[idx_x,idx_y],border_color):
					convergence_reached=True
					new_point=[idx_x,idx_y]
				idx_x-=1
		idx_x=new_point_click[0]-current_distance
		if idx_x>=0:
			idx_y=min([input_height-1,new_point_click[1]+current_distance-1])
			idx_y_limit=max([0,new_point_click[1]-current_distance-1])
			while convergence_reached==False and idx_y>idx_y_limit:
				if pixels_are_equal(input_pixels[idx_x,idx_y],border_color):
					convergence_reached=True
					new_point=[idx_x,idx_y]
				idx_y-=1
		current_distance+=1
	return convergence_reached,new_point


#Cyclically link points on the border to each other
def assign_border_connections(border_list,points_coordinates,points_type,image_width):

	border_arr=np.array(border_list)
	border_arr_flat=image_width*border_arr[:,1]+border_arr[:,0]
	points_arr=np.array(points_coordinates)
	points_arr_flat=image_width*points_arr[:,1]+points_arr[:,0]
	border_connections=[[] for idx in range(len(points_coordinates))]
	border_connections_paths=[[] for idx in range(len(points_coordinates))]

	num_border=0
	for idx in range(len(points_type)):
		if points_type[idx]==0:
			num_border+=1

	#Connect all border points in a cycle
	if num_border>1:
		for idx_p in range(len(points_coordinates)):
			if points_type[idx_p]==0:
				idx_b=np.argwhere(border_arr_flat==points_arr_flat[idx_p])[0,0]
				next_point_found=False
				idx_b2=idx_b+1
				while next_point_found==False and idx_b2<len(border_arr_flat):
					if border_arr_flat[idx_b2] in points_arr_flat:
						next_point_found=True
						idx_b3=np.argwhere(points_arr_flat==border_arr_flat[idx_b2])[0,0]
						path=border_arr[idx_b:idx_b2+1,:]
						border_connections[idx_p].append(idx_b3)
						border_connections[idx_b3].append(idx_p)
					idx_b2+=1
				idx_b2=0
				while next_point_found==False and idx_b2<len(border_arr_flat):
					if border_arr_flat[idx_b2] in points_arr_flat:
						next_point_found=True
						idx_b3=np.argwhere(points_arr_flat==border_arr_flat[idx_b2])[0,0]
						#TODO path
						border_connections[idx_p].append(idx_b3)
						border_connections[idx_b3].append(idx_p)
					idx_b2+=1

	return border_connections, border_connections_paths


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


points_coordinates=[]
points_type=[]		#0 - border, 1 - bulk, 2 - deleted
points_connections=[]
def Click_Loop(event):
	global points_coordinates
	global points_type
	global points_connections
	global selected_point_idx
	if event.dblclick==True:
		if event.button==1 and event.xdata!=None and event.ydata!=None:	#Left click
			new_point_click=[int(event.xdata),int(event.ydata)]
			near_other_point=False
			for idx in range(len(points_coordinates)):
				if abs(points_coordinates[idx][0]-new_point_click[0])<=min_size and abs(points_coordinates[idx][1]-new_point_click[1])<=min_size and points_type[idx]!=2:
					near_other_point=True
					break
			if near_other_point==False:
				convergence_reached,new_point_border=pin_click_to_border(new_point_click,padded_pixels,padded_width,padded_height)
				if convergence_reached:
					if len(points_coordinates)==0:
						points_coordinates=[new_point_border]
						points_type=[0]
						points_connections=[[]]
						selected_point_idx[0]=0
					else:
						points_coordinates.append(new_point_border)
						points_type.append(0)
						points_connections.append([])
						selected_point_idx[1]=selected_point_idx[0]
						selected_point_idx[0]=len(points_coordinates)-1
				else:
					if not pixel_is_background(padded_pixels[new_point_click[0],new_point_click[1]]):
						if len(points_coordinates)==0:
							points_coordinates=[new_point_click]
							points_type=[1]
							points_connections=[[]]
							selected_point_idx[0]=0
							selected_point_idx=0
						else:
							points_coordinates.append(new_point_click)
							points_type.append(1)
							points_connections.append([])
							selected_point_idx[1]=selected_point_idx[0]
							selected_point_idx[0]=len(points_coordinates)-1
			else:
				if selected_point_idx[0]<selected_point_idx[1]:
					if selected_point_idx[1] not in points_connections[selected_point_idx[0]]:
						points_connections[selected_point_idx[0]].append(selected_point_idx[1])			
				else:
					if selected_point_idx[0] not in points_connections[selected_point_idx[1]]:
						points_connections[selected_point_idx[1]].append(selected_point_idx[0])
				selected_point_idx[0]=selected_point_idx[1]
				selected_point_idx[1]=None
		if event.button==3 and event.xdata!=None and event.ydata!=None:	#Right click
			new_point_click=[int(event.xdata),int(event.ydata)]
			for idx in range(len(points_coordinates)-1,-1,-1):
				if abs(points_coordinates[idx][0]-new_point_click[0])<=min_size and abs(points_coordinates[idx][1]-new_point_click[1])<=min_size:
					points_type[idx]=2
					selected_point_idx=[None,None]

	if event.dblclick==False:
		if event.button==1 and event.xdata!=None and event.ydata!=None:	#Left click
			new_point_click=[int(event.xdata),int(event.ydata)]
			near_other_point=False
			for idx in range(len(points_coordinates)):
				if abs(points_coordinates[idx][0]-new_point_click[0])<=min_size and abs(points_coordinates[idx][1]-new_point_click[1])<=min_size and points_type[idx]!=2:
					near_other_point=True
					selected_point_idx[1]=selected_point_idx[0]
					selected_point_idx[0]=idx
					break
	if selected_point_idx[0]!=None:
		selected_points_coordinates=points_coordinates[selected_point_idx[0]]
					
	print(event.dblclick,event.button,event.x,event.y,event.xdata,event.ydata,selected_point_idx)
	plt.clf()
	draw_full_figure(padded_image)
	plt.draw()


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
		border_pixels_all=np.zeros((final_width,final_height),dtype='int32')
		border_list_all=[]

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

			#Set up border
			border_list,border_pixels=border_to_list(padded_pixels,padded_width,padded_height)
			border_list_all.append(border_list)
			border_pixels_all[:len(border_pixels[:,0]),:len(border_pixels[0,:])]+=border_pixels[:,:]
		for idx_x in range(final_width):
			for idx_y in range(final_height):
				if border_pixels_all[idx_x,idx_y]!=0:
					final_pixels[idx_x,idx_y]=border_color
			
		fig1=plt.figure()
		ax1=fig1.gca()
		plt.imshow(final_image)
		plt.show()




