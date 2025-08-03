import { Box, Typography } from "@mui/material";
import { useEffect, useRef, useState } from "react";
import { FormProvider, useForm } from "react-hook-form";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useParams } from "react-router-dom";
import { useAsyncFn } from "react-use";

import { CircularLoading } from "@/components/loadings/CircularLoading";
import { Spacer } from "@/components/spacers/Spacer";
import { CONVERTIBLE_TO_PDF } from "@/const";
import { useBot } from "@/hooks/useBot";
import { useChat } from "@/hooks/useChat";
import { useChatScroll } from "@/hooks/useChatScroll";
import { useConversation } from "@/hooks/useConversation";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { useScreen } from "@/hooks/useScreen";
import { useUserInfo } from "@/hooks/useUserInfo";
import { isUrsaBot } from "@/libs/bot";
import { getErrorMessage } from "@/libs/error";
import { AnalysisPanel } from "@/modules/chat/AnalysisPanel";
import { BaseChat } from "@/modules/chat/BaseChat";
import { ChatFirstView } from "@/modules/chat/ChatFirstView";
import { ChatMessages } from "@/modules/chat/ChatMessages";
import { ChatQuestionFormParams } from "@/modules/chat/ChatQuestionForm";
import { PreviewTenantGuidelineDrawer } from "@/modules/chat/PreviewTenantGuidelineDrawer";
import {
  getDocument,
  getQuestionAnswer,
  getTenantGuideline,
  useGetTenantGuidelines,
} from "@/orval/backend-api";
import {
  Approach,
  Attachment,
  Bot,
  ConversationEvent,
  DataPoint,
  DataPointType,
  DocumentFolder,
  Guideline,
  GuidelineDetail,
  QuestionAnswer,
} from "@/orval/models/backend-api";
import { DocumentToDisplay } from "@/types/document";

export const ChatPage = () => {
  const { bots, isLoadingFetchBots, reorderBots } = useBot();
  const [selectedBot, setSelectedBot] = useState<Bot>();

  const { userInfo } = useUserInfo();
  const tenantId = userInfo.tenant.id;

  const [error, setError] = useState<unknown>();

  const [activeDataPoint, setActiveDataPoint] = useState<DataPoint | null>(null);
  const [documentToDisplay, setDocumentToDisplay] = useState<DocumentToDisplay | null>(null);
  const [selectedQuestionAnswer, setSelectedQuestionAnswer] = useState<QuestionAnswer | null>(null);

  const [selectedAnswerIndex, setSelectedAnswerIndex] = useState<number>(0);
  const [isAnalysisOpen, setIsAnalysisOpen] = useState<boolean>(false);
  const [useWebBrowsing, setUseWebBrowsing] = useState<boolean>(false);

  const [searchParams, setSearchParams] = useSearchParams();
  const { conversationId } = useParams();

  const { isTablet } = useScreen();
  const { enqueueErrorSnackbar } = useCustomSnackbar();

  const navigate = useNavigate();

  const {
    status,
    queries,
    isLoading: isLoadingCreateChatRequest,
    isStreaming,
    answers,
    setAnswers,
    streamedAnswers,
    onChatRequest,
    clearChatHistory,
    onStopChat,
    responseConversationId,
    resetChat,
    onSendFeedback,
    isFeedbackSending,
  } = useChat();

  const { getConversation } = useConversation();

  const { data: getGuidelinesData, error: getGuidelinesError } = useGetTenantGuidelines(tenantId);
  if (getGuidelinesError) {
    const errMsg = getErrorMessage(getGuidelinesError);
    enqueueErrorSnackbar({
      message: errMsg || "ガイドラインの取得に失敗しました",
    });
  }
  const guidelines = getGuidelinesData?.guidelines ?? [];

  const [guidelineToPreview, setGuidelineToPreview] = useState<GuidelineDetail | null>(null);

  const {
    isOpen: isOpenPreviewGuidelineDrawer,
    open: openPreviewGuidelineDrawer,
    close: closePreviewGuidelineDrawer,
  } = useDisclosure({ onClose: () => setGuidelineToPreview(null) });

  const [
    { loading: isLoadingPreviewGuideline, error: previewGuidelineError },
    handleClickGuideline,
  ] = useAsyncFn(async (guideline: Guideline) => {
    try {
      const guidelineDetail = await getTenantGuideline(tenantId, guideline.id);
      setGuidelineToPreview(guidelineDetail);
      openPreviewGuidelineDrawer();
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "ガイドラインの表示に失敗しました。" });
    }
  });

  const useFormMethods = useForm<ChatQuestionFormParams>({
    mode: "onChange",
    defaultValues: {
      question: "",
      attachmentIds: [],
    },
  });

  const { setValue, setFocus } = useFormMethods;

  const [initConversationState, initConversation] = useAsyncFn(async () => {
    if (!conversationId || responseConversationId === conversationId) {
      return;
    }

    // conversationIdが存在してかつ、responseConversationIdと異なる場合、つまり履歴取得の場合
    try {
      clearChat();
      const conversation = await getConversationWithTurns(conversationId);
      if (!conversation) {
        return;
      }

      const bot = bots.find(bot => bot.id === conversation.bot_id);
      if (!bot) {
        return;
      }

      setSelectedBot(bot);
      setAnswers(
        conversation.turns.map(turn => {
          return {
            user: turn.user_input,
            bot: {
              conversation_id: conversation.id,
              answer: turn.bot_output.answer,
              data_points: turn.bot_output.data_points,
              conversation_turn_id: turn.id,
              event: ConversationEvent.response_generation_completed,
            },
            feedback: turn.feedback,
            conversationTurnId: turn.id,
            attachments: turn.attachments,
            documentFolder: turn?.document_folder,
          };
        }),
      );
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "チャット履歴の取得に失敗しました。" });
    }
  }, [conversationId, responseConversationId, bots]);

  useEffect(() => {
    initConversation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [responseConversationId, conversationId, bots]);

  useEffect(() => {
    if (conversationId || isLoadingFetchBots || bots.length === 0) {
      return;
    }
    const queryParamBotId = searchParams.get("botId");
    const botId = Number(queryParamBotId);
    const bot = botId && bots.find(bot => bot.id === botId);
    if (!botId || !bot) {
      setSearchParams({ botId: bots[0].id.toString() });
      clearChat();
      return;
    }
    reorderBots(bot);
    setSelectedBot(bot);
    clearChat();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, conversationId, isLoadingFetchBots, bots]);

  useEffect(() => {
    setUseWebBrowsing(false);
  }, [selectedBot]);

  const getConversationWithTurns = async (conversationId: string) => {
    return await getConversation(conversationId);
  };

  const { reset } = useFormMethods;

  const onChatWithBot = async (
    question: string,
    attachments?: Attachment[],
    documentFolder?: DocumentFolder,
  ) => {
    if (!selectedBot) {
      return;
    }
    if (error) {
      setError(undefined);
    }
    setActiveDataPoint(null);
    try {
      onChatRequest(
        selectedBot.id,
        question,
        useWebBrowsing,
        attachments,
        documentFolder,
        conversationId,
      );
      reset();
    } catch (err) {
      const errMsg = getErrorMessage(err);
      enqueueErrorSnackbar({ message: errMsg || "チャットの送信に失敗しました。" });
      setError(err);
    }
  };

  const clearChat = () => {
    error && setError(undefined);
    setActiveDataPoint(null);
    resetChat();
    clearChatHistory();
    resetScrollBottom();
  };

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

  const onInput = (question: string) => {
    setValue("question", question, { shouldValidate: true });
    setFocus("question");
  };

  const openAnalysisPanel = () => {
    setIsAnalysisOpen(true);
  };

  const closeAnalysisPanel = () => {
    setDocumentToDisplay(null);
    setIsAnalysisOpen(false);
  };

  const [onShowCitationState, onShowCitation] = useAsyncFn(
    async (citation: DataPoint, index: number) => {
      if (!selectedBot) {
        return;
      }

      // Web検索のCitation
      if (citation.type === DataPointType.web) {
        window.open(citation.url, "_blank", "noopener noreferrer");
        return;
      }

      setActiveDataPoint(citation);
      setSelectedAnswerIndex(index);
      openAnalysisPanel();
      // 社内ドキュメントのCitation
      if (citation.type === DataPointType.internal) {
        if (!citation.document_id) {
          return;
        }
        try {
          const document = await getDocument(selectedBot.id, citation.document_id);
          setDocumentToDisplay({
            name: document.name,
            extension: document.file_extension,
            displayUrl: CONVERTIBLE_TO_PDF.includes(document.file_extension)
              ? document.signed_url_pdf || ""
              : document.signed_url_original,
            downloadUrl: document.signed_url_original,
            externalUrl: document.external_url,
            documentFolderDetail: document.parent_document_folder,
          });
        } catch (error) {
          const errMsg = getErrorMessage(error);
          enqueueErrorSnackbar({ message: errMsg || "ドキュメントの取得に失敗しました。" });
        }
        return;
      }

      // FAQのCitation
      if (citation.type !== DataPointType.question_answer || !citation.question_answer_id) {
        return;
      }
      try {
        const questionAnswer = await getQuestionAnswer(selectedBot.id, citation.question_answer_id);
        setSelectedQuestionAnswer(questionAnswer);
      } catch (error) {
        enqueueErrorSnackbar({ message: "FAQの取得に失敗しました。" });
      }
      return;
    },
    [selectedBot],
  );

  const onToggleTab = (index: number) => {
    setSelectedAnswerIndex(index);
  };

  const onMoveToFolder = (folderId: string | null) => {
    if (!selectedBot) {
      return;
    }
    const folderQuery = folderId ? `&folderId=${folderId}` : "";
    navigate(`/main/assistants/${selectedBot.id}?tabKey=document${folderQuery}`);
  };

  const initializeChat = () => {
    clearChat();
    navigate(`/main/chat?botId=${selectedBot?.id}`);
  };

  const enableAttachment =
    selectedBot?.approach &&
    ([Approach.chat_gpt_default, Approach.neollm, Approach.custom_gpt] as string[]).includes(
      selectedBot?.approach,
    );

  return (
    <>
      <FormProvider {...useFormMethods}>
        {selectedBot && (
          <BaseChat
            bot={selectedBot}
            onChatWithBot={onChatWithBot}
            onStopChat={onStopChat}
            stoppableChat={isStreaming || isLoadingCreateChatRequest}
            isAtChatBottom={isAtBottom}
            scrollToChatBottomSmoothly={scrollToBottomSmoothly}
            enableAttachment={enableAttachment}
            browsingProps={{
              botApproach: selectedBot.approach || Approach.chat_gpt_default,
              enableWebBrowsing:
                selectedBot.approach === Approach.chat_gpt_default
                  ? Boolean(userInfo.tenant?.enable_basic_ai_web_browsing)
                  : selectedBot.enable_web_browsing,
              useWebBrowsing,
              setUseWebBrowsing,
            }}
            initializeChat={initializeChat}
            guidelines={guidelines}
            onClickGuideline={handleClickGuideline}
          >
            {isTablet ? (
              answers.length > 0 || isStreaming ? (
                <>
                  <Spacer px={16} />
                  <Typography variant="h6" textAlign="center">
                    {selectedBot.name}
                  </Typography>
                  <Spacer px={8} />
                </>
              ) : (
                <Spacer px={64} />
              )
            ) : null}
            <Box
              flex={1}
              pr="1px"
              height="100%"
              ref={chatRef}
              position="relative"
              sx={{
                overflowX: "hidden",
                overflowY: "auto",
              }}
            >
              {initConversationState.loading ? (
                <Box
                  position="absolute"
                  sx={{
                    top: "50%",
                    left: "50%",
                    transform: "translate(-50%, -50%)",
                  }}
                >
                  {!isLoadingFetchBots && bots.length === 0 ? (
                    <Typography>データがありません</Typography>
                  ) : (
                    <CircularLoading />
                  )}
                </Box>
              ) : (
                <>
                  {!isTablet && <Spacer px={24} />}
                  {answers.length === 0 && streamedAnswers.length === 0 ? (
                    <ChatFirstView bot={selectedBot} onInput={onInput} />
                  ) : (
                    <>
                      <ChatMessages
                        status={status}
                        queries={queries}
                        onChatWithBot={onChatWithBot}
                        onClickFeedback={onSendFeedback}
                        isLoading={isLoadingCreateChatRequest}
                        isStreaming={isStreaming}
                        isFeedbackSending={isFeedbackSending}
                        answers={answers}
                        streamedAnswers={streamedAnswers}
                        error={error}
                        onShowCitation={onShowCitation}
                        bot={selectedBot}
                      />
                      {isStreaming && <Spacer px={32} />}
                    </>
                  )}

                  {(answers.length > 0 || streamedAnswers.length > 0) && activeDataPoint && (
                    <AnalysisPanel
                      isOpen={isAnalysisOpen}
                      isLoadingGetCitation={onShowCitationState.loading}
                      onClose={closeAnalysisPanel}
                      activeDataPoint={activeDataPoint}
                      documentToDisplay={documentToDisplay}
                      onActiveTabChanged={() => onToggleTab(selectedAnswerIndex)}
                      dataPoints={
                        isStreaming
                          ? streamedAnswers[selectedAnswerIndex]?.bot.data_points
                          : answers[selectedAnswerIndex]?.bot.data_points
                      }
                      questionAnswer={selectedQuestionAnswer}
                      showTab={!isUrsaBot(selectedBot)}
                      onMoveToFolder={onMoveToFolder}
                    />
                  )}
                </>
              )}
            </Box>
          </BaseChat>
        )}
      </FormProvider>

      {guidelineToPreview && (
        <PreviewTenantGuidelineDrawer
          open={isOpenPreviewGuidelineDrawer}
          onClose={closePreviewGuidelineDrawer}
          guidelineDetail={guidelineToPreview}
          loading={isLoadingPreviewGuideline}
          error={Boolean(previewGuidelineError)}
        />
      )}
    </>
  );
};
