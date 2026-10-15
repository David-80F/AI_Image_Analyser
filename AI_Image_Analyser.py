import customtkinter as ctk
import base64
import os
import threading
from pathlib import Path
from dotenv import load_dotenv
from customtkinter import filedialog
from PIL import Image
from google import genai

# Variables

SCREEN_SIZE = "1000x600"              # Sets screen size
screen_width = int(SCREEN_SIZE.split("x")[0])  # Gets screen width
screen_height = int(SCREEN_SIZE.split("x")[1]) # Gets screen height

project_folder = Path(__file__).parent # Gets path directory of project
load_dotenv(project_folder/".env")     # Accesses environment file within project file
API_key = os.getenv("API_Key")         # Gets API key from environment file

# Functions

def select_image():                   # Lets user select image
    img_path = filedialog.askopenfilename(filetypes=[("Image Files", ("*.png", "*.jpeg", "*.jpg"))]) # Gets image file path
    if img_path != "":                    # Doesn't proceed if user pressed cancel
        file_extension = Path(img_path).suffix.lower().split(".")[1] # Gets file extension of image
        if file_extension == "jpg":                          # Checks if file extension is jpg (jpg not accepted MIME type)
             file_extension = "jpeg"                         # Sets jpg to accpeted MIME type: jpeg
        image_category = "image/" + file_extension           # Puts together 'image' category and its suffix
        show_frames(image_frame)          # Switches frame to image frame in order to display image

        loading_label = ctk.CTkLabel(image_frame, text="Analysing Image...", text_color="white")
        loading_label.grid(row=1, column=1)
         
        image_description = threading.Thread(target=send_to_API, args=(img_path, image_category, loading_label)) # Sends selected image to API for analysis and fetches AI Agent's description via background thread
        image_description.start()
        
def send_to_API(img_path, image_category, loading_label):   # Sends selected image to API for analysis
    with open(img_path, "rb") as file: # Turns selected image into binary (covertable into base64)
         binary_img = file.read()
    img_base64 = base64.b64encode(binary_img).decode("utf-8") # Turns binary into base64 (API understands this)
     
    client = genai.Client(api_key = API_key)  # Accesses AI using the API key
    contents = [{                             # Content of prompt to AI Agent
        "inline_data": {
            "data" : img_base64,              # Specifies input type: 'data', and inputs base64 data of image
            "mime_type" : image_category}     # specifies inout type: 'mime type', and inputs mime type (Category: 'Image', file extension: "png/ jpeg")
            }, 
                "What is going on in this image? Please be concise" # Asks agent what's happening in input image
                ]
    try:
        response = client.models.generate_content(model="gemini-3.8-flash", contents=contents) # Sends prompt to AI Agent
    except Exception as error:
        if getattr(error, "code", None) == 400:
            error_message = "There seems to be a problem with your API key. Please check your API key and try again."
        elif getattr(error, "code", None) == 503:
            error_message = "The AI agent is currently receiving too much traffic. Please try again later."
        else:
            error_message = "There seems to be a problem analysis the image. Please try again."   
        error_received(error_message, loading_label)
        return
    
    response_received(img_path, response.text, loading_label)

def response_received(img_path, image_description, loading_label):
    app.after(0, update_GUI, img_path, image_description, loading_label)

def update_GUI(img_path, image_description, loading_label):
    loading_label.destroy()
    display_image(img_path, image_description)

def display_image(img_path, image_description):          # Displays the image
    img_open = Image.open(img_path)       # Opens selected image

    img_width = img_open.size[0]          # Gets the image's width
    img_height = img_open.size[1]         # Gets the image's height

    while img_width >= (screen_width* 0.9) or img_height >= (screen_height * 0.9): # Ensures that image size is smaller than screen and leaves a 10% margin
            img_width = img_width * 0.9   # Reduces image width by 10%
            img_height = img_height *  0.9# Reduces image height by 10% (keeps same aspect ratio)

    img = ctk.CTkImage(light_image= img_open, dark_image= img_open, size = (img_width, img_height)) # Creates an image object of selected image
    img_display = ctk.CTkLabel(image_frame, image= img, text="") # Makes image object a diplayable label object
    img_display.grid(row=0, column= 1)    # Displays image on the grid
    
    response_label = ctk.CTkLabel(image_frame, text=image_description, justify="left", wraplength=img_width, text_color="white") # Creates a label image description
    response_label.grid(row=1, column=1)

def error_received(error_message, loading_label):
    app.after(0, update_GUI_error, error_message, loading_label)

def update_GUI_error(error_message, loading_label):
    loading_label.destroy()
    display_error(error_message)

def display_error(error_message):
    error_label = ctk.CTkLabel(image_frame, text=error_message, justify="left", wraplength=screen_width) # Creates an error label
    error_label.grid(row=1, column=1)

def show_frames(frame):                   # Switches to correct frame 
    for widget in image_frame.winfo_children():  # Removes image and description from image frame
        if widget != back_button:                # Checks that back button isn't removed
            widget.destroy()                     # Removes image / description
    home_frame.grid_remove()              # Removes home frame
    image_frame.grid_remove()             # Removes image frame

    frame.grid(row=0, column=0, sticky="nswe") # Selects called frame

# Main App

app = ctk.CTk()                       # Makes app

app.title("Image Analyser")                # Adds app title
app.geometry(SCREEN_SIZE)             # Sets frame size

app.grid_rowconfigure(0, weight=1)    # Makes grid row
app.grid_columnconfigure(0, weight=1) # Makes grid column

# Frames

home_frame = ctk.CTkFrame(app)             # Makes home frame
image_frame = ctk.CTkFrame(app, fg_color="#2a2a30")            # Makes frame showing image

home_frame.rowconfigure((0,1,2), weight=1)      # Makes home frame rows
home_frame.columnconfigure((0,1,2), weight=1)   # Makes home frame columns 

image_frame.rowconfigure((0,1,2), weight=1)      # Makes image frame rows
image_frame.columnconfigure((0,1,2), weight=1)   # Makes image frame columns

home_frame.grid(row=0, column=0, sticky="nswe") # Puts home frame in grid to start

# Background

background_img_path = Image.open(project_folder/"EarthBackground.png")
background_image = ctk.CTkImage(light_image=background_img_path, dark_image=background_img_path, size=(screen_width, screen_height))
background_label = ctk.CTkLabel(home_frame, image=background_image, text="")
background_label.place(x=0, y=0, relwidth=1, relheight=1)

# Labels

title_label = ctk.CTkLabel(home_frame, text="Image Analyser", font=("Arial", 25, "bold"),text_color="white", bg_color="#0e0e11", fg_color="#0e0e11")
title_label.grid(row=0, column=1)

# Buttons

select_image_button = ctk.CTkButton(home_frame, width=25, height=13, command=select_image, text="Select File", text_color="White", font=("Arial",12,"bold"), corner_radius=100, bg_color="#3e5587", fg_color="#96cc33") # Creates button
select_image_button.place(x=screen_width/2 - 28, y=(screen_height/2)-20)      # Adds button to frame

back_button = ctk.CTkButton(image_frame, width=1, height=1, command=lambda: show_frames(home_frame), text="Back", fg_color="red")
back_button.grid(row=2, column=1)

# App Loop
if __name__ == "__main__":
    app.mainloop()                              # Runs app loop