from typing import Annotated

from pydantic import BaseModel, Field, model_validator


class Well(BaseModel):
    row: int = Field(ge=0)
    col: int = Field(ge=0)
    rate: float  # 这个不限制，因为可以抽水也可以注水
    description: str = Field(default="", max_length=50)


class CHDHead(BaseModel):
    row: int = Field(ge=0)
    col: int = Field(ge=0)
    head: float  # 这个不限制，定水头边界可以存在正负


class ModelParams(BaseModel):
    sim_name: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    modelname: str = Field(min_length=3, max_length=50, default="gwf")
    delr: float = Field(gt=0)
    delc: float = Field(gt=0)
    nrow: int = Field(ge=1, le=100)
    ncol: int = Field(ge=1, le=100)
    k: Annotated[float, Field(
        gt=0)] | list[list[Annotated[float, Field(gt=0)]]]
    chds: list[CHDHead] = Field(min_length=1)
    wells: list[Well] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_row_and_col(self):
        for chd in self.chds:
            if chd.row >= self.nrow or chd.col >= self.ncol:
                raise ValueError("CHD position out of bounds")
        for well in self.wells:
            if well.row >= self.nrow or well.col >= self.ncol:
                raise ValueError("Well position out of bounds")
        if isinstance(self.k, list):
            if len(self.k) != self.nrow:
                raise ValueError(
                    f"k row count mismatch: expected {self.nrow} rows (nrow), got {len(self.k)}"
                )
            for i, row in enumerate(self.k):
              if len(row) != self.ncol:
                raise ValueError(
                    f"k column count mismatch in row {i}: expected {self.ncol} columns (ncol), got {len(row)}"
                )
        return self
