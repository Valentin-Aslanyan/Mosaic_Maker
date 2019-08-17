import numpy as np
from PIL import Image
import matplotlib.pyplot as Plot

max_size=15 #pixels
min_size=5
max_connections=4
outside_color=(0,0,0,0)#(255,255,255)
border_color_raw=(0,0,0)
border_color=(1,1,1)

def pixels_are_equal(pixel1,pixel2):
	if pixel1[0]==pixel2[0] and pixel1[1]==pixel2[1] and pixel1[2]==pixel2[2]:
		return True
	else:
		return False

def border_to_list(input_image):
	input_width,input_height=input_image.size
	input_pixels=input_image.load()
	labelled_pixels=np.zeros((input_width,input_height),dtype='int32')

	border_list=[]
	border_located=False
	idx_x=0
	while border_located==False and idx_x<input_width:
		for idx_y in range(input_height):
			if pixels_are_equal(input_pixels[idx_x,idx_y],border_color_raw):
				border_located=True
				border_list.append([idx_x,idx_y])
				labelled_pixels[idx_x,idx_y]=1
				break
		idx_x+=1

	border_complete=False
	while border_complete==False:
		idx_x=border_list[-1][0]
		idx_y=border_list[-1][1]
		if pixels_are_equal(input_pixels[idx_x+1,idx_y],border_color_raw) and labelled_pixels[idx_x+1,idx_y]==0:
			border_list.append([idx_x+1,idx_y])
			labelled_pixels[idx_x+1,idx_y]=1
		elif pixels_are_equal(input_pixels[idx_x+1,idx_y-1],border_color_raw) and labelled_pixels[idx_x+1,idx_y-1]==0:
			border_list.append([idx_x+1,idx_y-1])
			labelled_pixels[idx_x+1,idx_y-1]=1
		elif pixels_are_equal(input_pixels[idx_x,idx_y-1],border_color_raw) and labelled_pixels[idx_x,idx_y-1]==0:
			border_list.append([idx_x,idx_y-1])
			labelled_pixels[idx_x,idx_y-1]=1
		elif pixels_are_equal(input_pixels[idx_x-1,idx_y-1],border_color_raw) and labelled_pixels[idx_x-1,idx_y-1]==0:
			border_list.append([idx_x-1,idx_y-1])
			labelled_pixels[idx_x-1,idx_y-1]=1
		elif pixels_are_equal(input_pixels[idx_x-1,idx_y],border_color_raw) and labelled_pixels[idx_x-1,idx_y]==0:
			border_list.append([idx_x-1,idx_y])
			labelled_pixels[idx_x-1,idx_y]=1
		elif pixels_are_equal(input_pixels[idx_x-1,idx_y+1],border_color_raw) and labelled_pixels[idx_x-1,idx_y+1]==0:
			border_list.append([idx_x-1,idx_y+1])
			labelled_pixels[idx_x-1,idx_y+1]=1
		elif pixels_are_equal(input_pixels[idx_x,idx_y+1],border_color_raw) and labelled_pixels[idx_x,idx_y+1]==0:
			border_list.append([idx_x,idx_y+1])
			labelled_pixels[idx_x,idx_y+1]=1
		elif pixels_are_equal(input_pixels[idx_x+1,idx_y+1],border_color_raw) and labelled_pixels[idx_x+1,idx_y+1]==0:
			border_list.append([idx_x+1,idx_y+1])
			labelled_pixels[idx_x+1,idx_y+1]=1
		else:
			border_complete=True
	return border_list
	

def pin_click_to_border(new_point_click,input_image):
	input_width,input_height=input_image.size
	input_pixels=input_image.load()

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

def assign_connections(border_list,points_coordinates,points_type,image_width):

	border_arr=np.array(border_list)
	border_arr_flat=image_width*border_arr[:,1]+border_arr[:,0]
	points_arr=np.array(points_coordinates)
	points_arr_flat=image_width*points_arr[:,1]+points_arr[:,0]
	connections=[[] for idx in range(len(points_coordinates))]

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
						connections[idx_p].append(idx_b3)
						connections[idx_b3].append(idx_p)
					idx_b2+=1
				idx_b2=0
				while next_point_found==False and idx_b2<len(border_arr_flat):
					if border_arr_flat[idx_b2] in points_arr_flat:
						next_point_found=True
						idx_b3=np.argwhere(points_arr_flat==border_arr_flat[idx_b2])[0,0]
						connections[idx_p].append(idx_b3)
						connections[idx_b3].append(idx_p)
					idx_b2+=1

	#Connect border points to adjacent bulk points
	if len(points_type)>num_border:
		for idx_p in range(len(points_coordinates)):
			if points_type[idx_p]==0:
				start_idx=0
				while points_type[start_idx]==0 and start_idx<len(points_coordinates):
					start_idx+=1
				min_distance_idx=start_idx
				for idx2 in range(start_idx,len(points_coordinates)):
					if idx2!=idx_p and np.linalg.norm(points_arr[idx2,:]-points_arr[idx_p,:])<np.linalg.norm(points_arr[min_distance_idx,:]-points_arr[idx_p,:]) and points_type[idx2]!=0:
						min_distance_idx=idx2
				connections[idx_p].append(min_distance_idx)
				connections[min_distance_idx].append(idx_p)

	#Connect bulk points together
	if len(points_type)-num_border>1:
		for idx_p in range(len(points_coordinates)):
			if points_type[idx_p]!=0 and len(connections[idx_p])<4:
				distances_list=[]
				for idx2 in range(0,len(points_coordinates)):
					if idx2!=idx_p and points_type[idx2]!=0:
						distances_list.append(points_arr[idx2,:]-points_arr[idx_p,:])
				distances_list=np.array(distances_list)
				sorted_idx=np.argsort(distances_list)


	return connections

points_coordinates=[]
points_type=[]		#0 - border, 1 - "bulk" = inside region
def OnClick(event):
	global points_coordinates
	global points_type
	if event.dblclick==False:
		if event.button==1:	#Left click
			new_point_click=[int(event.xdata),int(event.ydata)]
			near_other_point=False
			for idx in range(len(points_coordinates)):
				if abs(points_coordinates[idx][0]-new_point_click[0])<=min_size and abs(points_coordinates[idx][1]-new_point_click[1])<=min_size:
					near_other_point=True
					break
			if near_other_point==False:
				convergence_reached,new_point_border=pin_click_to_border(new_point_click,input_image)
				if convergence_reached:
					if len(points_coordinates)==0:
						points_coordinates=[new_point_border]
						points_type=[0]
					else:
						points_coordinates.append(new_point_border)
						points_type.append(0)
				else:
					if pixels_are_equal(input_pixels[new_point_click[0],new_point_click[1]],outside_color)==False:
						if len(points_coordinates)==0:
							points_coordinates=[new_point_click]
							points_type=[1]
						else:
							points_coordinates.append(new_point_click)
							points_type.append(1)
		if event.button==3:	#Right click
			new_point_click=[int(event.xdata),int(event.ydata)]
			for idx in range(len(points_coordinates)-1,-1,-1):
				if abs(points_coordinates[idx][0]-new_point_click[0])<=min_size and abs(points_coordinates[idx][1]-new_point_click[1])<=min_size:
					del points_coordinates[idx]
					del points_type[idx]
					
	print(event.dblclick,event.button,event.x,event.y,event.xdata,event.ydata)
	Plot.clf()
	Plot.imshow(input_image)
	for idx in range(len(points_coordinates)):
		if points_type[idx]==1:
			Plot.plot([points_coordinates[idx][0]],[points_coordinates[idx][1]],"o",ms=4,color="black",mec="black")
		if points_type[idx]==0:
			Plot.plot([points_coordinates[idx][0]],[points_coordinates[idx][1]],"o",ms=4,color="green",mec="black")
	Plot.draw()


input_image=Image.open('Ex1.png')
input_width,input_height=input_image.size
input_pixels=input_image.load()

border_list=border_to_list(input_image)
for pixel_coords in border_list:
	input_image.putpixel(pixel_coords,border_color)

fig1=Plot.figure()
ax1=fig1.gca()
Plot.imshow(input_image)
cid_up = fig1.canvas.mpl_connect('button_press_event', OnClick)
Plot.show()
Plot.draw()

Plot.clf()
connections=assign_connections(border_list,points_coordinates,points_type,input_width)
Plot.imshow(input_image)
for idx in range(len(points_coordinates)):
	if points_type[idx]==1:
		Plot.plot([points_coordinates[idx][0]],[points_coordinates[idx][1]],"o",ms=4,color="black",mec="black")
	if points_type[idx]==0:
		Plot.plot([points_coordinates[idx][0]],[points_coordinates[idx][1]],"o",ms=4,color="green",mec="black")
for idx in range(len(connections)):
	for idx2 in range(0,len(connections[idx])):
		x_points=[points_coordinates[idx][0],points_coordinates[connections[idx][idx2]][0]]
		y_points=[points_coordinates[idx][1],points_coordinates[connections[idx][idx2]][1]]
		Plot.plot(x_points,y_points,color="blue")

print(connections)
Plot.show()

