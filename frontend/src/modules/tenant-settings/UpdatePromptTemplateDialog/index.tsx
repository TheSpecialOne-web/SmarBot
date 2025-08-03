import { FormProvider, useForm } from "react-hook-form";

import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { updatePromptTemplate } from "@/orval/backend-api";
import { PromptTemplate, PromptTemplateProps } from "@/orval/models/backend-api";

import { PromptTemplateForm } from "../PromptTemplateForm";

type Props = {
  open: boolean;
  onClose: () => void;
  promptTemplate: PromptTemplate;
  refetch: () => void;
};

export const UpdatePromptTemplateDialog = ({ open, onClose, refetch, promptTemplate }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const useFormMethods = useForm<PromptTemplate>({
    defaultValues: promptTemplate,
  });
  const { reset } = useFormMethods;

  const handleUpdatePromptTemplate = async (params: PromptTemplateProps) => {
    try {
      await updatePromptTemplate(promptTemplate?.id, params);
      enqueueSuccessSnackbar({ message: "プロンプトテンプレートを更新しました。" });
      refetch();
      onClose();
      reset();
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({
        message: errMsg || "プロンプトテンプレートの更新に失敗しました。",
      });
    }
  };

  return (
    <CustomDialog open={open} title="プロンプトテンプレートの編集" maxWidth="md" onClose={onClose}>
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
