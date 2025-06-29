import cv2
import numpy as np
import math
import tkinter as tk
import os
import time
import tracker

# Crop the image to maintain a specific aspect ratio (width:height) before resizing. 
def crop_to_aspect_ratio(image, width=640, height=480):
    
    # Calculate current aspect ratio
    current_height, current_width = image.shape[:2]
    desired_ratio = width / height
    current_ratio = current_width / current_height

    if current_ratio > desired_ratio:
        # Current image is too wide
        new_width = int(desired_ratio * current_height)
        offset = (current_width - new_width) // 2
        cropped_img = image[:, offset:offset+new_width]
    else:
        # Current image is too tall
        new_height = int(current_width / desired_ratio)
        offset = (current_height - new_height) // 2
        cropped_img = image[offset:offset+new_height, :]

    return cv2.resize(cropped_img, (width, height))

#apply thresholding to an image
def apply_binary_threshold(image, darkestPixelValue, addedThreshold):
    # Calculate the threshold as the sum of the two input values
    threshold = darkestPixelValue + addedThreshold
    # Apply the binary threshold
    _, thresholded_image = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY_INV)
    
    return thresholded_image

#Finds a square area of dark pixels in the image
#@param I input image (converted to grayscale during search process)
#@return a point within the pupil region

def get_darkest_area(image):
    if image is None:
        print("Error: Image not loaded properly")
        return None

    ignoreBounds = 20
    imageSkipSize = 10
    searchArea = 20
    internalSkipSize = 5
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    min_sum = float('inf')
    darkest_point = None

    # Loop over the image with spacing defined by imageSkipSize, ignoring the boundaries
    for y in range(ignoreBounds, gray.shape[0] - ignoreBounds - searchArea, imageSkipSize):
        for x in range(ignoreBounds, gray.shape[1] - ignoreBounds - searchArea, imageSkipSize):
            # Draw a rectangle on the color image to visualize the block
            #top_left = (x, y)
            #bottom_right = (x + searchArea, y + searchArea)
            #cv2.rectangle(gray, top_left, bottom_right, (0, 0, 255), imageSkipSize)
            # Display the image with the drawn rectangles
            #cv2.imshow("Grayscale Image for darkest area get", gray)
            #cv2.waitKey(1)  # Wait for 200 milliseconds to see the rectangles

            current_sum = 0
            num_pixels = 0
            for dy in range(0, searchArea, internalSkipSize):
                if (y + dy) >= gray.shape[0]:
                    break
                for dx in range(0, searchArea, internalSkipSize):
                    if (x + dx) >= gray.shape[1]:
                        break

                    current_sum = current_sum + gray[y + dy,x + dx].astype(np.int32)
                    num_pixels += 1

            # Update the darkest point if the current block is darker
            if current_sum < min_sum and num_pixels > 0:
                min_sum = current_sum
                darkest_point = (x + searchArea // 2, y + searchArea // 2)  # Center of the block
            
    return darkest_point

#mask all pixels outside a square defined by center and size
def mask_outside_square(image, center, size):
    x, y = center
    half_size = size // 2

    # Create a mask initialized to black
    mask = np.zeros_like(image)

    # Calculate the top-left corner of the square
    top_left_x = max(0, x - half_size)
    top_left_y = max(0, y - half_size)

    # Calculate the bottom-right corner of the square
    bottom_right_x = min(image.shape[1], x + half_size)
    bottom_right_y = min(image.shape[0], y + half_size)

    # Set the square area in the mask to white
    mask[top_left_y:bottom_right_y, top_left_x:bottom_right_x] = 255

    # Apply the mask to the image
    masked_image = cv2.bitwise_and(image, mask)

    return masked_image
   
def optimize_contours_by_angle(contours, image):
    if len(contours) < 1:
        return contours

    # Holds the candidate points
    all_contours = np.concatenate(contours[0], axis=0)

    # Set spacing based on size of contours
    spacing = int(len(all_contours)/25)  # Spacing between sampled points

    # Temporary array for result
    filtered_points = []
    
    # Calculate centroid of the original contours
    centroid = np.mean(all_contours, axis=0)
    
    # Create an image of the same size as the original image
    point_image = image.copy()
    
    skip = 0
    
    # Loop through each point in the all_contours array
    for i in range(0, len(all_contours), 1):
    
        # Get three points: current point, previous point, and next point
        current_point = all_contours[i]
        prev_point = all_contours[i - spacing] if i - spacing >= 0 else all_contours[-spacing]
        next_point = all_contours[i + spacing] if i + spacing < len(all_contours) else all_contours[spacing]
        
        # Calculate vectors between points
        vec1 = prev_point - current_point
        vec2 = next_point - current_point
        
        with np.errstate(invalid='ignore'):
            # Calculate angles between vectors
            angle = np.arccos(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

        
        # Calculate vector from current point to centroid
        vec_to_centroid = centroid - current_point
        
        # Check if angle is oriented towards centroid
        # Calculate the cosine of the desired angle threshold (e.g., 80 degrees)
        cos_threshold = np.cos(np.radians(60))  # Convert angle to radians
        
        if np.dot(vec_to_centroid, (vec1+vec2)/2) >= cos_threshold:
            filtered_points.append(current_point)
    
    return np.array(filtered_points, dtype=np.int32).reshape((-1, 1, 2))

#returns the largest contour that is not extremely long or tall
#contours is the list of contours, pixel_thresh is the max pixels to filter, and ratio_thresh is the max ratio
def filter_contours_by_area_and_return_largest(contours, pixel_thresh, ratio_thresh):
    max_area = 0
    largest_contour = None
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area >= pixel_thresh:
            x, y, w, h = cv2.boundingRect(contour)
            length = max(w, h)
            width = min(w, h)

            # Calculate the length-to-width ratio and width-to-length ratio
            length_to_width_ratio = length / width
            width_to_length_ratio = width / length

            # Pick the higher of the two ratios
            current_ratio = max(length_to_width_ratio, width_to_length_ratio)

            # Check if highest ratio is within the acceptable threshold
            if current_ratio <= ratio_thresh:
                # Update the largest contour if the current one is bigger
                if area > max_area:
                    max_area = area
                    largest_contour = contour

    # Return a list with only the largest contour, or an empty list if no contour was found
    if largest_contour is not None:
        return [largest_contour]
    else:
        return []

#Fits an ellipse to the optimized contours and draws it on the image.
def fit_and_draw_ellipses(image, optimized_contours, color):
    if len(optimized_contours) >= 5:
        # Ensure the data is in the correct shape (n, 1, 2) for cv2.fitEllipse
        contour = np.array(optimized_contours, dtype=np.int32).reshape((-1, 1, 2))

        # Fit ellipse
        ellipse = cv2.fitEllipse(contour)

        # Draw the ellipse
        cv2.ellipse(image, ellipse, color, 2)  # Draw with green color and thickness of 2

        return image
    else:
        print("Not enough points to fit an ellipse.")
        return image

#checks how many pixels in the contour fall under a slightly thickened ellipse
#also returns that number of pixels divided by the total pixels on the contour border
#assists with checking ellipse goodness    
def check_contour_pixels(contour, image_shape, debug_mode_on):
    # Check if the contour can be used to fit an ellipse (requires at least 5 points)
    if len(contour) < 5:
        return [0, 0]  # Not enough points to fit an ellipse
    
    # Create an empty mask for the contour
    contour_mask = np.zeros(image_shape, dtype=np.uint8)
    # Draw the contour on the mask, filling it
    cv2.drawContours(contour_mask, [contour], -1, (255), 1)
   
    # Fit an ellipse to the contour and create a mask for the ellipse
    ellipse_mask_thick = np.zeros(image_shape, dtype=np.uint8)
    ellipse_mask_thin = np.zeros(image_shape, dtype=np.uint8)
    ellipse = cv2.fitEllipse(contour)
    
    # Draw the ellipse with a specific thickness
    cv2.ellipse(ellipse_mask_thick, ellipse, (255), 10) #capture more for absolute
    cv2.ellipse(ellipse_mask_thin, ellipse, (255), 4) #capture fewer for ratio

    # Calculate the overlap of the contour mask and the thickened ellipse mask
    overlap_thick = cv2.bitwise_and(contour_mask, ellipse_mask_thick)
    overlap_thin = cv2.bitwise_and(contour_mask, ellipse_mask_thin)
    
    # Count the number of non-zero (white) pixels in the overlap
    absolute_pixel_total_thick = np.sum(overlap_thick > 0)#compute with thicker border
    absolute_pixel_total_thin = np.sum(overlap_thin > 0)#compute with thicker border
    
    # Compute the ratio of pixels under the ellipse to the total pixels on the contour border
    total_border_pixels = np.sum(contour_mask > 0)
    
    ratio_under_ellipse = absolute_pixel_total_thin / total_border_pixels if total_border_pixels > 0 else 0
    
    return [absolute_pixel_total_thick, ratio_under_ellipse, overlap_thin]

#outside of this method, select the ellipse with the highest percentage of pixels under the ellipse 
#TODO for efficiency, work with downscaled or cropped images
def check_ellipse_goodness(binary_image, contour, debug_mode_on):
    ellipse_goodness = [0,0,0] #covered pixels, edge straightness stdev, skewedness   
    # Check if the contour can be used to fit an ellipse (requires at least 5 points)
    if len(contour) < 5:
        print("length of contour was 0")
        return 0  # Not enough points to fit an ellipse
    
    # Fit an ellipse to the contour
    ellipse = cv2.fitEllipse(contour)
    
    # Create a mask with the same dimensions as the binary image, initialized to zero (black)
    mask = np.zeros_like(binary_image)
    
    # Draw the ellipse on the mask with white color (255)
    cv2.ellipse(mask, ellipse, (255), -1)
    
    # Calculate the number of pixels within the ellipse
    ellipse_area = np.sum(mask == 255)
    
    # Calculate the number of white pixels within the ellipse
    covered_pixels = np.sum((binary_image == 255) & (mask == 255))
    
    # Calculate the percentage of covered white pixels within the ellipse
    if ellipse_area == 0:
        print("area was 0")
        return ellipse_goodness  # Avoid division by zero if the ellipse area is somehow zero
    
    #percentage of covered pixels to number of pixels under area
    ellipse_goodness[0] = covered_pixels / ellipse_area
    
    #skew of the ellipse (less skewed is better?) - may not need this
    axes_lengths = ellipse[1]  # This is a tuple (minor_axis_length, major_axis_length)
    major_axis_length = axes_lengths[1]
    minor_axis_length = axes_lengths[0]
    ellipse_goodness[2] = min(ellipse[1][1]/ellipse[1][0], ellipse[1][0]/ellipse[1][1])
    
    return ellipse_goodness

def process_frames(prev_threshold_index, threshold_swtich_confidence_margin, 
                   thresholded_image_strict, thresholded_image_medium, thresholded_image_relaxed, 
                   frame, gray_frame, darkest_point, track_darkest_point, 
                   debug_mode_on, render_cv_window, 
                   lock_mode_on, lockpos_threshold,
                   arduino, prev_command
                   ):
    """

    
    """
    final_rotated_rect = ((0,0),(0,0),0)

    image_array = [thresholded_image_relaxed, thresholded_image_medium, thresholded_image_strict] #holds images
    name_array = ["relaxed", "medium", "strict"] #for naming windows
    final_image = image_array[0] #holds return array
    final_contours = [] #holds final contours
    ellipse_reduced_contours = [] #holds an array of the best contour points from the fitting process
    goodness = [] # goodness arr for to store goodness for all ellipse
    best_array = 0 
    kernel_size = 5  # Size of the kernel (5x5)
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    gray_copy1 = gray_frame.copy()
    gray_copy2 = gray_frame.copy()
    gray_copy3 = gray_frame.copy()
    gray_copies = [gray_copy1, gray_copy2, gray_copy3]
    final_goodness = 0

    best_image_threshold_index = 1
    
    #iterate through binary images and see which fits the ellipse best
    for i in range(1,4):
        # Dilate the binary image
        dilated_image = cv2.dilate(image_array[i-1], kernel, iterations=2)#medium
        
        # Find contours
        contours, hierarchy = cv2.findContours(dilated_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Create an empty image to draw contours
        contour_img2 = np.zeros_like(dilated_image)
        reduced_contours = filter_contours_by_area_and_return_largest(contours, 1000, 3)

        if len(reduced_contours) > 0 and len(reduced_contours[0]) > 5:
            current_goodness = check_ellipse_goodness(dilated_image, reduced_contours[0], debug_mode_on)
            gray_copy = gray_frame.copy()
            cv2.drawContours(gray_copies[i-1], reduced_contours, -1, (255), 1)
            ellipse = cv2.fitEllipse(reduced_contours[0])
            if debug_mode_on: #show contours 
                cv2.imshow(name_array[i-1] + " threshold", gray_copies[i-1])
                
            #in total pixels, first element is pixel total, next is ratio
            total_pixels = check_contour_pixels(reduced_contours[0], dilated_image.shape, debug_mode_on)                 
            
            cv2.ellipse(gray_copies[i-1], ellipse, (255, 0, 0), 2)  # Draw with specified color and thickness of 2
            font = cv2.FONT_HERSHEY_SIMPLEX  # Font type
            
            current = current_goodness[0]*total_pixels[0]*total_pixels[0]*total_pixels[1]
            
            #show intermediary images with text output
            if debug_mode_on:
                cv2.putText(gray_copies[i-1], "%filled:     " + str(current_goodness[0])[:5] + " (percentage of filled contour pixels inside ellipse)", (10,30), font, .55, (255,255,255), 1) #%filled
                cv2.putText(gray_copies[i-1], "abs. pix:   " + str(total_pixels[0]) + " (total pixels under fit ellipse)", (10,50), font, .55, (255,255,255), 1    ) #abs pix
                cv2.putText(gray_copies[i-1], "pix ratio:  " + str(total_pixels[1]) + " (total pix under fit ellipse / contour border pix)", (10,70), font, .55, (255,255,255), 1    ) #abs pix
                cv2.putText(gray_copies[i-1], "final:     " + str(current) + " (filled*ratio)", (10,90), font, .55, (255,255,255), 1) #skewedness
                cv2.imshow(name_array[i-1] + " threshold", image_array[i-1])
                cv2.imshow(name_array[i-1], gray_copies[i-1])
        
            goodness.append(current)
            ellipse_reduced_contours.append(total_pixels[2])
            final_contours.append(reduced_contours)

            # If the current iteration has the best goodness set it as best_image_threshold_index
            if current > 0 and current == max(current, final_goodness): 
                best_image_threshold_index = i-1
                final_goodness = current
                
        else:
            goodness.append(0)
            ellipse_reduced_contours.append([])
            final_contours.append([])

        
    # Confidence-Based Threshold Switching, to prevent flickering caused by toggling between thresholds, only switch if goodness difference btw thres is significant
    # If the threshold index used in the previous frame and cur frame are not the same, apply confidence check
    if best_image_threshold_index != prev_threshold_index:
        # Assign the current goodness of prev_threshold_index to prev_goodness
        prev_goodness = goodness[prev_threshold_index] if prev_threshold_index >= 0 else 0
    
        # If the best_image index's goodness is better than prev_goodness by the stipluted margin, switch images, else dont 
        if goodness[best_image_threshold_index] > prev_goodness * (1 + threshold_swtich_confidence_margin):
            print("Changed prev_threshold_index ", prev_threshold_index, " prev_goodness ", prev_goodness, " cur index ", best_image_threshold_index, " goodness ", goodness[best_image_threshold_index])
            prev_threshold_index = best_image_threshold_index


    ellipse_reduced_contours = ellipse_reduced_contours[prev_threshold_index]
    final_contours = final_contours[prev_threshold_index]
    final_image = dilated_image

    if debug_mode_on:
        # Ensure ellipse_reduced_contours is a valid image
        if isinstance(ellipse_reduced_contours, np.ndarray):
            cv2.imshow("Reduced contours of best thresholded image", ellipse_reduced_contours)
        else:
            print("Error: ellipse_reduced_contours is not a valid image.")
            print("type ellipse_reduced_contours", type(ellipse_reduced_contours))
            print("ellipse_reduced_contours", ellipse_reduced_contours)

    # If darkest point position hover around a particular location for more than 5 seconds, or if "L" is pressed then lockpos
    if lock_mode_on:
            print("lock_mode_on running,  track_darkest_pt ", track_darkest_point,  " darkest_point ", darkest_point)
            if (track_darkest_point == -1):
                print("setting")
                track_darkest_point = darkest_point
            else:
                euclid_dist =  math.dist(track_darkest_point, darkest_point) 
                print("mathing, euclid dist: ", euclid_dist)
                frame, prev_command = lockpos(frame, final_contours, euclid_dist, lockpos_threshold, arduino, prev_command)

    test_frame = frame.copy()
    
    final_contours = [optimize_contours_by_angle(final_contours, gray_frame)]
    
    if final_contours and not isinstance(final_contours[0], list) and len(final_contours[0] > 5):
        #cv2.drawContours(test_frame, final_contours, -1, (255, 255, 255), 1)
        ellipse = cv2.fitEllipse(final_contours[0])
        final_rotated_rect = ellipse
        #cv2.circle(test_frame, darkest_point, 3, (255, 125, 125), -1)
        center_x, center_y = map(int, ellipse[0])
        cv2.circle(test_frame, (center_x, center_y), 3, (255, 255, 0), -1)
        cv2.putText(test_frame, "SPACE = play/pause", (10,410), cv2.FONT_HERSHEY_SIMPLEX, .55, (255,90,30), 2) #space
        cv2.putText(test_frame, "Q      = quit", (10,430), cv2.FONT_HERSHEY_SIMPLEX, .55, (255,90,30), 2) #quit
        cv2.putText(test_frame, "D      = show debug", (10,450), cv2.FONT_HERSHEY_SIMPLEX, .55, (255,90,30), 2) #debug

        if lock_mode_on == False:
            cv2.ellipse(test_frame, ellipse, (255, 0, 0), 2)

    if render_cv_window:
        cv2.imshow('best_thresholded_image_contours_on_frame', test_frame)
    
    # Create an empty image to draw contours
    contour_img3 = np.zeros_like(image_array[i-1])
    
    if len(final_contours[0]) >= 5:
        contour = np.array(final_contours[0], dtype=np.int32).reshape((-1, 1, 2)) #format for cv2.fitEllipse
        ellipse = cv2.fitEllipse(contour) # Fit ellipse
        cv2.ellipse(gray_frame, ellipse, (255,255,255), 2)  # Draw with white color and thickness of 2

    #process_frames now returns a rotated rectangle for the ellipse for easy access
    return final_rotated_rect, final_contours, prev_threshold_index, prev_command


# Finds the pupil in an individual frame and returns the center point
def process_frame(frame):

    # Crop and resize frame
    frame = crop_to_aspect_ratio(frame)

    #find the darkest point
    darkest_point = get_darkest_area(frame)

    # Convert to grayscale to handle pixel value operations
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    darkest_pixel_value = gray_frame[darkest_point[1], darkest_point[0]]
    
    # apply thresholding operations at different levels
    # at least one should give us a good ellipse segment
    thresholded_image_strict = apply_binary_threshold(gray_frame, darkest_pixel_value, 5)#lite
    thresholded_image_strict = mask_outside_square(thresholded_image_strict, darkest_point, 250)

    thresholded_image_medium = apply_binary_threshold(gray_frame, darkest_pixel_value, 15)#medium
    thresholded_image_medium = mask_outside_square(thresholded_image_medium, darkest_point, 250)
    
    thresholded_image_relaxed = apply_binary_threshold(gray_frame, darkest_pixel_value, 25)#heavy
    thresholded_image_relaxed = mask_outside_square(thresholded_image_relaxed, darkest_point, 250)
    
    #take the three images thresholded at different levels and process them
    final_rotated_rect, final_contours = process_frames(thresholded_image_strict, thresholded_image_medium, thresholded_image_relaxed, frame, gray_frame, darkest_point, -1, False, False, False, 5)
    
    return final_rotated_rect, final_contours

def process_video(video_path, input_method, zoom_factor=5, zoom_center=None, lockpos_threshold=5, arduino_port=None, threshold_swtich_confidence_margin=1):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for MP4 format
    out = cv2.VideoWriter('C:/Storage/Source Videos/output_video.mp4', fourcc, 30.0, (640, 480))  # Output video filename, codec, frame rate, and frame size

    if input_method == 1:
        cap = cv2.VideoCapture(video_path)
    elif input_method == 2:
        cap = cv2.VideoCapture(0)  # Camera input
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2048) # Resolution set to 2k (2048, 1080)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        cap.set(cv2.CAP_PROP_EXPOSURE, 0)
    else:
        print("Invalid video source.")
        return

    if not cap.isOpened():
        print("Error: Could not open video.")
        return
    
    debug_mode_on = False
    lock_mode_on = False
    track_darkest_point = -1

    # Track last index used, use to implement Confidence-Based Threshold Switching btw threshold to reduce flickering
    prev_threshold_index = 0

    # Track last command sent to arduino, only send command if there is a change in command
    prev_command = 'L'

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Crop and resize frame
        frame = crop_to_aspect_ratio(frame)

        # Apply zoom effect
        frame = zoom_frame(frame, zoom_factor, zoom_center)

        # Find the darkest point
        darkest_point = get_darkest_area(frame)

        if debug_mode_on:
            darkest_image = frame.copy()
            cv2.circle(darkest_image, darkest_point, 10, (0, 0, 255), -1)
            cv2.imshow('Darkest image patch', darkest_image)

        # Convert to grayscale to handle pixel value operations
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        darkest_pixel_value = gray_frame[darkest_point[1], darkest_point[0]]
        
        # Apply thresholding operations at different levels
        thresholded_image_strict = apply_binary_threshold(gray_frame, darkest_pixel_value, 5)  # lite
        thresholded_image_strict = mask_outside_square(thresholded_image_strict, darkest_point, 250)

        thresholded_image_medium = apply_binary_threshold(gray_frame, darkest_pixel_value, 15)  # medium
        thresholded_image_medium = mask_outside_square(thresholded_image_medium, darkest_point, 250)
        
        thresholded_image_relaxed = apply_binary_threshold(gray_frame, darkest_pixel_value, 25)  # heavy
        thresholded_image_relaxed = mask_outside_square(thresholded_image_relaxed, darkest_point, 250)
        
        # Take the three images thresholded at different levels and process them
        print("lock_mode ", lock_mode_on)
        pupil_rotated_rect, final_contours, threshold_index, prev_command = process_frames(prev_threshold_index, threshold_swtich_confidence_margin, thresholded_image_strict, thresholded_image_medium, thresholded_image_relaxed, frame, gray_frame, darkest_point, track_darkest_point, debug_mode_on, True, lock_mode_on, lockpos_threshold, arduino_port, prev_command)

        # Set the current threshold being used as the prev threshold index, once image processed.
        prev_threshold_index = threshold_index

        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('d') and not debug_mode_on:
            debug_mode_on = True
        elif key == ord('d') and debug_mode_on:
            debug_mode_on = False
            cv2.destroyAllWindows()

        if key == ord('q'):
            break
        elif key == ord(' '):
            while True:
                key = cv2.waitKey(1) & 0xFF
                if key == ord(' '):
                    break
                elif key == ord('q'):
                    break
        if key == ord('l') and not lock_mode_on:
            print("Setting lock")
            track_darkest_point = darkest_point
            lock_mode_on = True
        elif key == ord('l') and lock_mode_on:
            print("Resetting lock")
            track_darkest_point = -1
            lock_mode_on = False

    arduino_port.close()
    cap.release()
    out.release()
    cv2.destroyAllWindows()

def zoom_frame(frame, zoom_factor, center=None):
    """
    Zooms into a specific area of the frame based on the zoom factor.
    
    :param frame: The input frame (image) to zoom into.
    :param zoom_factor: The factor by which to zoom. Values greater than 1 will zoom in.
    :param center: The center of the zoom. If None, zooms into the center of the frame.
    :return: The zoomed-in frame.
    """
    (h, w) = frame.shape[:2]
    
    if center is None:
        center = (w // 2, h // 2)
    
    # Calculate the new dimensions
    new_w = int(w / zoom_factor)
    new_h = int(h / zoom_factor)
    
    # Calculate the cropping box
    x = max(center[0] - new_w // 2, 0)
    y = max(center[1] - new_h // 2, 0)
    x2 = min(x + new_w, w)
    y2 = min(y + new_h, h)
    
    # Crop and resize the frame
    cropped_frame = frame[y:y2, x:x2]
    zoomed_frame = cv2.resize(cropped_frame, (w, h))
    
    return zoomed_frame

##Lockpos 
def lockpos(frame, final_contours, euclid_dist, lockpos_threshold, arduino_deets, prev_command):
    command = 'H'

    if final_contours != []:

        if (euclid_dist > lockpos_threshold):
            frame = fit_and_draw_ellipses(frame, final_contours[0], (255, 0, 0))
            #tracker.check_connection(arduino_deets)
            command = 'H'

            if arduino_deets:
                if tracker.buzzer(arduino_deets, 'H', prev_command) == 1:
                    print("HIGH command sent and acknowledged.")

                elif tracker.buzzer(arduino_deets, 'H', prev_command) == 2:
                    print("Prog Ended.")
                    return frame, command
                else:
                    print("Failed to send HIGH command or no acknowledgment received.")
            print("Out of thres")
            ##cv2.imshow('Darkest image patch', frame)
        else:
            command = 'L'

            frame = fit_and_draw_ellipses(frame, final_contours[0], (0, 255, 0))
            print("whithin threshold")
            if arduino_deets:
                if tracker.buzzer(arduino_deets, 'L', prev_command) == 1:
                    print("LOW command sent and acknowledged.")
                elif tracker.buzzer(arduino_deets, 'L', prev_command) == 2:
                    print("Prog Ended.")

                # Need to find a way to end the program, dicuss how to end the program
                return frame, command
            else:
                print("Failed to send LOW command or no acknowledgment received.")

        return frame, command
    
    return frame, command


#Prompts the user to select a video file if the hardcoded path is not found
#This is just for my debugging convenience :)

import os
def select_video():
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    video_path = './assets/eye_test.mp4'
    abs_path = os.path.abspath(video_path)    # Get absolute path
    print(abs_path)

    connect_to_arduino = False
    arduino_port = '/dev/cu.usbserial-120' #'/dev/cu.usbserial-130'
    baud_rate = 115200
    arduino_deets = [arduino_port, baud_rate]
    
    if connect_to_arduino:
        # Connect to Arduino
        time.sleep(1.5)
        arduino = tracker.connect_to_arduino(arduino_port,baud_rate)
        if arduino is None:
            print("Failed to connect to Arduino.")
            return
    else:
        arduino = None

    # if not os.path.exists(abs_path):
    #     print("No file found at hardcoded path. Please select a video file.")
    #     video_path = filedialog.askopenfilename(title="Select Video File", filetypes=[("Video Files", "*.mp4;*.avi")])
    #     if not video_path:
    #         print("No file selected. Exiting.")
    #         return
            
    # first parameter is for path of video
    # second parameter is 1 for video 2 for webcam
    # third parameter is for zoom_factor
    # fourth parameter is for zoom_center, none == (center,center)
    # fifth parameter is for lock_pos_threshold , old 90
    # six parameter is the arduino port
    # seven parameter is the threshold confidence 
    process_video(abs_path, input_method=2, zoom_factor=8, zoom_center=None, lockpos_threshold=48, arduino_port=arduino, threshold_swtich_confidence_margin=2)
    # process_video(abs_path, input_method=2, zoom_factor=8, zoom_center=None, lockpos_threshold=48, arduino_port=arduino, threshold_swtich_confidence_margin=2)

if __name__ == "__main__":
    select_video()


