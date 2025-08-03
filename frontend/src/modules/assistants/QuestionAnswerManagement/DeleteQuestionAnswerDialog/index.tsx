import { Typography } from "@mui/material";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useDeleteQuestionAnswer } from "@/orval/backend-api";
import { Bot, QuestionAnswer } from "@/orval/models/backend-api";

type Props = {
  open: boolean;
  questionAnswer: QuestionAnswer;
  botId: Bot["id"];
  onClose: () => void;
  refetch: () => void;
};

export const DeleteQuestionAnswerDiaolog = ({
  open,
  questionAnswer,
  botId,
  onClose,
  refetch,
}: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger, isMutating } = useDeleteQuestionAnswer(botId, questionAnswer.id);

  const deleteQuestionAnswer = async () => {
    try {
      await trigger();
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "FAQを削除しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "FAQの削除に失敗しました。" });
    }
  };

  const deleteDialogContents = (
    <Typography>
      選択した質問:
      <Typography component="span" fontWeight="bold">
        {questionAnswer.question.length > 10
          ? questionAnswer?.question.slice(0, 10) + "..."
          : questionAnswer?.question}
      </Typography>
      を削除してもよろしいですか？
    </Typography>
  );

  return (
    <ConfirmDialog
      open={open}
      onClose={onClose}
      title="FAQ削除確認"
      content={deleteDialogContents}
      buttonText="削除"
      onSubmit={deleteQuestionAnswer}
      isLoading={isMutating}
    />
  );
};
