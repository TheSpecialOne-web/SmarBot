import CommentIcon from "@mui/icons-material/Comment";
import CommentOutlinedIcon from "@mui/icons-material/CommentOutlined";
import ThumbDownAltIcon from "@mui/icons-material/ThumbDownAlt";
import ThumbDownOffAltIcon from "@mui/icons-material/ThumbDownOffAlt";
import ThumbUpIcon from "@mui/icons-material/ThumbUp";
import ThumbUpOffAltIcon from "@mui/icons-material/ThumbUpOffAlt";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { useAsyncFn } from "react-use";

import { ChatIconButton } from "@/components/buttons/ChatIconButton";
import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { Feedback } from "@/orval/models/backend-api";
import { Evaluation } from "@/orval/models/backend-api/evaluation";

type Props = {
  feedback?: Feedback;
  onClickFeedback: (feedback: Feedback) => void;
};

export const FeedbackButtons = ({ feedback, onClickFeedback }: Props) => {
  const { isOpen: open, close: onClose, open: onOpen } = useDisclosure({});

  const { control, watch, handleSubmit, setValue } = useForm({
    defaultValues: {
      comment: feedback?.comment ?? "",
      evaluation: feedback?.evaluation,
    },
  });

  const [evaluation, comment] = watch(["evaluation", "comment"]);
  const isFeedbackGood = evaluation === Evaluation.good;
  const isFeedbackBad = evaluation === Evaluation.bad;
  const { enqueueSuccessSnackbar, enqueueErrorSnackbar } = useCustomSnackbar();
  const [isFeedbackSent, setIsFeedbackSent] = useState(
    Boolean(feedback && (feedback.comment || feedback.evaluation)),
  );

  const [{ loading: isFeedbackSending }, handleSave] = useAsyncFn(
    async (data: { comment: Feedback["comment"]; evaluation: Feedback["evaluation"] }) => {
      const updatedFeedback: Feedback = {
        ...feedback,
        comment: data.comment,
        evaluation: data.evaluation,
      };
      try {
        await onClickFeedback(updatedFeedback);
        enqueueSuccessSnackbar({ message: "フィードバックが送信されました" });
      } catch (error) {
        enqueueErrorSnackbar({ message: "フィードバックの送信に失敗しました" });
      }
      setIsFeedbackSent(true);
      onClose();
    },
  );

  return (
    <>
      <ChatIconButton
        tooltipTitle="フィードバック"
        icon={
          isFeedbackSent ? (
            <CommentIcon fontSize="small" />
          ) : (
            <CommentOutlinedIcon fontSize="small" />
          )
        }
        onClick={onOpen}
      />
      <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
        <DialogTitle>フィードバックを送信</DialogTitle>
        <form noValidate onSubmit={handleSubmit(handleSave)}>
          <DialogContent>
            <Stack direction="row" spacing={1}>
              <ChatIconButton
                tooltipTitle="良い回答"
                icon={
                  isFeedbackGood ? (
                    <ThumbUpIcon fontSize="small" />
                  ) : (
                    <ThumbUpOffAltIcon fontSize="small" />
                  )
                }
                onClick={() => {
                  if (!isFeedbackSent) {
                    setValue("evaluation", !isFeedbackGood ? Evaluation.good : undefined);
                  }
                }}
                disabled={isFeedbackSent}
              />
              <ChatIconButton
                tooltipTitle="良くない回答"
                icon={
                  isFeedbackBad ? (
                    <ThumbDownAltIcon fontSize="small" />
                  ) : (
                    <ThumbDownOffAltIcon fontSize="small" />
                  )
                }
                onClick={() => {
                  if (!isFeedbackSent) {
                    setValue("evaluation", !isFeedbackBad ? Evaluation.bad : undefined);
                  }
                }}
                disabled={isFeedbackSent}
              />
            </Stack>
            <Controller
              name="comment"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  autoFocus
                  margin="dense"
                  label="コメント"
                  type="text"
                  fullWidth
                  variant="standard"
                  disabled={isFeedbackSent}
                />
              )}
            />
          </DialogContent>
          <CustomDialogAction
            onClose={onClose}
            buttonText="送信"
            loading={isFeedbackSending}
            disabled={isFeedbackSent || isFeedbackSending || (!evaluation && !comment)}
          />
        </form>
      </Dialog>
    </>
  );
};
