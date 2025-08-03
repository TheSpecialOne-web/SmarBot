import { FormProvider, useForm } from "react-hook-form";

import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { updateBotPromptTemplate } from "@/orval/backend-api";
import { Bot, BotPromptTemplate, UpdateBotPromptTemplateParam } from "@/orval/models/backend-api";

import { PromptTemplateForm } from "../PromptTemplateForm";

type Props = {
  open: boolean;
  onClose: () => void;
  promptTemplate: BotPromptTemplate;
  refetch: () => void;
  assistantId: Bot["id"];
};

export const UpdatePromptTemplateDialog = ({
  open,
  onClose,
  refetch,
  promptTemplate,
  assistantId,
}: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const useFormMethods = useForm<BotPromptTemplate>({
    defaultValues: promptTemplate,
  });

  const handleUpdatePromptTemplate = async (params: UpdateBotPromptTemplateParam) => {
    if (!promptTemplate) {
      return;
    }
    try {
      await updateBotPromptTemplate(assistantId, promptTemplate.id, params);
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
      <FormProvider {...useFormMethods}>
        <PromptTemplateForm
          onClose={onClose}
          onSubmit={handleUpdatePromptTemplate}
          submitButtonText="保存"
        />
      </FormProvider>
    </CustomDialog>
  );
};
