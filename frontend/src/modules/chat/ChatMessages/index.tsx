import { Box, Stack } from "@mui/material";
import { Fragment } from "react";

import {
  Attachment,
  Bot,
  ConversationEvent,
  DataPoint,
  Feedback,
} from "@/orval/models/backend-api";
import { ChatSession } from "@/types/chat";

import { Answer } from "../Answer";
import { UserChatMessage } from "../UserChatMessage";
import { AnswerError } from "./AnswerError";
import { AnswerLoading } from "./AnswerLoading";
import { FollowUpQuestions } from "./FollowUpQuestions";

type Props = {
  status: ConversationEvent | undefined;
  queries: string[];
  onShowCitation: (citation: DataPoint, index: number) => void;
  onChatWithBot: (question: string, attachments?: Attachment[]) => Promise<void>;
  onClickFeedback: (conversationTurnId: string, feedback: Feedback) => void;
  isLoading: boolean;
  isStreaming: boolean;
  isFeedbackSending: boolean;
  answers: ChatSession[];
  streamedAnswers: ChatSession[];
  bot: Bot;
  error: unknown;
  isEmbedded?: boolean;
  hideCitationList?: boolean;
};

export const ChatMessages = ({
  status,
  queries,
  onShowCitation,
  onChatWithBot,
  onClickFeedback,
  isLoading,
  isStreaming,
  bot,
  answers,
  streamedAnswers,
  error,
  isEmbedded = false,
  hideCitationList = false,
}: Props) => {
  const answersToDisplay = isLoading || isStreaming ? streamedAnswers : answers;

  return (
    <Stack gap={2} sx={{ pl: 0.5 }}>
      {answersToDisplay.map((answer, index) => {
        const isLastAnswer = index == answers.length - 1;

        return (
          <Fragment key={index}>
            <UserChatMessage
              botId={bot.id}
              message={answer.user}
              attachments={answer.attachments}
              documentFolder={answer.documentFolder}
            />

            {isLastAnswer && isLoading ? (
              <AnswerLoading bot={bot} status={status} queries={queries} isEmbedded={isEmbedded} />
            ) : error && isLastAnswer ? (
              <AnswerError errorMessage={error.toString()} bot={bot} isEmbedded={isEmbedded} />
            ) : (
              <Answer
                answer={answer.bot}
                feedback={answer.feedback}
                onClickCitation={c => onShowCitation(c, index)}
                isStreaming={isStreaming && isLastAnswer}
                bot={bot}
                conversationId={answer.bot.conversation_id}
                conversationTurnId={answer.bot.conversation_turn_id}
                onClickFeedback={onClickFeedback}
                onRegenerateAnswer={() => onChatWithBot(answer.user, answer.attachments)}
                isEmbedded={isEmbedded}
                hideCitationList={hideCitationList}
              />
            )}
            {isLastAnswer &&
              !isLoading &&
              !isStreaming &&
              answer.bot.follow_up_questions &&
              answer.bot.follow_up_questions.length > 0 && (
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "right",
                  }}
                >
                  <FollowUpQuestions
                    questions={answer.bot.follow_up_questions}
                    onQuestionClicked={onChatWithBot}
                  />
                </Box>
              )}
          </Fragment>
        );
      })}
    </Stack>
  );
};
