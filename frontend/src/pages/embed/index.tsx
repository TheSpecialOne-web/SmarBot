import { Box } from "@mui/material";
import { useContext, useEffect, useRef, useState } from "react";
import { FormProvider, useForm } from "react-hook-form";
import { useLocation } from "react-router-dom";
import { useAsyncFn } from "react-use";

import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { LoadingDialog } from "@/components/dialogs/LoadingDialog";
import { CircularLoading } from "@/components/loadings/CircularLoading";
import { CONVERTIBLE_TO_PDF } from "@/const";
import { EmbedContext } from "@/contexts/EmbedContext";
import { useChat } from "@/hooks/useChat";
import { useChatScroll } from "@/hooks/useChatScroll";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { getErrorMessage } from "@/libs/error";
import { BaseChat } from "@/modules/chat/BaseChat";
import { ChatFirstView } from "@/modules/chat/ChatFirstView";
import { ChatMessages } from "@/modules/chat/ChatMessages";
import { ChatQuestionFormParams } from "@/modules/chat/ChatQuestionForm";
import { getDocumentSignedUrl, getQuestionAnswer } from "@/orval/api";
import {
  Approach,
  DataPoint,
  DataPointType,
  QuestionAnswer,
} from "@/orval/models/backend-api";
import { getFileExtension } from "@/utils/getFileExtension";

export const EmbedPage = () => {
  const [error, setError] = useState<unknown>();
  const [selectedQuestionAnswer, setSelectedQuestionAnswer] = useState<QuestionAnswer | null>(null);
  const [useWebBrowsing, setUseWebBrowsing] = useState<boolean>(false);

  const {
    isOpen: isQuestionAnswerDialogOpen,
    open: openQuestionAnswerDialog,
    close: closeQuestionAnswerDialog,
  } = useDisclosure({});

  const { endpointId, bot } = useContext(EmbedContext);

  const { search } = useLocation();
  const queryParams = new URLSearchParams(search);

  const { enqueueErrorSnackbar } = useCustomSnackbar();

  const {
    status,
    queries,
    isLoading: isLoadingCreateChatRequest,
    isStreaming,
    answers,
    streamedAnswers,
    onEmbedChatRequest,
    onStopChat,
    resetChat,
    onSendEmbeddedFeedback,
    isFeedbackSending,
  } = useChat();

  const hideCitationList = queryParams.get("hide_citations") === "true";

  const useFormMethods = useForm<ChatQuestionFormParams>({
    mode: "onChange",
    defaultValues: {
      question: "",
      attachmentIds: [],
    },
  });

  const { setValue, reset, setFocus } = useFormMethods;

  const chatRef = useRef<HTMLElement>();

  const { isAtBottom, scrollToBottom, scrollToBottomSmoothly, resetScrollBottom } = useChatScroll({
    chatRef,
    answers: streamedAnswers,
  });

  useEffect(() => {
    if (isAtBottom) {
      scrollToBottom();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streamedAnswers]);

  const onChatWithBot = async (question: string) => {
    if (error) {
      setError(undefined);
    }
    try {
      onEmbedChatRequest(question);
      reset();
    } catch (err) {
      const errMsg = getErrorMessage(err);
      enqueueErrorSnackbar({ message: errMsg || "チャットの送信に失敗しました。" });
      setError(err);
    }
  };

  const clearChat = () => {
    error && setError(undefined);
    resetChat();
    resetScrollBottom();
  };

  const onInput = (question: string) => {
    setValue("question", question, { shouldValidate: true });
    setFocus("question");
  };

  const [onShowCitationState, onShowCitation] = useAsyncFn(
    async (citation: DataPoint, _: number) => {
      // 社内ドキュメントのCitation
      if (citation.type === DataPointType.internal) {
        if (!citation.document_id) {
          return;
        }
        try {
          const url = await getDocumentSignedUrl(endpointId, citation.document_id);
          const extension = getFileExtension(citation.file_name);

          const displayUrl = CONVERTIBLE_TO_PDF.includes(extension)
            ? url.signed_url_pdf
            : url.signed_url_original;
          window.open(displayUrl, "_blank", "noopener noreferrer");
        } catch (error) {
          enqueueErrorSnackbar({ message: "ドキュメントの取得に失敗しました。" });
        }
        return;
      }

      // FAQのCitation
      if (citation.type === DataPointType.question_answer) {
        if (!citation.question_answer_id) {
          return;
        }
        openQuestionAnswerDialog();
        try {
          const questionAnswer = await getQuestionAnswer(endpointId, citation.question_answer_id);
          setSelectedQuestionAnswer(questionAnswer);
        } catch (error) {
          enqueueErrorSnackbar({ message: "FAQの取得に失敗しました。" });
        }
        return;
      }
      // Citation.type が不正な場合
      enqueueErrorSnackbar({ message: "参照元の取得に失敗しました。" });
    },
  );

  return (
    <FormProvider {...useFormMethods}>
      <BaseChat
        bot={bot}
        onChatWithBot={onChatWithBot}
        onStopChat={onStopChat}
        stoppableChat={isStreaming || isLoadingCreateChatRequest}
        isAtChatBottom={isAtBottom}
        scrollToChatBottomSmoothly={scrollToBottomSmoothly}
        enableAttachment={false}
        enableDocumentFolder={false}
        browsingProps={{
          botApproach: bot.approach || Approach.chat_gpt_default,
          enableWebBrowsing: bot.enable_web_browsing || false,
          useWebBrowsing,
          setUseWebBrowsing,
        }}
        initializeChat={clearChat}
        isEmbedded
      >
        <Box
          flex={1}
          py={2}
          pr={{ xs: 0, sm: 2 }}
          height="100%"
          ref={chatRef}
          position="relative"
          sx={{
            overflowX: "hidden",
            overflowY: "auto",
          }}
        >
          <>
            {answers.length === 0 && streamedAnswers.length === 0 ? (
              <ChatFirstView
                bot={bot}
                onInput={onInput}
                showPromptTemplates={false}
                isEmbedded
              />
            ) : (
              <ChatMessages
                status={status}
                queries={queries}
                onChatWithBot={onChatWithBot}
                onClickFeedback={onSendEmbeddedFeedback}
                isLoading={isLoadingCreateChatRequest}
                isStreaming={isStreaming}
                isFeedbackSending={isFeedbackSending}
                answers={answers}
                streamedAnswers={streamedAnswers}
                error={error}
                onShowCitation={onShowCitation}
                bot={bot}
                isEmbedded
                hideCitationList={hideCitationList}
              />
            )}
          </>
        </Box>
      </BaseChat>
      <LoadingDialog open={onShowCitationState.loading} />
      <CustomDialog
        open={isQuestionAnswerDialogOpen}
        onClose={closeQuestionAnswerDialog}
        title={selectedQuestionAnswer?.question || ""}
      >
        <CustomDialogContent>
          {onShowCitationState.loading ? <CircularLoading /> : selectedQuestionAnswer?.answer}
        </CustomDialogContent>
      </CustomDialog>
    </FormProvider>
  );
};
