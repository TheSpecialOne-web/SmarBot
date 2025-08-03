from api.app import app
from api.domain.models import prompt_template as pt_domain
from api.infrastructures.postgres.prompt_template import PromptTemplateRepository
from api.infrastructures.postgres.tenant import TenantRepository


def main():
    with app.app_context():
        tenant_repo = TenantRepository()
        tenants = tenant_repo.find_all()
        prompt_template_repo = PromptTemplateRepository()
        default_prompt_templates = pt_domain.DefaultPromptTemplates()
        for tenant in tenants:
            try:
                prompt_template_repo.bulk_create(
                    tenant_id=tenant.id,
                    prompt_templates=default_prompt_templates.prompt_templates,
                )
                print(f"created default prompt templates for {tenant.name.value}")
            except Exception as e:
                print(e)
                raise e


if __name__ == "__main__":
    main()
