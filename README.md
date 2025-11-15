## Assumptions
 A directory "MyFiles" were given with different files(.txt,.jpeg,etc.) 
 
## Execution

1. `main.py`  
   The entry point of the application. It initializes and runs two pipelines:  
   - **Logging pipeline** — sets up logging configuration  
   - **Folder watcher pipeline** — starts monitoring the folder for file changes and syncs with Google Drive

2. `google.py`  
   Contains functions to interact with Google Drive API for:  
   - Uploading files  
   - Deleting files 
   - Renaming files 
   - Creating folders

3. `logs.py`  
   Defines logging configuration used throughout the project.

4. `folder_watcher.py`  
   Contains the core logic that:  
   - Starts a separate thread to watch for file system changes  
   - Syncs detected changes with Google Drive in real-time


