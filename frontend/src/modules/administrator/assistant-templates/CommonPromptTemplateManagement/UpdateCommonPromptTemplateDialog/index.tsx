import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { updateCommonPromptTemplate } from "@/orval/administrator-api";
import {
  BotTemplate,
  CommonPromptTemplate,
  UpdateCommonPromptTemplateParam,
} from "@/orval/models/administrator-api";

import { PromptTemplateForm } from "../PromptTemplateForm";

type Props = {
  open: boolean;
  onClose: () => void;
  commonPromptTemplate: CommonPromptTemplate;
  refetch: () => void;
  assistantTemplateId: BotTemplate["id"];
};

export const UpdateCommonPromptTemplateDialog = ({
  open,
  onClose,
  refetch,
  commonPromptTemplate,
  assistantTemplateId,
}: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const handleUpdateCommonPromptTemplate = async (params: UpdateCommonPromptTemplateParam) => {
    if (!commonPromptTemplate) {
      return;
    }
    try {
      await updateCommonPromptTemplate(assistantTemplateId, commonPromptTemplate.id, params);
      enqueueSuccessSnackbar({ message: "質問例を更新しました。" });
      refetch();
      onClose();
    } catch (err) {
      const errMsg = getErrorMessage(err);
      enqueueErrorSnackbar({
        message: errMsg || "質問例の更新に失敗しました。",
      });
    }
  };

  return (
    <CustomDialog open={open} title="質問例の編集" maxWidth="md" onClose={onClose}>
      <PromptTemplateForm
        onClose={onClose}
        onSubmit={handleUpdateCommonPromptTemplate}
        submitButtonText="保存"
        commonPromptTemplate={commonPromptTemplate}
      />
    </CustomDialog>
  );
};
