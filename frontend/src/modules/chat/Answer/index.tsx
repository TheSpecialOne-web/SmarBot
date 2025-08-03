import { Divider, Stack } from "@mui/material";
import dayjs from "dayjs";
import { useState } from "react";
import { useAsyncFn } from "react-use";

import { Spacer } from "@/components/spacers/Spacer";
import { CustomMarkdown } from "@/components/texts/CustomMarkdown";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { isUrsaBot } from "@/libs/bot";
import { getErrorMessage } from "@/libs/error";
import { transformAnswer, transformAnswerToStringForCopy } from "@/libs/formatAnswer";
import { BotChatBase } from "@/modules/chat/BotChatBase";
import { convertFile, useGetConversationTurnDataPoints } from "@/orval/backend-api";
import {
  Bot,
  ConversationResponse,
  DataPoint,
  DocumentFeedbackSummary,
  Feedback,
} from "@/orval/models/backend-api";
import { downloadFile } from "@/utils/downloadFile";
import { isNotUndefined } from "@/utils/primitive";

import { AnswersTable } from "./AnswersTable";
import { CitationList } from "./CitationList";

type Props = {
  answer: ConversationResponse;
  onClickCitation?: (citation: DataPoint) => void;
  onClickFeedback?: (conversationTurnId: string, feedback: Feedback) => void;
  isStreaming: boolean;
  conversationTurnId?: string;
  bot: Bot;
  feedback?: Feedback;
  onRegenerateAnswer: () => void;
  isEmbedded?: boolean;
  hideCitationList?: boolean;
  conversationId?: string;
};

export const Answer = ({
  answer,
  onClickCitation,
  onClickFeedback: onClickFeedbackProp,
  feedback,
  isStreaming,
  conversationTurnId,
  bot,
  onRegenerateAnswer,
  isEmbedded = false,
  hideCitationList = false,
  conversationId,
}: Props) => {
  const [isCopied, setIsCopied] = useState(false);

  const { enqueueErrorSnackbar } = useCustomSnackbar();

  let transformedAnswer = isUrsaBot(bot)
    ? answer.answer
    : transformAnswer(answer.answer, answer.data_points);
  if (isUrsaBot(bot) && answer.data_points.length === 0 && !isStreaming) {
    transformedAnswer = "検索した結果、該当資料は見つかりませんでした。"; // TODO: API で返すべき
  }

  const onCopy = async () => {
    try {
      const formattedAnswer = transformAnswerToStringForCopy(answer.answer, answer.data_points);
      await navigator.clipboard.writeText(formattedAnswer);
      setIsCopied(true);
    } catch (err) {
      const errMsg = getErrorMessage(err);
      enqueueErrorSnackbar({
        message: errMsg || "クリップボードへのコピーに失敗しました。",
      });
    }
    setTimeout(() => setIsCopied(false), 2000);
  };

  const onClickFeedback = (fb: Feedback) => {
    if (conversationTurnId && onClickFeedbackProp && fb) {
      onClickFeedbackProp(conversationTurnId, fb);
    }
  };

  const [onDownloadDocxState, onDownloadDocx] = useAsyncFn(async (content: string) => {
    try {
      const data = await convertFile({
        content,
        file_extension: "docx",
      });
      downloadFile(`neoAI-Chat-${dayjs().format("YYYYMMDDHHmm")}.docx`, data);
    } catch (error) {
      enqueueErrorSnackbar({ message: "チャットのダウンロードに失敗しました。" });
    }
  });

  const isFeedbackButtonVisible = !isStreaming && Boolean(conversationTurnId);

  const {
    data: dataPointsData,
    error: getDataPointsError,
    mutate: refetchDataPoints,
  } = useGetConversationTurnDataPoints(conversationId ?? "", conversationTurnId ?? "", {
    swr: { enabled: Boolean(conversationId && conversationTurnId) && isUrsaBot(bot) },
  });
  if (getDataPointsError) {
    const errMsg = getErrorMessage(getDataPointsError);
    enqueueErrorSnackbar({ message: errMsg || "ドキュメントの取得に失敗しました。" });
  }
  const dataPoints = dataPointsData?.data_points ?? [];
  const documentIdToDocumentFeedbackMap = new Map<number, DocumentFeedbackSummary>(
    dataPoints
      .map(({ document_id, document_feedback_summary }) =>
        document_id && document_feedback_summary
          ? ([document_id, document_feedback_summary] as const)
          : undefined,
      )
      .filter(isNotUndefined),
  );

  return (
    <BotChatBase
      bot={bot}
      copyProps={{
        onCopy,
        isCopied,
        displayCopyButton: !isStreaming && !isUrsaBot(bot),
      }}
      feedbackProps={{
        onClickFeedback,
        feedback,
        isFeedbackButtonVisible,
      }}
      regenerateProps={{
        onRegenerateAnswer,
        isRegenerateButtonVisible: !isStreaming,
      }}
      downloadProps={{
        isDownloadButtonVisible: !isStreaming && !isUrsaBot(bot),
        isDownloadingDocx: onDownloadDocxState.loading,
        onClickDownloadDocx: () => onDownloadDocx(transformedAnswer),
      }}
      isEmbedded={isEmbedded}
    >
      {!hideCitationList && !isUrsaBot(bot) && answer.data_points.length > 0 && onClickCitation && (
        <Stack gap={1}>
          <CitationList dataPoints={answer.data_points} onClickCitation={onClickCitation} />
          <Divider />
        </Stack>
      )}
      <CustomMarkdown
        markdown={transformedAnswer}
        dataPoints={answer.data_points}
        onClickCitation={onClickCitation}
      />
      {isUrsaBot(bot) && answer.data_points.length > 0 && !isStreaming && onClickCitation && (
        <>
          <Spacer px={16} />
          <AnswersTable
            dataPoints={answer.data_points}
            onClickCitation={onClickCitation}
            botId={bot.id}
            documentIdToDocumentFeedbackMap={documentIdToDocumentFeedbackMap}
            refetchDataPoints={refetchDataPoints}
          />
        </>
      )}
    </BotChatBase>
  );
};
