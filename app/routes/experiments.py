"""CRUD de experimentos pertenecientes a proyectos propios."""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select

from app.models import Experiment, Project, User
from app.routes.projects import owned_project
from app.schemas import ExperimentInput, ExperimentOut
from app.security import get_current_user, get_db

router = APIRouter(tags=["experiments"], dependencies=[Depends(get_current_user)])


def owned_experiment(db, experiment_id: int, user_id: int) -> Experiment:
    experiment = db.scalar(
        select(Experiment)
        .join(Project, Experiment.project_id == Project.id)
        .where(Experiment.id == experiment_id, Project.user_id == user_id)
    )
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experimento no encontrado.")
    return experiment


@router.get("/projects/{project_id}/experiments", response_model=list[ExperimentOut])
def list_experiments(
    project_id: int,
    model: str | None = None,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    owned_project(db, project_id, user.id)
    statement = select(Experiment).where(Experiment.project_id == project_id)
    if model is not None:
        statement = statement.where(Experiment.model == model)
    return db.scalars(statement.order_by(Experiment.id)).all()


@router.post("/projects/{project_id}/experiments", response_model=ExperimentOut, status_code=201)
def create_experiment(
    project_id: int,
    payload: ExperimentInput,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    owned_project(db, project_id, user.id)
    experiment = Experiment(project_id=project_id, **payload.model_dump())
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment


@router.get("/experiments/{experiment_id}", response_model=ExperimentOut)
def get_experiment(
    experiment_id: int, user: User = Depends(get_current_user), db=Depends(get_db)
):
    return owned_experiment(db, experiment_id, user.id)


@router.put("/experiments/{experiment_id}", response_model=ExperimentOut)
def update_experiment(
    experiment_id: int,
    payload: ExperimentInput,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    experiment = owned_experiment(db, experiment_id, user.id)
    for field, value in payload.model_dump().items():
        setattr(experiment, field, value)
    db.commit()
    db.refresh(experiment)
    return experiment


@router.delete("/experiments/{experiment_id}", status_code=204)
def delete_experiment(
    experiment_id: int, user: User = Depends(get_current_user), db=Depends(get_db)
):
    experiment = owned_experiment(db, experiment_id, user.id)
    db.delete(experiment)
    db.commit()
    return Response(status_code=204)
