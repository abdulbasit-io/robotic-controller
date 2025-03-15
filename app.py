from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse, JSONResponse
from models.control_model import ControlCommand
# from controls.robotic_control import control_arm



app = FastAPI()


@app.get("/")
async def server_page():
    return FileResponse("control.html")

# collect form from webpage and control the robotic arm
# note that time is being passed in 24 hours format
@app.post("/control")
async def control_robot(command: ControlCommand = Depends(ControlCommand.as_form)):
    print("Command: ", command)
    
    # pass the command to the robotic arm control module here
    control_arm(command)
    
    return JSONResponse(content={"message": "✅ Command received successfully!"})

  
  


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)