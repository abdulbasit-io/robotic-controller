from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse, JSONResponse
from models.control_model import ControlCommand


# import the robotic arm control module
# Example: from controls.robotic_module import control_arm

app = FastAPI()


@app.get("/")
async def server_page():
    return FileResponse("control.html")

# collect form from webpage and control the robotic arm
@app.post("/control")
async def control_robot(command: ControlCommand = Depends(ControlCommand.as_form)):
    print("Command: ", command)
    
    # pass the command to the robotic arm control module here
    # Example: control_arm(command)
    
    return JSONResponse(content={"message": "✅ Command received successfully!"})

  
  


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)