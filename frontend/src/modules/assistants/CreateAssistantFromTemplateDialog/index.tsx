import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { BotTemplate, Group, UserTenant } from "@/orval/models/backend-api";

import { CreateAssistantFromTemplateForm } from "./CreateAssistantFromTemplateForm";

type Props = {
  groups: Group[];
  defaultGroup?: Group;
  open: boolean;
  onClose: () => void;
  tenant: UserTenant;
  botTemplate: BotTemplate;
};

export const CreateAssistantFromTemplateDialog = ({
  groups,
  defaultGroup,
  open,
  onClose,
  tenant,
  botTemplate,
}: Props) => {
  return (
    <CustomDialog
      title="テンプレートからアシスタント作成"
      open={open}
      onClose={onClose}
      maxWidth="md"
    >
      <CreateAssistantFromTemplateForm
        groups={groups}
        defaultGroup={defaultGroup}
        botTemplate={botTemplate}
        allowedModelFamilies={tenant.allowed_model_families}
        enableDocumentIntelligence={tenant.enable_document_intelligence}
        enableLLMDocumentReader={tenant.enable_llm_document_reader}
        onClose={onClose}
      />
    </CustomDialog>
  );
};
