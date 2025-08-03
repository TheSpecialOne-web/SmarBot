import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { createCommonPromptTemplate } from "@/orval/administrator-api";
import { BotTemplate, CreateCommonPromptTemplateParam } from "@/orval/models/administrator-api";

import { PromptTemplateForm } from "../PromptTemplateForm";

type Props = {
  open: boolean;
  onClose: () => void;
  refetch: () => void;
  assistantTemplateId: BotTemplate["id"];
};

export const CreateCommonPromptTemplateDialog = ({
  open,
  onClose,
  refetch,
  assistantTemplateId,
}: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const handleCreateCommonPromptTemplate = async (params: CreateCommonPromptTemplateParam) => {
    try {
      await createCommonPromptTemplate(assistantTemplateId, params);
      enqueueSuccessSnackbar({ message: "質問例を追加しました。" });
      refetch();
      onClose();
    } catch (err) {
      const errMsg = getErrorMessage(err);
      enqueueErrorSnackbar({
        message: errMsg || "質問例の追加に失敗しました。",
      });
    }
  };

  return (
    <CustomDialog open={open} title="質問例の追加" maxWidth="md" onClose={onClose}>
      <PromptTemplateForm
        onClose={onClose}
        onSubmit={handleCreateCommonPromptTemplate}
        submitButtonText="追加"
      />
    </CustomDialog>
  );
};
