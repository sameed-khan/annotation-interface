# Annotation Interface

![A screenshot of the Anki-style labeling interface of the repository software](front/assets/images/interface-screenshot.png)

A simple web application interface for annotating images of any kind.
Point the application to the folder where images are stored on your hard drive and enjoy a clean Anki-style labeling interface with labels bound to home-row keys.
This application does not require internet access and can be run entirely locally on your computer.
It is a "web" application only insofar that the interface was created for viewing inside of a browser, but it does not require online access and does not send your data or store it anywhere besides your hard drive.

TODO: 
- build: configure vite and litestar to work together via a single build script and have all assets
work smoothly
    - figure out how the vite build process enforces constraints on what litestar gets to name its
    routes vs the actual filepath there
- build: first task - get the login page to successfully reference the henry ford logo 
- get all the rest of the template pages working
- configure it so that python variables reference the dist directory accurately at least when 
manually set - in an ideal world, this is done by a centralized build script
