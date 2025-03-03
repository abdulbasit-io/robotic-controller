"""
Controls data structure
"""

from pydantic import BaseModel
from fastapi import Form

class ControlCommand(BaseModel):
    mode: str
    start_time: str | None = None
    end_time: str | None = None
    lasers: bool = False
    speakers: bool = False
    cycle_duration: int | None = None
    cycle_rest: int | None = None
    speaker_volume: int | None = None
    speaker_duration: int | None = None
    laser_duration: int | None = None
    laser_intensity: int | None = None



    @classmethod
    def as_form(
        cls,
        mode: str = Form(...),
        start_time: str = Form(None),
        end_time: str = Form(None),
        lasers: bool = Form(False),
        speakers: bool = Form(False),
        cycle_duration: int = Form(None),
        cycle_rest: int = Form(None),
        speaker_volume: int = Form(None),
        speaker_duration: int = Form(None),
        laser_duration: int = Form(None),
        laser_intensity: int = Form(None),
    ):
        return cls(
            mode=mode,
            start_time=start_time,
            end_time=end_time,
            lasers=lasers,
            speakers=speakers,
            cycle_duration=cycle_duration,
            cycle_rest=cycle_rest,
            speaker_volume=speaker_volume,
            speaker_duration=speaker_duration,
            laser_duration=laser_duration,
            laser_intensity=laser_intensity,
        )
