import cv2
import numpy as np
import csv
import argparse
import os.path
import subprocess

#### Image parameters, could be changed if your imaging setup is different
dpi = 300
header_offset = 0

# Grid size, corresponding to grid_a.pdf.
dx = 261
dy = 477

# Number of rows and columns
nrows = 7
ncols = 18


def is_valid_file(parser, arg):
	"""
	Checks if a file given to the argument parser actually exists
	"""
	if not os.path.exists(arg):
		parser.error("The file %s does not exist! Did you make a typo?" % arg)
	else:
		return arg

def data_writer(outputfile, data_table):
	"""
	Helper function to write data to a csv
	"""
	with open(outputfile, 'w', newline = '') as f:
		writer = csv.writer(f)
		writer.writerow(['column','row','bioassay', 'dpi', 'genotype','pathogen','treatment','leaf_area', 'bacteria_area', 'chlorotic_area'])
		for row in data_table:
			writer.writerow(row)

def crop(scan, row, column):
	"""
	Crops a 1-leaf rectangle out of a scan, based on the (row, column) coordinate
	"""
	return scan[row * dx : (row + 1) * dx, column * dy: (column + 1) * dy]

def overlay(img1, img2):
	"""
	Overlays two images, here with hard coded alpha of 0.9
	"""
	return cv2.addWeighted(img1, 0.1, crop_film,0.9,0)

def calculate_area(binary_img):
	"""
	Returns the area (in px) of the white area of an img. Other functions return 'selected' area as a white mask.
	"""
	return np.sum(binary_img == 255)

def find_bacteria(scan_crop, leaf_mask, threshold):
	"""
	Calculates the area of bacterial signal in a leaf, in pixels.
	Uses a threshold to determine when we count the signal 'detected' or not.
	Uses the mask of the leaf to exclude any signal outside leaf area.
	"""
	black = np.zeros((dx,dy),np.uint8)

	# Invert the bacterial signal to make it white
	scan_grey = ~cv2.cvtColor(scan_crop, cv2.COLOR_BGR2GRAY)

	# Mask the leaf area
	scan_masked = cv2.bitwise_and(scan_grey, scan_grey, mask = leaf_mask)

	# Select pixels that cross a threshold
	bacteria_mask = ~cv2.inRange(scan_masked, 0, threshold)

	# Find and draw contour of the leaf
	contours, hierarchy = cv2.findContours(leaf_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
	if len(contours) != 0:
		for contour in contours:
			cv2.drawContours(scan_crop,[contour], 0, (0,100,255), thickness=6)

	# Find all contours of the bacteria
	contours, hierarchy = cv2.findContours(bacteria_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	if len(contours) != 0:
		for contour in contours:
			cv2.drawContours(scan_crop,[contour], 0, (150,0,255), thickness=4)

	return bacteria_mask, scan_crop

def find_chlorosis(scan_crop, leaf_mask):
	"""
	Finds chlorotic regions of a leaf, returns this area, a mask of that area, and an image where we draw the borders of chlorotic areas.
	"""
	imgHSV = cv2.cvtColor(scan_crop, cv2.COLOR_BGR2HSV)
	imgHSV_masked = cv2.bitwise_and(imgHSV, imgHSV, mask=leaf_mask)
	scan_crop_masked = cv2.bitwise_and(scan_crop, scan_crop, mask=leaf_mask)

	# draw the leaf contour
	contours, hierarchy = cv2.findContours(leaf_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
	if len(contours) != 0:
		for contour in contours:
			cv2.drawContours(scan_crop,[contour], 0, (0,100,255), thickness=6)

	# experimentally picked values, could be further optimized
	lower_range = np.array([12,50,170])
	upper_range = np.array([37,210,255])

	yellow = cv2.inRange(imgHSV_masked,lower_range,upper_range)

	# find all contours of yellow leaf area
	contours, hierarchy = cv2.findContours(yellow, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
	chlorosis_area = 0
	chlorosis_mask = np.zeros((dx,dy),np.uint8)

	if len(contours) != 0:
		for contour in contours:
			# calculate area and draw contours
			chlorosis_area += cv2.contourArea(contour)
			cv2.drawContours(scan_crop,[contour], 0, (255,255,0), thickness=4)

			# also draw a mask
			cv2.drawContours(chlorosis_mask, [contour], -1, 255, -1)

	return chlorosis_mask, chlorosis_area, scan_crop

def find_leaf(img):
	"""
	Finds the green and yellow parts of an image, i.e.: the leaves.

	Based on Gerrit Hardemans original script
	"""
	imgHSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
	lower_range = np.array([0,0,0])
	upper_range = np.array([255,75,255])   #

	# Create a mask of the image using the range threshold above
	yellow_green = ~cv2.inRange(imgHSV,lower_range,upper_range)
	output = cv2.bitwise_and(img, img, mask=yellow_green)

	# Find all contours (this includes both the leaf, and some soil particles in some cases)
	contours, hierarchy = cv2.findContours(yellow_green, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	if len(contours) != 0:
		# Select biggest contour in this image (this is always the leaf, and gets rid of e.g. soil particles), mask original image only with this contour
		leaf_mask = np.zeros((dx,dy),np.uint8)
		cv2.drawContours(leaf_mask, [max(contours, key = cv2.contourArea)], -1,(255), -1)

		return leaf_mask

	# TODO: implement some minimal size of the leaf, and if not: return NA or a completely masked image.

def read_metadata(filepath):
	"""
	Reads a bioassay metadata file (.csv) with bioassaynumber, date, dpi, and the grid layout
	"""
	with open(filepath) as f:
		csvraw = list(csv.reader(f, delimiter = ','))

	bioassay = csvraw[0][1]
	dpi = csvraw[1][1]
	date_sampling = csvraw[2][1]

	# Some numpy slicing to get rid of row and column numbers
	# TODO (low priority): there are too many hardcoded values here, will not work with other grid sizes
	genotypes = np.array(csvraw[4:12])[1:,1:]
	pathogens = np.array(csvraw[13:21])[1:,1:]
	treatments = np.array(csvraw[22:30])[1:,1:]
	bioassays = np.array(csvraw[31:39])[1:,1:]
	dpis = np.array(csvraw[40:48])[1:,1:]

	# TODO (low priority): this could perhaps b returned as an object, or a tuple, but this works for now
	return bioassay, dpi, date_sampling, bioassays, dpis, genotypes, pathogens, treatments

#### Main program
if __name__ == "__main__":

	# Parse command line arguments
	parser = argparse.ArgumentParser(description='ScAnalyzer v0.1')
	parser.add_argument('-leaves', required=True, type=lambda x: is_valid_file(parser, x), help='The scan of the leaves (.jpg)')
	parser.add_argument('-film', type=lambda x: is_valid_file(parser, x), required=True, help='The scan of the film displaying bacterial presence (.jpg)')
	parser.add_argument('-samples', type=lambda x: is_valid_file(parser, x), required=True, help='The samplelist (.csv)')
	parser.add_argument('-prefix', required=True, help='Prefix for the output files')
	parser.add_argument('--autoplot', action='store_true', help='Activate autoplot function')
	args = parser.parse_args()

	# Open the different image files and the samplelist
	leaves = cv2.imread(args.leaves)
	film = cv2.imread(args.film)
	sample_list = args.samples

	bioassay, dpi, date_sampling, bioassays, dpis, genotypes, pathogens, treatments = read_metadata(sample_list)

	# Prepare some empty lists
	data_rows = []
	leaves_annotated_collage = []
	film_annotated_collage = []

	# Looping through the grid by columns and rows
	for c in range(0,ncols):
		leaves_annotated = []
		film_annotated = []

		for r in range(0,nrows):
			crop_leaf = crop(leaves, c, r)
			crop_film = crop(film, c, r)

			# Get a mask that contains the leaf
			leaf_mask = find_leaf(crop_leaf)
			leaf_area = calculate_area(leaf_mask)

			# Get the area of the leaf colonized by bacterial signal
			# Potential improvement: improve hard coded 128 threshold here --> actually also to HSV color space?
			bacteria_mask, bacteria_annotated = find_bacteria(crop_film,leaf_mask, 126)
			bacteria_area = calculate_area(bacteria_mask)

			# Get the area of the leaf that is chlorotic
			yellow_mask, yellow_area, yellow_annotated = find_chlorosis(crop_leaf, leaf_mask)

			leaves_annotated.append(yellow_annotated)
			film_annotated.append(bacteria_annotated)

			# Here we save each data row, with a rough hardcoded minimum size of the leaf
			if leaf_area > 400:
				data_row = [str(c + 1), str(nrows - r), bioassays[nrows-r-1][c], dpis[nrows-r-1][c], genotypes[nrows-r-1][c], pathogens[nrows-r-1][c], treatments[nrows-r-1][c], leaf_area, bacteria_area, yellow_area]
			else:
				data_row = [str(c + 1), str(nrows - r), bioassays[nrows-r-1][c], dpis[nrows-r-1][c], genotypes[nrows-r-1][c], pathogens[nrows-r-1][c], treatments[nrows-r-1][c],"NA","NA","NA"]

			data_rows.append(data_row)


		# Concatenate a row of analyzed pictues
		row_leaves = cv2.hconcat(leaves_annotated)
		leaves_annotated_collage.append(row_leaves)
		row_film = cv2.hconcat(film_annotated)
		film_annotated_collage.append(row_film)

	# Concatename columns of analyzed pictures
	leaves_collage = cv2.vconcat(leaves_annotated_collage)
	film_collage = cv2.vconcat(film_annotated_collage)

	# Save data file, and analyzed picture collages
	# TODO: automate filenames
	cv2.imwrite(args.prefix+"_leaves_processed.png", leaves_collage)
	cv2.imwrite(args.prefix+"_film_processed.png", film_collage)

	data_writer(args.prefix+"_data.csv", data_rows)

	# Call R autoplotter
	if args.autoplot:
		subprocess.call("Rscript autoplotter.R "+args.prefix+"_data.csv", shell=True)
