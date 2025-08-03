import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useUpdateQuestionAnswer } from "@/orval/backend-api";
import { Bot, QuestionAnswer, UpdateQuestionAnswerParam } from "@/orval/models/backend-api";

import { UpdateQuestionAnswerForm } from "./UpdateQuestionAnswerForm";

type Props = {
  open: boolean;
  onClose: () => void;
  questionAnswer: QuestionAnswer;
  refetch: () => void;
  assistantId: Bot["id"];
};

export const UpdateQuestionAnswerDialog = ({
  open,
  onClose,
  refetch,
  questionAnswer,
  assistantId,
}: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger: updateQuestionAnswer } = useUpdateQuestionAnswer(assistantId, questionAnswer.id);

  const handleUpdateQuestionAnswer = async (params: UpdateQuestionAnswerParam) => {
    try {
      await updateQuestionAnswer(params);
      enqueueSuccessSnackbar({ message: "FAQを更新しました。" });
      refetch();
      onClose();
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({
        message: errMsg || "FAQの更新に失敗しました。",
      });
    }
  };

  return (
    <CustomDialog open={open} title="FAQの編集" maxWidth="md">
      <UpdateQuestionAnswerForm
        questionAnswer={questionAnswer}
        onClose={onClose}
        onSubmit={handleUpdateQuestionAnswer}
      />
    </CustomDialog>
  );
};
