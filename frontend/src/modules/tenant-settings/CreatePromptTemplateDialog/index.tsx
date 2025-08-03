import { FormProvider, useForm } from "react-hook-form";

import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { createPromptTemplates } from "@/orval/backend-api";
import { PromptTemplateProps } from "@/orval/models/backend-api";

import { PromptTemplateForm } from "../PromptTemplateForm";

type Props = {
  open: boolean;
  onClose: () => void;
  refetch: () => void;
};

export const CreatePromptTemplateDialog = ({ open, onClose, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const useFormMethods = useForm<PromptTemplateProps>({
    defaultValues: {
      title: "",
      description: "",
      prompt: "",
    },
  });
  const { reset } = useFormMethods;

  const handleCreatePromptTemplate = async (params: PromptTemplateProps) => {
    try {
      await createPromptTemplates({
        prompt_templates: [params],
      });
      enqueueSuccessSnackbar({ message: "プロンプトテンプレートを追加しました。" });
      refetch();
      onClose();
      reset();
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({
        message: errMsg || "プロンプトテンプレートの追加に失敗しました。",
      });
    }
  };

  return (
    <CustomDialog open={open} title="プロンプトテンプレートの追加" maxWidth="md" onClose={onClose}>
      <FormProvider {...useFormMethods}>
        <PromptTemplateForm
          onClose={onClose}
          onSubmit={handleCreatePromptTemplate}
          submitButtonText="追加"
        />
      </FormProvider>
    </CustomDialog>
  );
};
