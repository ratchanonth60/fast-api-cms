from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
import os
import databases

# กำหนด FastAPI app
app = FastAPI()


user = os.getenv("POSTGRES_USER", "postgresql")
password = os.getenv("POSTGRES_PASSWORD", "054362770aA")
endpoint = os.getenv(
    "POSTGRES_ENDPOINT", "db-golang-v2.cjcc0ye241bn.ap-southeast-1.rds.amazonaws.com"
)
port = os.getenv("POSTGRES_PORT", "5432")
db_name = os.getenv("POSTGRES_DB", "fastapi_db")
postgres_url = f"postgresql://{user}:{password}@{endpoint}:{port}/{db_name}"
database = databases.Database(postgres_url)
engine = create_engine(postgres_url, echo=True)  # echo=True เพื่อ debug SQL


# กำหนด model Hero
class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    secret_name: str


# Dependency สำหรับ session
def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


# สร้างตารางเมื่อ startup
@app.on_event("startup")
async def on_startup():
    await database.connect()
    SQLModel.metadata.create_all(engine)


@app.on_event("shutdown")
async def on_shutdown():
    await database.disconnect()


# Endpoint สำหรับสร้าง Hero
@app.post("/heroes/")
def create_hero(hero: Hero, session: SessionDep) -> Hero:
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero


# Endpoint สำหรับอ่าน Heroes
@app.get("/heroes/")
def read_heroes(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Hero]:
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes


# Endpoint สำหรับอ่าน Hero โดย ID
@app.get("/heroes/{hero_id}")
def read_hero(hero_id: int, session: SessionDep) -> Hero:
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero


# Endpoint สำหรับลบ Hero
@app.delete("/heroes/{hero_id}")
def delete_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
    return {"ok": True}
