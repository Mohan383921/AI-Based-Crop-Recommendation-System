from pydantic import BaseModel
from typing import Optional

class CropRequest(BaseModel):
    district: str
    soil_ph: Optional[float] = None
    soil_moisture: Optional[float] = None
    nutrient_n: Optional[float] = None
    nutrient_p: Optional[float] = None
    nutrient_k: Optional[float] = None
    rainfall: Optional[float] = None
    temperature: Optional[float] = None
    last_crop: Optional[str] = None
    top_k: int = 3
