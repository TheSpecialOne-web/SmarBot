from api.controllers.backend_api.openapi import models
from api.domain.models.workflow.specifications.workflow_spec_for_run import (
    RunWorkflowRequestArrayField,
    RunWorkflowRequestField,
    RunWorkflowResponseArrayField,
    RunWorkflowResponseField,
)


def _to_request_model_fields(
    properties: list[RunWorkflowRequestField],
) -> list[models.RunWorkflowRequestField]:
    return [
        models.RunWorkflowRequestField(
            key=property.key,
            display_name=property.display_name,
            description=property.description,
            type=property.type,
            required=property.required,
            default_value=property.default_value,
            item=_to_request_model_array_fields(property.item) if property.item else None,
        )
        for property in properties
    ]


def _to_request_model_array_fields(
    item: RunWorkflowRequestArrayField,
) -> models.RunWorkflowRequestArrayField:
    return models.RunWorkflowRequestArrayField(
        type=item.type,
        properties=_to_request_model_fields(item.properties) if item.properties else None,
    )


def _to_response_model_array_fields(
    item: RunWorkflowResponseArrayField,
) -> models.RunWorkflowResponseArrayField:
    return models.RunWorkflowResponseArrayField(
        type=item.type,
        properties=_to_response_model_fields(item.properties) if item.properties else None,
    )


def _to_response_model_fields(
    properties: list[RunWorkflowResponseField],
) -> list[models.RunWorkflowResponseField]:
    return [
        models.RunWorkflowResponseField(
            key=property.key,
            type=property.type,
            item=_to_response_model_array_fields(property.item) if property.item else None,
        )
        for property in properties
    ]
