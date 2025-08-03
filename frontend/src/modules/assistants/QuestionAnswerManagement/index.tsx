import Add from "@mui/icons-material/Add";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import { Stack, Typography } from "@mui/material";
import { useFlags } from "launchdarkly-react-client-sdk";
import { useState } from "react";

import { IconButtonWithTooltip } from "@/components/buttons/IconButtonWithTooltip";
import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { RefreshButton } from "@/components/buttons/RefreshButton";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { CustomTableSkeleton } from "@/components/loadings/TableSkeletonLoading";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { getErrorMessage } from "@/libs/error";
import { useGetQuestionAnswers } from "@/orval/backend-api";
import { Bot, QuestionAnswer } from "@/orval/models/backend-api";

import { BulkCreateOrUpdateQuestionAnswersDialog } from "./BulkCreateOrUpdateQuestionAnswersDialog";
import { CreateQuestionAnswerDialog } from "./CreateQuestionAnswerDialog";
import { DeleteQuestionAnswerDiaolog } from "./DeleteQuestionAnswerDialog";
import { QuestionAnswersTable } from "./QuestionAnswersTable";
import { UpdateQuestionAnswerDialog } from "./UpdateQuestionAnswerDialog";

type Props = {
  botId: Bot["id"];
  hasWritePolicy: boolean;
};

export const QuestionAnswerManagement = ({ botId, hasWritePolicy }: Props) => {
  const { tmpBulkOperationsOfQuestionAnswers } = useFlags();
  const {
    isOpen: isOpenCreateQuestionAnswerDialog,
    open: openCreateQuestionAnswerDialog,
    close: closeCreateQuestionAnswerDialog,
  } = useDisclosure({});

  const {
    isOpen: isOpenUpdateQuestionAnswerDialog,
    open: openUpdateQuestionAnswerDialog,
    close: closeUpdateQuestionAnswerDialog,
  } = useDisclosure({
    onClose: () => {
      setSelectedQuestionAnswer(null);
    },
  });

  const {
    isOpen: isOpenDeleteQuestionAnswerDialog,
    open: openDeleteQuestionAnswerDialog,
    close: closeDeleteQuestionAnswerDialog,
  } = useDisclosure({});

  const {
    isOpen: isOpenBulkCreateQuestionAnswersDialog,
    open: openBulkCreateQuestionAnswersDialog,
    close: closeBulkCreateQuestionAnswersDialog,
  } = useDisclosure({});

  const [selectedQuestionAnswer, setSelectedQuestionAnswer] = useState<QuestionAnswer | null>();

  const { enqueueErrorSnackbar } = useCustomSnackbar();

  const {
    data: questionAnswersData,
    error,
    isValidating: isLoadingGetQuestionAnswers,
    mutate: refetchQuestionAnswers,
  } = useGetQuestionAnswers(botId);
  const questionAnswers = questionAnswersData?.question_answers ?? [];
  if (error) {
    const errMsg = getErrorMessage(error);
    enqueueErrorSnackbar({ message: errMsg || "FAQの取得に失敗しました。" });
  }

  const handleOpenUpdateDialog = (questionAnswer: QuestionAnswer) => {
    setSelectedQuestionAnswer(questionAnswer);
    openUpdateQuestionAnswerDialog();
  };

  const handleOpenDeleteDialog = (questionAnswer: QuestionAnswer) => {
    setSelectedQuestionAnswer(questionAnswer);
    openDeleteQuestionAnswerDialog();
  };

  if (isLoadingGetQuestionAnswers) {
    return <CustomTableSkeleton />;
  }

  return (
    <>
      <ContentHeader>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Stack direction="row" alignItems="center" gap={0.5}>
            <Typography variant="h4">FAQ</Typography>
            <IconButtonWithTooltip
              tooltipTitle="質問と回答のセットをあらかじめ設定することで、指定した通りの回答を出力するようになります。"
              color="primary"
              icon={<HelpOutlineIcon sx={{ fontSize: 20 }} />}
              iconButtonSx={{ p: 0.5 }}
            />
          </Stack>
          <Stack direction="row" gap={2}>
            <RefreshButton onClick={refetchQuestionAnswers} />
            {hasWritePolicy && (
              <>
                <PrimaryButton
                  startIcon={<Add />}
                  text="追加"
                  onClick={openCreateQuestionAnswerDialog}
                />
                {tmpBulkOperationsOfQuestionAnswers && (
                  <PrimaryButton
                    text="一括追加"
                    onClick={openBulkCreateQuestionAnswersDialog}
                    variant="outlined"
                  />
                )}
              </>
            )}
          </Stack>
        </Stack>
      </ContentHeader>
      <QuestionAnswersTable
        questionAnswers={questionAnswers}
        hasWritePolicy={hasWritePolicy}
        onClickUpdateIcon={handleOpenUpdateDialog}
        onClickDeleteIcon={handleOpenDeleteDialog}
      />

      <CreateQuestionAnswerDialog
        open={isOpenCreateQuestionAnswerDialog}
        onClose={closeCreateQuestionAnswerDialog}
        refetch={refetchQuestionAnswers}
        botId={botId}
      />

      <BulkCreateOrUpdateQuestionAnswersDialog
        open={isOpenBulkCreateQuestionAnswersDialog}
        onClose={closeBulkCreateQuestionAnswersDialog}
        refetch={refetchQuestionAnswers}
        botId={botId}
      />

      {selectedQuestionAnswer && (
        <UpdateQuestionAnswerDialog
          open={isOpenUpdateQuestionAnswerDialog}
          onClose={closeUpdateQuestionAnswerDialog}
          questionAnswer={selectedQuestionAnswer}
          refetch={refetchQuestionAnswers}
          assistantId={botId}
        />
      )}
      {selectedQuestionAnswer && (
        <DeleteQuestionAnswerDiaolog
          open={isOpenDeleteQuestionAnswerDialog}
          onClose={closeDeleteQuestionAnswerDialog}
          questionAnswer={selectedQuestionAnswer}
          botId={botId}
          refetch={refetchQuestionAnswers}
        />
      )}
    </>
  );
};
