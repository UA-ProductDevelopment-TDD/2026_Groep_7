"""Validated UI data; coordinates are schematic canvas units, not robot metres."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Model(BaseModel):
    model_config = ConfigDict(extra='ignore', allow_inf_nan=False)

class Point(Model):
    x: float = Field(ge=30, le=930)
    y: float = Field(ge=30, le=570)

class TerrainObject(Point):
    id: str = Field(min_length=1, max_length=80, pattern=r'^[a-zA-Z0-9_-]+$')
    type: Literal['coop', 'nest', 'water', 'plant', 'door', 'fence', 'dock']
    name: str = Field(min_length=1, max_length=60)
    w: float = Field(ge=10, le=400)
    h: float = Field(ge=8, le=300)
    rotation: float = Field(ge=0, le=360)

class Route(Model):
    id: str = Field(min_length=1, max_length=80, pattern=r'^[a-zA-Z0-9_-]+$')
    name: str = Field(min_length=1, max_length=60)
    points: list[Point] = Field(min_length=2, max_length=150)
    closed: bool = True

class Project(Model):
    version: Literal[1] = 1
    objects: list[TerrainObject] = Field(max_length=120)
    routes: list[Route] = Field(max_length=30)
    zones: list[Route] = Field(max_length=30)
    eggs: int = Field(ge=0, le=24, strict=True)
    eggTime: int = Field(ge=0, le=9999999999999)
    doorTime: int = Field(ge=0, le=9999999999999)

    @model_validator(mode='after')
    def unique_ids(self):
        items = self.objects + self.routes + self.zones
        if len({o.id for o in items}) != len(items):
            raise ValueError('Onderdeel-ID’s moeten uniek zijn.')
        if any(len(z.points) < 3 for z in self.zones):
            raise ValueError('Een verboden zone heeft minstens drie punten.')
        return self

class SaveProject(Model):
    revision: int = Field(ge=1)
    project: Project

class Command(Model):
    id: str = Field(min_length=1, max_length=80, pattern=r'^[a-zA-Z0-9_-]+$')
    action: Literal['patrol', 'pause', 'resume', 'stop', 'dock', 'eggs', 'water']
    route_id: str | None = Field(default=None, max_length=80)

class Scenario(Model):
    name: Literal['normal', 'offline', 'low-battery', 'door-open', 'fox', 'camera-off']
