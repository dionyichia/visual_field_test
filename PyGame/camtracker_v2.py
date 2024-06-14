# Webcam EyeTracker classes
# This version of cam_tracker identifies the subjects face and crops the image, from the cropped image, 
# identifies the subjects pupil and crops the image
# This aims to recreate the Melbourne Rapid Field Test Project


# in DEBUG mode, images of the calibration are saved as strings in a textfile,
# after the calibration, the textfile will be read and PNG images will be
# produced based on the content of the file
DEBUG = False
BUFFSEP = 'edwinisdebeste'


# # # # #
# imports

import os.path
import time
import numpy as np

# Try to import VideoCapture Library
# Requires VideoCapture & PIL libraries
vcAvailable = False
import importlib.util

try:
  importlib.util.find_spec('cv2')
  import cv2 as cv
  vcAvailable = True
except ImportError:
  print ("VideoCapture from OpenCV not available")

try:
	import pygame
	import pygame.camera
	pygame.init()
	pygame.camera.init()
except:
	raise Exception("Error in camtracker: PyGame could not be imported and initialized! :(")


# # # # #
# functions

def available_devices():
	
	"""Returns a list of available device names or numbers; each name or
	number can be used to pass as Setup's device keyword argument
	
	arguments
	None
	
	keyword arguments
	None
	
	returns
	devlist		--	a list of device names or numbers, e.g.
					['/dev/video0','/dev/video1'] or [0,1]
	"""
	
	return pygame.camera.list_cameras()
	

# # # # #
# classes

class Setup:
	
	"""The Setup class provides means to calibrate your webcam to function
	as an eye tracker"""
	
	def __init__(self, device=None, camres=(640,480), disptype='window', dispres=(1024,768), display=None):
		
		"""Initializes a Setup instance
		
		arguments
		None
		
		keyword arguments
		device		--	a string or an integer, indicating either
						device name (e.g. '/dev/video0'), or a
						device number (e.g. 0); None can be passed
						too, in this case Setup will autodetect a
						useable device (default = None)
		camres		--	the resolution of the webcam, e.g.
						(640,480) (default = (640,480))
		disptype		--	a string indicating what kind of
						calibration display should be presented;
						choose from 'window' (PyGame windowed),
						'fullscreen' (PyGame fullscreen)
						(default = 'window')
		dispres		--	the resolution of the display, e.g.
						(1280,1024) (default = 1024,768)
		display		--	pass None to let the Setup create its own
						display, otherwise pass a display that
						matches the disptype you provided (under
						the disptype argument) to let the Setup use
						that display; example: set disptype to
						'fullscreen', then pass a
						pygame.surface.Surface instance that is
						returned by pygame.display.set_mode:
						calibration will then be presented on the
						passed pygame.surface.Surface instance
		"""
		
		# DEBUG #
		if DEBUG:
			self.savefile = open('data/savefile.txt','w')
		# # # # #

		# create new Display if none was passed, or use the provided display
		if display == None:
			if disptype == 'window':
				self.disp = pygame.display.set_mode(dispres, pygame.RESIZABLE)
			elif disptype == 'fullscreen':
				self.disp = pygame.display.set_mode(dispres, pygame.FULLSCREEN|pygame.HWSURFACE|pygame.DOUBLEBUF)
			else:
				raise Exception("Error in camtracker.Setup.__init__: disptype '%s' was not recognized; please use 'window', 'fullscreen'")
		# if a display was specified, use that
		else:
			self.disp = display
			dispres = self.disp.get_size()
		
		# select a device if none was selected
		if device == None:
			available = available_devices()
			if available == []:
				raise Exception("Error in camtracker.Setup.__init__: no available camera devices found (did you forget to plug it in?)")
			else:
				device = available[0]
		
		# create new camera
		self.tracker = CamEyeTracker(device=device, camres=camres)
		
		# find font: first look in directory, if that fails we fall back to default
		try:
			fontname = os.path.join(os.path.split(os.path.abspath(__file__))[0],'resources','roboto_regular-webfont.ttf')
		except:
			fontname = pygame.font.get_default_font()
			print("WARNING: camtracker.Setup.__init__: could not find 'roboto_regular-webfont.ttf' in the resources directory!")
		# create a Font instance
		self.font = pygame.font.Font(fontname, 24)
		self.sfont = pygame.font.Font(fontname, 12)
		
		# set some properties
		self.disptype = disptype
		self.dispsize = dispres
		self.fgc = (255,255,255)
		self.bgc = (0,0,0)
		
		# fill display with background colour
		self.disp.fill(self.bgc)

		# set some more properties
		self.img = pygame.surface.Surface((self.tracker.get_size()))	# empty surface, gets filled out with camera images
		self.settings = {'pupilcol':(0,0,0), \
					'threshold':100, \
					'nonthresholdcol':(100,100,255,255), \
					'pupilpos': (camres[0]/2,camres[1]/2), \
					'pupilrect':pygame.Rect(camres[0]/2-50,camres[1]/2-25,100,50), \
					'pupilbounds': [0,0,0,0], \
					'':None					
					}
	
	
	def start(self):
		
		"""Starts running the GUI
		
		arguments
		None
		
		keyword arguments
		None
		
		returns
		None
		"""

		# show welcoming screen (loading...)
		self.show_welcome(loading=True)
		
		# DEBUG #
		if DEBUG:
			self.savefile.write(pygame.image.tostring(self.disp,'RGB')+BUFFSEP)
		# # # # #
		
		# create GUI
		self.setup_GUI()
		
		# replace 'loading' on welcoming screen with 'press any key to start'
		self.show_welcome(loading=False)
		
		# DEBUG #
		if DEBUG:
			self.savefile.write(pygame.image.tostring(self.disp,'RGB')+BUFFSEP)
		# # # # #
		
		# wait for keypress
		noinput = True
		while noinput:
			for event in pygame.event.get():
				if event.type == pygame.KEYDOWN:
					noinput = False
		
		# show welcoming screen (and we're loading again)
		self.show_welcome(loading=True)
		
		# DEBUG #
		if DEBUG:
			self.savefile.write(pygame.image.tostring(self.disp,'RGB')+BUFFSEP)
		# # # # #

		# draw general GUI (no stage information yet)
		self.draw_stage(stagenr=None)
		
		# DEBUG #
		if DEBUG:
			self.savefile.write(pygame.image.tostring(self.disp,'RGB')+BUFFSEP)
		# # # # #
		
		# mouse visibility
		pygame.mouse.set_visible(True)
		
		# start setup (should return a CamEyeTracker instance)
		tracker = self.run_GUI()
		
		return tracker
		
	
	def show_welcome(self, loading=False):
		
		"""Shows a welcoming screen with package and author information,
		either depecting "Loading, please wait..." or "Press any key to
		start", depending on the loading argument
		
		arguments
		None
		
		keyword arguments
		loading		--	Boolean indicating whether welcoming screen
						should say "Loading, please wait..." or
						"Press any key to start"

		returns
		None			--	directly draws on self.disp
		"""
		
		# welcome text
		welcometext = \
		"""Welcome to the Webcam EyeTracker calibration interface!
		
		author: Edwin Dalmaijer
		version: 0.1 (12-10-2013)
		
		
		
		"""
		
		# reset display
		self.disp.fill(self.bgc)
		
		# loading message
		if loading:
			welcometext += "Loading, please wait..."
		else:
			welcometext += "Press any key to start!"
		
		# remove tabs from text
		welcometext = welcometext.replace("\t","")
		
		# draw lines on display
		x = self.dispsize[0]/2; y = self.dispsize[0]/2
		lines = welcometext.split("\n")
		nlines = len(lines)
		for lnr in range(nlines):
			# render text
			linesize = self.font.size(lines[lnr])
			rendered = self.font.render(lines[lnr], True, self.fgc) # Font.render(text, antialias, color, background=None)
			# position
			pos = (x-linesize[0]/2, y + (lnr - nlines/2)*linesize[1])
			# draw to disp
			self.disp.blit(rendered, pos)

		# update!
		pygame.display.flip()
	
	
	def setup_GUI(self):
		
		"""Sets up a GUI interface within a PyGame Surface
		
		arguments
		None
		
		keyword arguments
		None
		
		returns
		None			--	returns nothing, but draws on self.disp and
						sets self.guisurface
		"""
		
		# directory
		resdir = os.path.join(os.path.split(os.path.abspath(__file__))[0],'resources')
		if not os.path.exists(resdir):
			raise Exception("Error in camtracker.Setup.setup_GUI: could not find 'resources' directory to access button images; was it relocated or renamed, or is the installation of camtracker incorrect?")
		
		# find image paths
		imgpaths = {}
		buttnames = ['1','2','3','up','down','t','space','r','escape','left','right']
		buttstates = ['active','inactive']
		for bn in buttnames:
			imgpaths[bn] = {}
			for bs in buttstates:
				filename = "%s_%s.png" % (bn,bs)
				imgpaths[bn][bs] = os.path.join(resdir,filename)
				if not os.path.isfile(imgpaths[bn][bs]):
					print("WARNING: image file '%s' was not found in resources!" % filename)
					imgpaths[bn][bs] = os.path.join(resdir,"blank_%s.png" % bs)
		
		# image positions (image CENTERS!)
		buttsize = (50,50)
		camres = self.tracker.get_size()
		buttpos = {}
		y = self.dispsize[1]/2 + int(camres[1]*0.6)
		buttpos['1'] = int(self.dispsize[0]*(2/6.0) - buttsize[0]/2), y
		buttpos['2'] = int(self.dispsize[0]*(3/6.0) - buttsize[0]/2), y
		buttpos['3'] = int(self.dispsize[0]*(4/6.0) - buttsize[0]/2), y
		buttpos['space'] = int(self.dispsize[0]*(5/6.0) - buttsize[0]/2), y
		
		leftx = self.dispsize[0]/2 - (camres[0]/2 + buttsize[0]) # center of the buttons on the right
		rightx = self.dispsize[0]/2 + camres[0]/2 + buttsize[0] # center of the buttons on the left
		buttpos['up'] = rightx, self.dispsize[1]/2-buttsize[1] # above snapshot half, to the right
		buttpos['down'] = rightx, self.dispsize[1]/2+buttsize[1] # below snapshot half, to the right
		buttpos['t'] = leftx, self.dispsize[1]/2+camres[1]/2-buttsize[1]/2 # same level as snapshot bottom, to the left
		buttpos['r'] = leftx, self.dispsize[1]/2 # halfway snapshot (==halfway display), to the left
		buttpos['escape'] = buttsize[0], buttsize[1] # top left

		#self-edits for the left and right button for stage2 
		buttpos['left'] = rightx+buttsize[1]+5, self.dispsize[1]/2-buttsize[1] # above snapshot half, to the right
		buttpos['right'] = rightx+buttsize[1]+5, self.dispsize[1]/2+buttsize[1] # below snapshot half, to the right
		
		# new dict for button properties (image, position, and rect)
		self.buttons = {}
		# loop through button names
		for bn in imgpaths.keys():
			# new dict for this button name
			self.buttons[bn] = {}
			# recalculate position
			buttpos[bn] = buttpos[bn][0]-buttsize[0]/2, buttpos[bn][1]-buttsize[1]/2
			# loop through button states
			for bs in imgpaths[bn].keys():
				# new dict for this button name and this button state
				self.buttons[bn][bs] = {}
				# load button image
				self.buttons[bn][bs]['img'] = pygame.image.load(imgpaths[bn][bs])
				# save position and rect
				self.buttons[bn][bs]['pos'] = buttpos[bn]
				self.buttons[bn][bs]['rect'] = buttpos[bn][0], buttpos[bn][1], buttsize[0], buttsize[1]
		
		# save buttsize
		self.buttsize = buttsize
	
	
	def draw_button(self, image, pos):
		
		"""Draws a button on the display
		
		arguments
		image			--	a pygame.surface.Surface instance, depicting
						a button
		pos			--	a (x,y) position coordinate, indicating the
						top left corner of the button
		
		keyword arguments
		None
		
		returns
		None			--	directly draws on self.disp
		"""
		
		self.disp.blit(image, pos)
	
	
	def draw_stage(self, stagenr=None):
		
		"""Draws the GUI window for the passed stage nr
		
		arguments
		None
		
		keyword arguments
		stagenr		--	None for only the basic buttons, or a stage
						number for the basic buttons, as well as the
						stage specific buttons
		
		returns
		None			--	directly draws on self.disp
		"""
		
		# clear display
		self.disp.fill(self.bgc)
		
		# universal buttons
		buttonstodraw = ['1','2','3','space','escape','t','r']
		activetodraw = []
		
		# stage specific buttons
		if stagenr == 1:
			title = "set pupil detection threshold"
			buttonstodraw.extend(['up','down'])
			activetodraw.extend(['1'])
		elif stagenr == 2:
			title = "select pupil and set pupil detection bounds"
			buttonstodraw.extend(['up','down','left','right'])
			activetodraw.extend(['2'])
		elif stagenr == 3:
			title = "confirmation"
			buttonstodraw.extend(['up','down'])
			activetodraw.extend(['3'])
		else:
			title = "loading, please wait..."

		# draw inactive buttons
		for buttname in buttonstodraw:
			self.draw_button(self.buttons[buttname]['inactive']['img'],self.buttons[buttname]['inactive']['pos'])
		
		# draw active buttons
		for buttname in activetodraw:
			self.draw_button(self.buttons[buttname]['active']['img'],self.buttons[buttname]['active']['pos'])
		
		# draw title
		titsize = self.font.size(title)
		titpos = self.dispsize[0]/2-titsize[0]/2, self.dispsize[1]/2-(self.tracker.get_size()[1]/2+titsize[1])
		titsurf = self.font.render(title, True, self.fgc)
		self.disp.blit(titsurf,titpos)

	def run_GUI(self):
		
		"""Perform a setup to set all settings using a GUI
		
		arguments
		None
		
		keyword arguments
		None
		
		returns
		None			--	returns nothing, but does fill in
						the self.settings dict
		"""
		
		# # # # #
		# variables
		
		# general
		stage = 1 # stage is updated by handle_input functions
		
		# stage specific
		stagevars = {}
		
		stagevars[0] = {}
		stagevars[0]['show_threshimg'] = False # False for showing snapshots, True for showing thresholded snapshots
		stagevars[0]['use_prect'] = True # False for no pupil search limits, True for pupil rect

		stagevars[1] =  {}
		stagevars[1]['thresholdchange'] = None # None, 'up', or 'down'
		
		stagevars[2] = {}
		stagevars[2]['clickpos'] = 0,0 # becomes a (x,y) tuple, indicating click position within the webcam's snapshots (to determine pupil rect)
		stagevars[2]['prectsize'] = 100,100 # pupilrectsize
		stagevars[2]['prect'] = pygame.Rect(stagevars[2]['clickpos'][0],stagevars[2]['clickpos'][1],stagevars[2]['prectsize'][0],stagevars[2]['prectsize'][1]) # rect around pupil, in which the pupil is expected to be
		stagevars[2]['vprectchange'] = None  # None, 'up', or 'down'
		stagevars[2]['hprectchange'] = None  # None, 'right', or 'left'
		
		stagevars[3] = {}
		stagevars[3]['confirmed'] = False

		stagevars[4] = {}
		stagevars[4]['locked'] = False

		stagevars[5] = {}
		stagevars[5]['re_calib'] = False

		# set Booleans
		running = True			# turns False upon quiting the GUI
		
		# set image variables, blitpos is the bottom left corner of the image frame 
		
		imgsize = self.img.get_size()
		blitpos = (self.dispsize[0]/2-imgsize[0]/2, self.dispsize[1]/2-imgsize[1]/2)
		
		# # # # #
		# run GUI
		locked_pos = []

		#Flag to cancel auto-calibraion
		start_auto_calibration = True

		while running:
			
			# # # # #
			# general

			# draw stage
			self.draw_stage(stagenr=stage)
			
			# get new snapshot, thresholded image, and pupil measures (only use pupil bounding rect after stage 1)
			useprect = stagevars[0]['use_prect'] and stage > 1
			print("useprect", useprect)
			self.img, self.thresholded, pupilpos, pupilsize, pupilbounds, facepos, facesize, facebounds = self.tracker.give_me_all(pupilrect=useprect)
			
			# update settings
			self.settings = self.tracker.settings
	
			# check if the thresholded image button is active
			if stagevars[0]['show_threshimg']:
				# draw active button
				self.draw_button(self.buttons['t']['active']['img'], self.buttons['t']['active']['pos'])
			# if threshold button is not active, draw inactive button
			else:
				self.draw_button(self.buttons['t']['inactive']['img'], self.buttons['t']['inactive']['pos'])
	
			# check if the thresholded image button is active
			if stagevars[0]['use_prect']:
				# draw active button
				self.draw_button(self.buttons['r']['active']['img'], self.buttons['r']['active']['pos'])
			# if threshold button is not active, draw inactive button
			else:
				self.draw_button(self.buttons['r']['inactive']['img'], self.buttons['r']['inactive']['pos'])

			if stagevars[4]['locked']:
				# draw active button
				self.draw_button(self.buttons['r']['active']['img'], self.buttons['r']['active']['pos'])
			# if threshold button is not active, draw inactive button
			else:
				self.draw_button(self.buttons['r']['inactive']['img'], self.buttons['r']['inactive']['pos'])

			if stagevars[5]['re_calib']:
				# draw active button
				self.draw_button(self.buttons['r']['active']['img'], self.buttons['r']['active']['pos'])
			# if threshold button is not active, draw inactive button
			else:
				self.draw_button(self.buttons['r']['inactive']['img'], self.buttons['r']['inactive']['pos'])


			# check for input
			inp, inptype = self.check_input()
			
			# handle input, according to the stage (this changes the stagevars!)
			stage, stagevars = self.handle_input(inptype, inp, stage, stagevars)
			
			# # # # #
			# stage specific

			""""""
			### Self-Edit: Auto Calibration Function
			pupil_detected = True

			print("facebounds ", facebounds, 'facepos', facepos, " pupilbounds ", pupilbounds, " pupilpos", pupilpos)

			if (facebounds == (-1,-1,-1,-1)) or (pupilpos == (0,0)) or (stagevars[5]['re_calib'] == True):
				if (self.settings['threshold'] < 200) and (stagevars[5]['re_calib'] == False):
					print("Increase threshold slightly to ensure detection")
					self.settings['threshold'] += 2
					start_auto_calibration = False
					print("up threshold",self.settings['threshold'])
				else:
					print("Reset Thres")
					self.settings['threshold'] = 100
					start_auto_calibration = True
					stagevars[5]['re_calib'] = False

				pupil_detected = False
			
			print("pupil_detected", pupil_detected)
			print(stage, pupil_detected, self.settings['threshold'])

			if (stage == 2) and (pupil_detected == True) and (self.settings['threshold'] < 254):
				print("legso")

				# Draw face rectangle in the image
				try:
					pygame.draw.rect(self.img, (0, 255, 0), facebounds, 1)
					pygame.draw.rect(self.thresholded, (0, 255, 0), facebounds, 1)
					print("this is facebounds ", facebounds)
					print("this is pupilpos ", pupilpos)
				except Exception as e:
					print(f"Error drawing facebounds: {e}")
				
				# Find and draw face position
				
				stagevars[2]['clickpos'] = facepos
				self.settings['pupilpos'] = stagevars[2]['clickpos'][:]
				print(stagevars[2]['clickpos'], self.settings['pupilpos'])

                #This adjusts the rough position of the blue box in the facebox (x,y) and the width adn height of the box 
				x = facepos[0] - stagevars[2]['prectsize'][0] / 1.5
				y = facepos[1] - stagevars[2]['prectsize'][1] / 3
				stagevars[2]['prect'] = pygame.Rect(x, y, (stagevars[2]['prectsize'][0])/2, (stagevars[2]['prectsize'][1])/3)
				self.settings['pupilrect'] = stagevars[2]['prect']
				print(self.settings['pupilrect'])
	

				print("self.settings['pupilrect']", self.settings['pupilrect'])
				# Try drawing pupil rectangle (blue) to check if it's detected
				try:
					pygame.draw.rect(self.thresholded, (0, 0, 255), self.settings['pupilrect'], 2)
					print(f"Threshold {self.settings['threshold']} - Face detected and drawn")
				except Exception as e:
					print(f"Threshold {self.settings['threshold']} - Face not detected: {e}")

				time.sleep(0.001)
			
				#facebounds = (bottomleftx, bottomlefty, width, height)
				x_coord = pupilpos[0]
				y_coord = pupilpos[1]
				x0_face = facebounds[0]
				x1_face = facebounds[0]+facebounds[2]
				y0_face = facebounds[1]
				y1_face = facebounds[1]+facebounds[3]

				print("this is pupilbounds ", pupilbounds)
				print("this is ppos ", pupilpos)

				#If pupil within facebox, assumed to be correctly identified, reduce threshold
				if (x0_face <= pupilpos[0] <= x1_face) & (y0_face <= pupilpos[1] <= y1_face):
					print("in facebox, thres at", self.settings['threshold'])
					
					if(start_auto_calibration == True):
						# Decrease threshold until the pupil is no longer detected i.e. recorded pupil position is outside face box
						self.settings['threshold'] -= 1
						print("down threshold",self.settings['threshold'])
					
				#If pupil not in facebox, assume not indentified, recalibrate
				else:
					print("not in facebox")
					start_auto_calibration = True
					pupil_detected = False

				# Draw pupil center and pupil bounds in the image 
				try:
					#Draw green eye rect
					pygame.draw.rect(self.img, (0, 255, 0), pupilbounds, 1)
					#Draw red pupil rect
					pygame.draw.rect(self.thresholded, (255, 0, 0), pupilbounds, 1)
				except Exception as e:
					print(f"Error drawing pupilbounds: {e}")

				try:
					pygame.draw.circle(self.img, (255, 0, 0), pupilpos, 3, 0)
					pygame.draw.circle(self.thresholded, (255, 0, 0), pupilpos, 3, 0)
				except Exception as e:
					print(f"Error drawing pupil position: {e}")

				# If settings are confirmed, stop running
				if stagevars[3]['confirmed']:
					running = False

				# Handle locked position logic
				if stagevars[4]['locked']:
					x_coord = pupilpos[0]
					y_coord = pupilpos[1]
					threshold_amount = 5  # Change this to adjust the threshold limit

					if locked_pos:
						threshold = list(locked_pos[0])
						if (x_coord > threshold[0] + threshold_amount) or (x_coord < threshold[0] - threshold_amount) or (y_coord > threshold[1] + threshold_amount) or (y_coord < threshold[1] - threshold_amount):
							# Draw a yellow box around threshold area
							try:
								pygame.draw.rect(self.img, (255, 255, 0), pupilbounds, 1)
								pygame.draw.rect(self.thresholded, (255, 255, 0), pupilbounds, 1)
							except Exception as e:
								print(f"Error drawing threshold pupilbounds: {e}")
					else:
						locked_pos.insert(0, pupilpos)
						print(f"Set pupilpos, locked_pos = {locked_pos}, length = {len(locked_pos)}")
				else:
					locked_pos = []

			#If pupil or face not detected, reset contrast threshold, try again			
			else:
				print("skipped")
				pass

            #This is the original code for manual calibration
			"""
			# stage 1: setting pupil threshold
			if stage == 1:
				# set camera threshold
				if stagevars[1]['thresholdchange'] != None:
					if stagevars[1]['thresholdchange'] == 'up' and self.settings['threshold'] < 255:
						self.settings['threshold'] += 1
					elif stagevars[1]['thresholdchange'] == 'down' and self.settings['threshold'] > 0:
						self.settings['threshold'] -= 1
					stagevars[1]['thresholdchange'] = None

				# draw face rect in image
				try: pygame.draw.rect(self.img, (0,255,0),facebounds,1); pygame.draw.rect(self.thresholded, (0,255,0),facebounds,1)
				except: print("facebounds=%s" % facebounds)
					

			# stage 2: select eye by clicking on it
			if stage == 2:
				# check if input is a mouse click
				if type(inp) in [tuple,list]:
					# check if mouse position is in image
					mpos = pygame.mouse.get_pos()
					hposok = mpos[0] > blitpos[0] and mpos[0] < blitpos[0]+imgsize[0]
					vposok = mpos[1] > blitpos[1] and mpos[1] < blitpos[1]+imgsize[1]
					if hposok and vposok:
						# set pupil position
						stagevars[2]['clickpos'] = inp[0]-blitpos[0], inp[1]-blitpos[1]
						self.settings['pupilpos'] = stagevars[2]['clickpos'][:]
						# set pupil rect
						x = stagevars[2]['clickpos'][0] - stagevars[2]['prectsize'][0]/2
						y = stagevars[2]['clickpos'][1] - stagevars[2]['prectsize'][1]/2
						stagevars[2]['prect'] = pygame.Rect(x,y,stagevars[2]['prectsize'][0],stagevars[2]['prectsize'][1])
						self.settings['pupilrect'] = stagevars[2]['prect']
				
				# if input was a key or button press
				elif stagevars[2]['vprectchange'] or stagevars[2]['hprectchange']:
					# change pupil rect size
					if stagevars[2]['vprectchange'] != None:
						if stagevars[2]['vprectchange'] == 'up':
							stagevars[2]['prectsize'] = stagevars[2]['prectsize'][0], stagevars[2]['prectsize'][1] + 1
						elif stagevars[2]['vprectchange'] == 'down':
							stagevars[2]['prectsize'] = stagevars[2]['prectsize'][0], stagevars[2]['prectsize'][1] - 1
						stagevars[2]['vprectchange'] = None
					if stagevars[2]['hprectchange'] != None:
						if stagevars[2]['hprectchange'] == 'right':
							stagevars[2]['prectsize'] = stagevars[2]['prectsize'][0] + 1, stagevars[2]['prectsize'][1]
						elif stagevars[2]['hprectchange'] == 'left':
							stagevars[2]['prectsize'] = stagevars[2]['prectsize'][0] - 1, stagevars[2]['prectsize'][1]
						stagevars[2]['hprectchange'] = None	
					# set pupil rect
					x = self.settings['pupilrect'][0]
					y = self.settings['pupilrect'][1]
					stagevars[2]['prect'] = pygame.Rect(x,y,stagevars[2]['prectsize'][0],stagevars[2]['prectsize'][1])
					self.settings['pupilrect'] = stagevars[2]['prect']

				# draw pupil rect
				pygame.draw.rect(self.img, (0,0,255), self.settings['pupilrect'], 2)
				pygame.draw.rect(self.thresholded, (0,0,255), self.settings['pupilrect'], 2)
			
			# stage 3: confirmation
			if stage == 3:
				# set camera threshold
				if stagevars[1]['thresholdchange'] != None:
					if stagevars[1]['thresholdchange'] == 'up' and self.settings['threshold'] < 255:
						self.settings['threshold'] += 1
					elif stagevars[1]['thresholdchange'] == 'down' and self.settings['threshold'] > 0:
						self.settings['threshold'] -= 1
					stagevars[1]['thresholdchange'] = None
				# draw pupil center and pupilbounds in image
				try: pygame.draw.rect(self.img, (0,255,0),pupilbounds,1); pygame.draw.rect(self.thresholded, (0,255,0),pupilbounds,1)
				except: print("pupilbounds=%s" % pupilbounds)
				try: pygame.draw.circle(self.img, (255,0,0),pupilpos,3,0); pygame.draw.circle(self.thresholded, (255,0,0),pupilpos,3,0)
				except: print("pupilpos=%s" % pupilpos)
				# is settings are confirmed, stop running
				if stagevars[3]['confirmed']:
					running = False
				
				#self-edits - to
				if stagevars[4]['locked']:
					x_coord = pupilpos[0]
					y_coord = pupilpos[1]
					threshold_amount = 5 # Change this to adjust the threshold limit
					if locked_pos:
						threshold = list(locked_pos[0])
						if (x_coord > threshold[0]+threshold_amount) or (x_coord < threshold[0]-threshold_amount) or (y_coord > threshold[1]+threshold_amount) or (y_coord < threshold[1]-threshold_amount):
							#Draw a yellow box around threshold area 
							try: pygame.draw.rect(self.img,(255,255,0),pupilbounds,1); pygame.draw.rect(self.thresholded,(255,255,0),pupilbounds,1)
							except: print("pupilbounds=%s" % pupilbounds)
					else: 
						locked_pos.insert(0 , pupilpos)
						print("set pupilpos, locked_pos = %s",locked_pos, len(locked_pos))
					
				else:
					locked_pos = []

			"""
			# EDIT HERE - EDIT HERE - EDIT HERE - EDIT HERE - EDIT HERE - EDIT HERE - EDIT HERE - EDIT HERE - EDIT HERE - EDIT HERE - EDIT HERE - EDIT HERE - EDIT HERE - EDIT HERE - EDIT HERE - EDIT HERE -


			# draw values
			starty = self.dispsize[1]/2 - imgsize[1]/2
			vtx = self.dispsize[0]/2 - imgsize[0]/2 - 10 # 10 isa
			vals = ['pupil colour',str(self.settings['pupilcol']), 'threshold', str(self.settings['threshold']), 'pupil position', str(self.settings['pupilpos']), 'pupil rect', str(self.settings['pupilrect'])]
			for i in range(len(vals)):
				# draw title
				tsize = self.sfont.size(vals[i])
				tpos = vtx-tsize[0], starty+i*20
				tsurf = self.sfont.render(vals[i], True, self.fgc)
				self.disp.blit(tsurf,tpos)
			
			# draw new image 
			"""
			try: image = self.thresholded 
			except: image = self.img

			#Edit here to change the image size drawn
			sprite_img = image.subsurface(300,400,75,75)
			sprite_img = pygame.transform.scale(sprite_img, (640,480))

			if stagevars[0]['show_threshimg']:
				self.disp.blit(image, blitpos)
			else:
				self.disp.blit(image, blitpos)
			"""

			# draw new image
			if stagevars[0]['show_threshimg']:
				self.disp.blit(self.thresholded, blitpos)
			else:
				self.disp.blit(self.img, blitpos)

			# update display
			pygame.display.flip()

			# apply settings
			self.tracker.settings = self.settings
		
			# DEBUG #
			if DEBUG:
				self.savefile.write(pygame.image.tostring(self.disp,'RGB')+BUFFSEP)
			# # # # #
		
		# DEBUG #
		if DEBUG:
			# close savefile
			self.savefile.close()
			# message
			print("processing images...")
			# open savefile
			savefile = open('data/savefile.txt','r')
			# read ALL contents in once, then close file again
			raw = savefile.read()
			savefile.close()
			# split based on newlines (this leaves one empty entry, because of the final newline)
			raw = raw.split(BUFFSEP)
			# process strings and save image
			for framenr in range(len(raw)-1):
				img = pygame.image.fromstring(raw[framenr],self.dispsize,'RGB')
			pygame.image.save(img,'data/frame%d.png' % framenr)
		# # # # #
		
		return self.tracker

	def check_input(self):
		
		"""Checks if there is any keyboard or mouse input, then returns
		input (keyname or clickposition) and inptype ('mouseclick' or
		'keypress') or None, None when no input is registered
		
		arguments
		None
		
		keyword arguments
		None
		
		returns
		inp, inptype	--	inp is a keyname (string) when a key has
							been pressed, or a click position
							((x,y) tuple) when a mouse button has
							been pressed
						inptype is a string, either 'mouseclick',
							or 'keypress'
						if no input is registered, returnvalues
						will be None, None
		"""
		
		# if nothing happens, None should be returned
		inp = None
		inptype = None
		
		# check events in queue
		for event in pygame.event.get():
			# mouseclicks
			if event.type == pygame.MOUSEBUTTONDOWN:
				inp = pygame.mouse.get_pos()
				inptype = 'mouseclick'
			# keypresses
			elif event.type == pygame.KEYDOWN:
				inp = pygame.key.name(event.key)
				inptype = 'keypress'

		return inp, inptype
	
	
	def handle_input(self, inptype, inp, stage, stagevars):
		
		"""Checks the input, compares this with what is possible in the
		current stage, then returns adjusted stage and adjusted stage
		variables
		
		arguments
		inptype		--	string indicating input type, should be
						either 'mouseclick' or 'keypress'
		inp			--	input, should be either
		"""
		
		# # # # #
		# mouseclicks to keypress value
		
		if inptype == 'mouseclick':
			
			# click position
			pos = inp[:]
			
			# Change this to include the positions of the new buttons!
			# loop through buttons
			for bn in self.buttons.keys():
				# check if click position is on a button
				r = self.buttons[bn]['inactive']['rect']
				if pos[0] > r[0] and pos[0] < r[0]+r[2] and pos[1] > r[1] and pos[1] < r[1]+r[3]:
					# change input to button name
					inp = bn
					# break from loop (we don't want to loop through all the other buttons once we've found the clicked one)
					break
		
		# # # # #
		# keypress (or simulated keypress) handling
		
		# stage 1
		if stage == 1:
			# up should increase threshold, down should decrease threshold
			if inp in ['up','down']:
				stagevars[1]['thresholdchange'] = inp
		
		# stage 2
		elif stage == 2:
			# up should increase pupil rect size, down should decrease pupil rect size
			if inp in ['up','down']:
				stagevars[2]['vprectchange'] = inp
			elif inp in ['left','right']:
				stagevars[2]['hprectchange'] = inp

			#self-edit
			if inp == 'l':
				state = stagevars[4]['locked']
				stagevars[4]['locked'] = not(state)

			if inp == "c":
				stagevars[5]['re_calib'] = True
		
		# stage 3
		elif stage == 3:
			# up should increase threshold, down should decrease threshold
			if inp in ['up','down']:
				stagevars[1]['thresholdchange'] = inp
			# space should confirm settings
			if inp == 'space':
				stagevars[3]['confirmed'] = True

			#self-edit
			if inp == 'l':
				state = stagevars[4]['locked']
				stagevars[4]['locked'] = not(state)

		# space should move to next stage (but not in stage 3)
		if inp == 'space' and stage < 3:
			stage += 1
		
		# number keys should make the stage jump to that number
		if inp in ['1','2','3']:
			stage = int(inp)
		
		# T should toggle between displays
		if inp == 't':
			if stagevars[0]['show_threshimg']:
				stagevars[0]['show_threshimg'] = False
			else:
				stagevars[0]['show_threshimg'] = True
		
		# R should toggle between using pupil rect or not
		if inp == 'r':
			if stagevars[0]['use_prect']:
				stagevars[0]['use_prect'] = False
			else:
				stagevars[0]['use_prect'] = True
		
		# escape should close down
		if inp == 'escape':
			pygame.display.quit()
			raise Exception("camtracker.Setup: Escape was pressed")
		
		# return the changed variables
		return stage, stagevars
	
	def resize_img(self, image):
		#Edit here to change the image size drawn
		sprite_img = image.subsurface(350,220,75,75)
		sprite_img = pygame.transform.scale(sprite_img, self.tracker.get_size())

		return sprite_img
	


class CamEyeTracker:
	
	"""The CamEyeTracker class uses your webcam as an eye tracker"""
	
	def __init__(self, device=None, camres=(640,480), zoom_factor=1.0):
		
		"""Initializes a CamEyeTracker instance
		
		arguments
		None
		
		keyword arguments
		device		--	a string or an integer, indicating either
						device name (e.g. '/dev/video0'), or a
						device number (e.g. 0); None can be passed
						too, in this case Setup will autodetect a
						useable device (default = None)
		camres		--	the resolution of the webcam, e.g.
						(640,480) (default = (640,480))
		"""

		global vcAvailable
		if vcAvailable == False:
			# select a device if none was selected
			if device == None:
				available = available_devices()
				if available == []:
					raise Exception("Error in camtracker.CamEyeTracker.__init__: no available camera devices found (did you forget to plug it in?)")
				else:
					device = available[0]
			
			# start the webcam
			self.cam = pygame.camera.Camera(device,(640,480),'RGB')
			self.cam.start()
		else:
			self.cam = cv.VideoCapture(0)
			self.cam.set(cv.CAP_PROP_FRAME_WIDTH, 2048)
			self.cam.set(cv.CAP_PROP_FRAME_HEIGHT, 1080)
			self.zoom_factor = zoom_factor

			
		# get the webcam resolution (get_size not available on all systems)
		try:
			self.camres = self.cam.get_size()
		except:
			self.camres = camres

		# default settings
		self.settings = {'pupilcol':(0,0,0), \
					'threshold':100, \
					'nonthresholdcol':(100,100,255,255), \
					'pupilpos':(-1,-1), \
					'pupilrect':pygame.Rect(self.camres[0]/2-50,self.camres[1]/2-25,100,100), \
					'pupilbounds': [0,0,0,0], \
					'':None					
					}
	
	
	def get_size(self):
		
		"""Returns a (w,h) tuple of the image size
		
		arguments
		None
		
		keyword arguments
		None
		
		returns
		imgsize		--	a (width,height) tuple indicating the size
						of the images produced by the webcam
		"""
		return self.camres

	
	def get_snapshot(self):
		"""Returns a snapshot, without doing any processing
		
		Arguments:
		None
		
		Keyword arguments:
		None
		
		Returns:
		snapshot -- a pygame.surface.Surface instance,
					containing a snapshot taken with the webcam
		"""
		global vcAvailable
		if vcAvailable:
			ret, frame = self.cam.read()
			if not ret:
				print("Error: Unable to capture frame from the camera.")
				return None

			if self.zoom_factor > 1.0:
				h, w, _ = frame.shape
				center_x, center_y = w // 2, h // 2
				radius_x, radius_y = int(w // (2 * self.zoom_factor)), int(h // (2 * self.zoom_factor))
				min_x, max_x = center_x - radius_x, center_x + radius_x
				min_y, max_y = center_y - radius_y, center_y + radius_y

				cropped_frame = frame[min_y:max_y, min_x:max_x]
				frame = cv.resize(cropped_frame, (w, h), interpolation=cv.INTER_LINEAR)
			
			try:
				frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

				# Resize the frame to match the display size
				frame = cv.resize(frame, np.array(self.camres))
				frame = np.swapaxes(frame, 0, 1)
				
				
				# Convert the frame to a NumPy array
				frame = np.array(frame, dtype=np.uint8)
				pygame_frame = pygame.surfarray.make_surface(frame)

			except Exception as e:
				print(e)
			
			return pygame_frame

		else:
			return self.cam.get_image()
		
		
	def threshold_image(self, image):
		
		"""Applies a threshold to an image and returns the thresholded
		image
		
		arguments
		image			--	the image that should be thresholded, a
						pygame.surface.Surface instance
		
		returns
		thresholded		--	the thresholded image,
						a pygame.surface.Surface instance
		"""
		
		# surface to apply threshold to surface
		thimg = pygame.surface.Surface(self.get_size(), 0, image)
		
		# perform thresholding
		th = (self.settings['threshold'],self.settings['threshold'],self.settings['threshold'])
		pygame.transform.threshold(thimg, image, self.settings['pupilcol'], th, self.settings['nonthresholdcol'], 1)
		
		return thimg
	
	
	def find_pupil(self, thresholded, pupilrect=False):
		print("pupilrect ", pupilrect)
		
		"""Get the pupil center, bounds, and size, based on the thresholded
		image; please note that the pupil bounds and size are very
		arbitrary: they provide information on the pupil within the
		thresholded image, meaning that they would appear larger if the
		camera is placed closer towards a subject, even though the
		subject's pupil does not dilate
		
		arguments
		thresholded		--	a pygame.surface.Surface instance, as
						returned by threshold_image
		
		keyword arguments
		pupilrect		--	a Boolean indicating whether pupil searching
						rect should be applied or not
						(default = False)
		
		returns
		pupilcenter, pupilsize, pupilbounds
					--	pupilcenter is an (x,y) position tuple that
						gives the pupil center with regards to the
						image (where the top left is (0,0))
						pupilsize is the amount of pixels that are
						considered to be part of the pupil in the
						thresholded image; when no pupilbounds can
						be found, this will return (-1,-1)
						pupilbounds is a (x,y,width,height) tuple,
						specifying the size of the largest square
						in which the pupil would fit
		"""
		
		
		# cut out pupilrect (but only if pupil bounding rect option is on)
		if pupilrect:
			# pupil rect boundaries
			rectbounds = pygame.Rect(self.settings['pupilrect'])
			# correct rect edges that go beyond image boundaries
			if self.settings['pupilrect'].left < 0:
				rectbounds.left = 0
			if self.settings['pupilrect'].right > self.camres[0]:
				rectbounds.right = self.camres[0]
			if self.settings['pupilrect'].top < 0:
				rectbounds.top = 0
			if self.settings['pupilrect'].bottom > self.camres[1]:
				rectbounds.bottom = self.camres[1]
			# cut rect out of image
			thresholded = thresholded.subsurface(rectbounds)
			ox, oy = thresholded.get_offset()
		
		# find potential pupil areas based on threshold
		th = (self.settings['threshold'],self.settings['threshold'],self.settings['threshold'])
		mask = pygame.mask.from_threshold(thresholded, self.settings['pupilcol'], th)
		
		# get largest connected area within mask (which should be the pupil)
		pupil = mask.connected_component()
		
		# get pupil center
		pupilcenter = pupil.centroid()
		
		# if we can only look within a rect around the pupil, do so
		if pupilrect:
			# compensate for subsurface offset
			pupilcenter = pupilcenter[0]+ox, pupilcenter[1]+oy
			# check if the pupil position is within the rect
			if (self.settings['pupilrect'].left < pupilcenter[0] < self.settings['pupilrect'].right) and (self.settings['pupilrect'].top < pupilcenter[1] < self.settings['pupilrect'].bottom):
				# set new pupil and rect position
				self.settings['pupilpos'] = pupilcenter
				x = pupilcenter[0] - self.settings['pupilrect'][2]/2
				y = pupilcenter[1] - self.settings['pupilrect'][3]/2
				self.settings['pupilrect'] = pygame.Rect(x,y,self.settings['pupilrect'][2],self.settings['pupilrect'][3])
			# if the pupil is outside of the rect, return missing
			else:
				self.settings['pupilpos'] = (-1,-1)
		else:
			self.settings['pupilpos'] = pupilcenter
		
		# get pupil bounds (sometimes failes, hence try-except)
		try:
			self.settings['pupilbounds'] = pupil.get_bounding_rects()[0]
			# if we're using a pupil rect, compensate offset
			if pupilrect:
				self.settings['pupilbounds'].left += ox
				self.settings['pupilbounds'].top += oy
		except:
			# if it fails, we simply use the old rect
			pass
		
		return self.settings['pupilpos'], pupil.count(), self.settings['pupilbounds']
	
	def find_face(self, image, facerect=False):
		"""
		Get the face center, bounds, and size, based on the input image.
		
		Arguments:
		image       -- a pygame.Surface instance containing the image
		
		Keyword Arguments:
		facerect    -- a Boolean indicating whether face searching rect should be applied or not (default = False)
		
		Returns:
		facecenter, facesize, facebounds
			facecenter: (x, y) position tuple that gives the face center within the image
			facesize: number of pixels considered part of the face; returns (-1, -1) if no face found
			facebounds: (x, y, width, height) tuple specifying the size of the largest rectangle fitting the face
		"""
		
		# Convert the pygame surface to an OpenCV image
		image_array = pygame.surfarray.array3d(image)
		image_array = cv.transpose(image_array)
		image_array = cv.cvtColor(image_array, cv.COLOR_RGB2BGR)
		
		ox, oy = 0, 0
		
		# Load the face detection classifier
		face_cascade = cv.CascadeClassifier(cv.data.haarcascades + 'haarcascade_frontalface_default.xml')
		
		# Detect faces in the image
		gray_image = cv.cvtColor(image_array, cv.COLOR_BGR2GRAY)
		faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
		
		if len(faces) > 0:
			# Assume the largest face is the target
			largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
			x, y, w, h = largest_face
			facecenter = (x + w // 2 + ox, y + h // 2 + oy)
			facebounds = (x + ox, y + oy, w, h)
			facesize = w * h
		else:
			# No face detected
			facecenter = (-1, -1)
			facebounds = (-1, -1, -1, -1)
			facesize = -1
		
		return facecenter, facesize, facebounds
		
	
	def give_me_all(self, pupilrect=False):
		
		"""Returns snapshot, thresholded image, pupil position, pupil area,
		and pupil bounds
		
		arguments
		None
		
		keyword arguments
		pupilrect		--	a Boolean indicating whether pupil searching
						rect should be applied or not
						(default = False)
		
		returns
		snapshot, thresholded, pupilcenter, pupilbounds, pupilsize
			snapshot	--	a pygame.surface.Surface instance,
						containing a snapshot taken with the webcam
			thresholded	--	the thresholded image,
						a pygame.surface.Surface instance
			pupilcenter	--	pupilcenter is an (x,y) position tuple that
						gives the pupil center with regards to the
						image (where the top left is (0,0))
			pupilsize	--	pupilsize is the amount of pixels that are
						considered to be part of the pupil in the
						thresholded image; when no pupilbounds can
						be found, this will return (-1,-1)
			pupilbounds	--	pupilbounds is a (x,y,width,height) tuple,
						specifying the size of the largest square
						in which the pupil would fit
		"""
		
		try: 
			img = self.get_snapshot() 
			print(img)
		except: 
			print("Cant snapshot")
		
		thimg = self.threshold_image(img)
		fpos, farea, fbounds = self.find_face(thimg, pupilrect)
		ppos, parea, pbounds = self.find_pupil(thimg, pupilrect)
		
		return img, thimg, ppos, parea, pbounds, fpos, farea, fbounds

	def close(self):
		
		"""Shuts down connection to the webcam and closes logfile
		
		arguments
		None
		
		keyword arguments
		None
		
		returns
		None
		"""
		
		# close camera
		self.cam.stop()
	
