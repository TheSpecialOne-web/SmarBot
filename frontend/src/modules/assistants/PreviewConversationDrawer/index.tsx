import { Box, Drawer, Stack, Typography } from "@mui/material";
import { Fragment, useEffect, useRef } from "react";
import { FormProvider, useForm } from "react-hook-form";

import { useChatScroll } from "@/hooks/useChatScroll";
import { usePreviewConversation } from "@/hooks/usePreviewConversation";
import { Answer } from "@/modules/chat/Answer";
import { BotIntroduction } from "@/modules/chat/ChatFirstView/BotIntroduction";
import { AnswerLoading } from "@/modules/chat/ChatMessages/AnswerLoading";
import { ChatQuestionForm, ChatQuestionFormParams } from "@/modules/chat/ChatQuestionForm";
import { UserChatMessage } from "@/modules/chat/UserChatMessage";
import { Approach, Bot, BotStatus, ModelFamily, PdfParser } from "@/orval/models/backend-api";

type Props = {
  approach: Approach;
  name: string;
  description: string;
  exampleQuestions: string[];
  responseSystemPrompt: string | undefined;
  responseGeneratorModelFamily: ModelFamily;
  iconUrl?: string;
  iconColor: string;
  open: boolean;
  onClose: () => void;
};

export const PreviewConversationDrawer = ({
  approach,
  name,
  description,
  exampleQuestions,
  responseSystemPrompt,
  responseGeneratorModelFamily,
  iconUrl,
  iconColor,
  open,
  onClose,
}: Props) => {
  const {
    isLoading,
    isStreaming,
    answers,
    streamedAnswers,
    handleChatRequest,
    clearChat,
    handleStopChat,
  } = usePreviewConversation();

  const handleClose = () => {
    onClose();
    clearChat();
  };

  const useFormMethods = useForm<ChatQuestionFormParams>({
    mode: "onChange",
    defaultValues: {
      question: "",
      attachmentIds: [],
    },
  });

  const { reset } = useFormMethods;

  const answersToDisplay = isLoading || isStreaming ? streamedAnswers : answers;

  const handleChatWithBot = async (question: string) => {
    try {
      handleChatRequest(
        question,
        responseGeneratorModelFamily,
        responseSystemPrompt || "",
        approach,
      );
      reset();
    } catch (error) {
      console.error(error);
    }
  };

  const chatRef = useRef<HTMLElement>();
  const { isAtBottom, scrollToBottom } = useChatScroll({
    chatRef,
    answers: streamedAnswers,
  });

  useEffect(() => {
    if (isAtBottom) {
      scrollToBottom();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streamedAnswers]);

  const previewBot: Bot = {
    id: 0,
    name,
    description,
    created_at: "",
    example_questions: exampleQuestions,
    approach,
    model_family: responseGeneratorModelFamily,
    system_prompt: responseSystemPrompt || "",
    document_limit: 0,
    pdf_parser: PdfParser.pypdf,
    enable_web_browsing: false,
    status: BotStatus.active,
    enable_follow_up_questions: false,
    icon_url: iconUrl,
    icon_color: iconColor,
  };

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={handleClose}
      sx={{
        width: "50%",
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: "40%",
          boxSizing: "border-box",
          padding: 2,
          bgcolor: "primaryBackground.main",
        },
      }}
    >
      <Box flex={1} overflow="auto" pb={2} pr={2} height="100%" ref={chatRef}>
        <Typography
          variant="h5"
          sx={{
            textAlign: "center",
          }}
        >
          プレビュー
        </Typography>
        <Stack gap={2} mt={2}>
          {answers.length === 0 && <BotIntroduction bot={previewBot} />}
          {answersToDisplay.map((answer, index) => {
            const isLastAnswer = index === answers.length - 1;
            return (
              <Fragment key={index}>
                <UserChatMessage message={answer.user} />
                {isLastAnswer && isLoading ? (
                  <AnswerLoading bot={previewBot} status={undefined} queries={[]} />
                ) : (
                  <Answer
                    answer={{
                      answer: answer.bot.answer,
                      data_points: answer.bot.data_points,
                      follow_up_questions: answer.bot.follow_up_questions,
                      conversation_id: "",
                      conversation_turn_id: "",
                      query: [],
                    }}
                    isStreaming={isStreaming && isLastAnswer}
                    bot={previewBot}
                    onRegenerateAnswer={() => handleChatWithBot(answer.user)}
                  />
                )}
              </Fragment>
            );
          })}
        </Stack>
      </Box>
      <FormProvider {...useFormMethods}>
        <ChatQuestionForm
          bot={previewBot}
          onSend={handleChatWithBot}
          stoppable={isStreaming}
          onStopChat={handleStopChat}
        />
      </FormProvider>
    </Drawer>
  );
};
