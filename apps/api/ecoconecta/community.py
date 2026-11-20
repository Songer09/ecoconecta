from fastapi import APIRouter
from pydantic import BaseModel, HttpUrl

router = APIRouter(tags=["Comunidad"])


class CommunityInfo(BaseModel):
    name: str
    description: str
    source_url: HttpUrl


@router.get("/public/community", response_model=list[CommunityInfo])
def community():
    return [
        CommunityInfo(name="Villas de San Pablo",
                      description="Megabarrio del suroccidente de Barranquilla que integra vivienda, espacios comunitarios y oportunidades de desarrollo local.",
                      source_url="https://fundacionsantodomingo.org/nuestro-impacto/desarrollo-territorial/villas-de-san-pablo/"),
        CommunityInfo(name="Fundación Santo Domingo",
                      description="Fundación familiar creada en Barranquilla en 1960. Trabaja con aliados en proyectos de desarrollo territorial, entre ellos Villas de San Pablo.",
                      source_url="https://fundacionsantodomingo.org/conocenos/quienes-somos/"),
    ]
