"""CRUD de proyectos propios."""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select

from app.models import Experiment, Project, User
from app.schemas import ProjectInput, ProjectOut
from app.security import get_current_user, get_db

router = APIRouter(tags=["projects"], dependencies=[Depends(get_current_user)])


def owned_project(db, project_id: int, user_id: int) -> Project:
    project = db.scalar(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
    return project


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(user: User = Depends(get_current_user), db=Depends(get_db)):
    return db.scalars(
        select(Project).where(Project.user_id == user.id).order_by(Project.id)
    ).all()


@router.post("/projects", response_model=ProjectOut, status_code=201)
def create_project(
    payload: ProjectInput, user: User = Depends(get_current_user), db=Depends(get_db)
):
    project = Project(user_id=user.id, **payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, user: User = Depends(get_current_user), db=Depends(get_db)):
    return owned_project(db, project_id, user.id)


@router.put("/projects/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    payload: ProjectInput,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    project = owned_project(db, project_id, user.id)
    for field, value in payload.model_dump().items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(
    project_id: int, user: User = Depends(get_current_user), db=Depends(get_db)
):
    project = owned_project(db, project_id, user.id)
    if db.scalar(select(Experiment.id).where(Experiment.project_id == project.id)) is not None:
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar un proyecto con experimentos.",
        )
    db.delete(project)
    db.commit()
    return Response(status_code=204)
