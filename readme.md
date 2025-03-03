# Robotic Controller

This project is a web-based interface for controlling a robotic arm. It uses FastAPI for the backend and a simple HTML/CSS/JavaScript frontend to send commands to the robotic arm.

## Project Structure

```
robotic-controller/
├── app.py
├── controls
├── models/
│   └── control_model.py
├── control.html
└── readme.md
```

## Files

- **app.py**: The main FastAPI application file that defines the endpoints.
- **models/control_model.py**: Contains the Pydantic model for the control commands.
- **control.html**: The frontend HTML file for the web interface.
- **readme.md**: This file.

## Setup

1. **Clone the repository**:
    ```bash
    git clone https://github.com/abdulbasit-io/robotic-controller.git
    cd robotic-controller
    ```

2. **Create a virtual environment and activate it**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Run the application**:
    ```bash
    python3 app.py # On Windows `python app.py`
    ```

5. **Open your browser and navigate to**:
    ```bash
    http://127.0.0.1:8000  # or http://0.0.0.0:8000
    ```

6. **If Running on  Raspberry Pi**:
    ```bash
    http://<raspberry-pi_IP>:8000
    ```  

7. **To check if it's working from another device**:  
    ```bash
    http://<your_PC_IP_OR_raspberry_pi_IP>:8000
    ```  
    
##### Be sure to be on the same network as the raspberry before trying to access the page

## Usage

- **Control Page**: The main page (`/`) serves the `control.html` file, which contains a form to send commands to the robotic arm.
- **Send Commands**: Fill out the form and click "Send Command" to send a command to the robotic arm.

## Endpoints

- **GET /**: Serves the control page.
- **POST /control**: Receives control commands from the form and processes them.

## Models

- **ControlCommand**: A Pydantic model that defines the structure of the control commands.

## Frontend

The frontend is a simple HTML page with a form to collect control parameters. It includes a dark mode toggle and a loader animation for better user experience.  

## How To Use

Update the codebase by placing your robotic control logic in the controls folder. Then modify the main logic to accept an argument of the `ControlCommand` class  

Example  

```py
from models.control_model import ControlCommand  

async def control_arm(command: ControlCommand):
   # your logic here
```  

After that, update `app.py` with your module to control the robotic arm