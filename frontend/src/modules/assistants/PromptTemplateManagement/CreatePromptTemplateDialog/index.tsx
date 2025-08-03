import { FormProvider, useForm } from "react-hook-form";

import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { createBotPromptTemplate } from "@/orval/backend-api";
import { Bot, CreateBotPromptTemplateParam } from "@/orval/models/backend-api";

import { PromptTemplateForm } from "../PromptTemplateForm";

type Props = {
  open: boolean;
  onClose: () => void;
  refetch: () => void;
  assistantId: Bot["id"];
};

export const CreatePromptTemplateDialog = ({ open, onClose, refetch, assistantId }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const useFormMethods = useForm<CreateBotPromptTemplateParam>({
    defaultValues: {
      title: "",
      description: "",
      prompt: "",
    },
  });

  const { reset } = useFormMethods;

  const handleCreatePromptTemplate = async (params: CreateBotPromptTemplateParam) => {
    try {
      await createBotPromptTemplate(assistantId, params);
      enqueueSuccessSnackbar({ message: "質問例を追加しました。" });
      refetch();
      reset();
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
