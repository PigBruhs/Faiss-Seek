@echo off

REM Navigate to the parent directory
cd ..
if %errorlevel% neq 0 (
    echo Failed to navigate to the parent directory. Please check the path.
    pause
    exit /b 1
)
echo Successfully navigated to the parent directory. Current directory: %cd%
REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python from https://www.python.org/downloads/
    start https://www.python.org/downloads/
    pause
    exit /b 1
)
REM Check if the .venv folder exists
if exist .venv (
    echo Virtual environment .venv detected, activating it...
) else (
    echo Virtual environment .venv not detected, creating and activating it...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo Failed to create the virtual environment.
        pause
        exit /b 1
    )
)

REM Check if npm is installed
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo npm not detected. Please install Node.js and npm first.
    pause
    exit /b 1
)

REM Start the development server
echo Running npm run dev...
start /b npm run dev
set dev_pid=%!
if %errorlevel% neq 0 (
    echo Failed to start the development server.
    pause
    exit /b 1
)


REM Activate the virtual environment
if exist .venv\Scripts\activate (
    call .venv\Scripts\activate
    if %errorlevel% neq 0 (
        echo Failed to activate the virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Failed to activate the virtual environment. Please check the .venv folder.
    pause
    exit /b 1
)


REM Check and install Python dependencies
if exist server\requirements.txt (
    echo requirements.txt detected in server directory, installing Python dependencies...
    pip install -r server\requirements.txt
    if %errorlevel% neq 0 (
        echo Failed to install Python dependencies from server\requirements.txt.
        pause
        exit /b 1
    )
) else (
    echo requirements.txt not found in server directory. Skipping Python dependencies installation.
)

REM Start the Python application
echo Starting the Python application...
if exist server (
    cd server
    if exist app.py (
        start /b python app.py
        set python_pid=%!
        if %errorlevel% neq 0 (
            echo Failed to start the Python application.
            pause
            exit /b 1
        )
    ) else (
        echo app.py file not found. Please ensure the file exists.
        pause
        exit /b 1
    )
    cd ..
) else (
    echo Server directory not found. Please ensure the server folder exists.
    pause
    exit /b 1
)

REM Wait for user input to terminate
echo Press any key to terminate both the frontend and backend...
pause >nul

REM Terminate the development server
echo Terminating the development server...
taskkill /PID %dev_pid% /F >nul 2>nul

REM Terminate the Python application
echo Terminating the Python application...
taskkill /PID %python_pid% /F >nul 2>nul

REM Deactivate the virtual environment
if exist .venv\Scripts\deactivate (
    call .venv\Scripts\deactivate
    if %errorlevel% neq 0 (
        echo Failed to deactivate the virtual environment.
        pause
        exit /b 1
    )
)

pause
exit /b