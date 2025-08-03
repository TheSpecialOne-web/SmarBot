import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useCreateQuestionAnswer } from "@/orval/backend-api";
import { Bot, CreateQuestionAnswerParam } from "@/orval/models/backend-api";

import { CreateQuestionAnswerForm } from "./CreateQuestionAnswerForm";

type Props = {
  open: boolean;
  onClose: () => void;
  refetch: () => void;
  botId: Bot["id"];
};

export const CreateQuestionAnswerDialog = ({ open, onClose, refetch, botId }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger: createQuestionAnswer } = useCreateQuestionAnswer(botId);

  const handleCreateQuestionAnswer = async (params: CreateQuestionAnswerParam) => {
    try {
      await createQuestionAnswer(params);
      enqueueSuccessSnackbar({ message: "FAQを追加しました。" });
      refetch();
      onClose();
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({
        message: errMsg || "FAQの追加に失敗しました。",
      });
    }
  };

  return (
    <CustomDialog open={open} title="FAQの追加" maxWidth="md">
      <CreateQuestionAnswerForm onClose={onClose} onSubmit={handleCreateQuestionAnswer} />
    </CustomDialog>
  );
};
