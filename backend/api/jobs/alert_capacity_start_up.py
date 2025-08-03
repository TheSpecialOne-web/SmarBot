from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.usecase.job.alert_capacity import AlertCapacityUseCase


def alert_capacity_start_up():
    with SessionFactory() as session:
        injector = get_injector(session)
        alert_capacity_interactor = injector.get(AlertCapacityUseCase)
        return alert_capacity_interactor.alert_capacity_start_up()
