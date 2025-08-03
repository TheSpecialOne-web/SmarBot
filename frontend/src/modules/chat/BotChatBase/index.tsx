import { Box, Paper, Stack, Typography } from "@mui/material";
import { ReactNode } from "react";
import { useNavigate } from "react-router-dom";

import { AssistantAvatar } from "@/components/icons/AssistantAvatar";
import { BasicAiAvater } from "@/components/icons/BasicAiAvatar";
import { Text2ImageAvater } from "@/components/icons/Text2ImageAvater";
import { Spacer } from "@/components/spacers/Spacer";
import { useScreen } from "@/hooks/useScreen";
import { getBaseModelColor } from "@/libs/bot";
import { Approach, Bot, Feedback } from "@/orval/models/backend-api";

import { ChatActionButtons } from "./ChatActionButtons";

type Props = {
  children: ReactNode;
  bot: Bot;
  copyProps?: {
    onCopy: () => void;
    isCopied: boolean;
    displayCopyButton: boolean;
  };
  feedbackProps?: {
    onClickFeedback: (feedback: Feedback) => void;
    feedback?: Feedback;
    isFeedbackButtonVisible: boolean;
  };
  regenerateProps?: {
    onRegenerateAnswer: () => void;
    isRegenerateButtonVisible: boolean;
  };
  downloadProps?: {
    isDownloadButtonVisible: boolean;
    isDownloadingDocx: boolean;
    onClickDownloadDocx: () => void;
  };
  isEmbedded?: boolean;
};

export const BotChatBase = ({
  children,
  bot,
  copyProps,
  feedbackProps,
  regenerateProps,
  downloadProps,
  isEmbedded = false,
}: Props) => {
  const { isMobile } = useScreen();
  const navigate = useNavigate();
  const AvatarComponent =
    bot.approach === "text_2_image"
      ? Text2ImageAvater
      : bot.approach === "chat_gpt_default"
      ? BasicAiAvater
      : AssistantAvatar;

  const handleMoveToAssistantPage = () => {
    if (isMobile) return;
    navigate(`/main/assistants/${bot.id}`);
  };

  return (
    <Stack direction="row" spacing={1} sx={{ width: "100%" }}>
      <Box>
        <Spacer px={8} />
        <AvatarComponent
          size={24}
          onClick={
            ([Approach.neollm, Approach.custom_gpt, Approach.ursa] as string[]).includes(
              bot.approach,
            ) && !isEmbedded
              ? handleMoveToAssistantPage
              : undefined
          }
          iconUrl={bot.icon_url}
          iconColor={bot.icon_color}
          bgColor={getBaseModelColor(bot.model_family)}
        />
      </Box>
      <Box
        flex={1}
        sx={{
          width: `calc(100% - 40px)`,
        }}
      >
        <Typography variant="h6">{bot.name}</Typography>
        <Paper sx={{ width: "100%", px: 2, py: 1.5 }}>{children}</Paper>
        <ChatActionButtons
          displayCopyButton={copyProps?.displayCopyButton}
          isCopied={copyProps?.isCopied}
          onCopy={copyProps?.onCopy}
          isEmbeddedChat={isEmbedded}
          isRegenerateButtonVisible={regenerateProps?.isRegenerateButtonVisible}
          onRegenerateAnswer={regenerateProps?.onRegenerateAnswer}
          feedback={feedbackProps?.feedback}
          onClickFeedback={feedbackProps?.onClickFeedback}
          isFeedbackButtonVisible={feedbackProps?.isFeedbackButtonVisible}
          isDownloadButtonVisible={downloadProps?.isDownloadButtonVisible}
          isDownloadingDocx={downloadProps?.isDownloadingDocx}
          onClickDownloadDocx={downloadProps?.onClickDownloadDocx}
        />
      </Box>
    </Stack>
  );
};
