import { Stack, Typography } from "@mui/material";

import { AssistantAvatar } from "@/components/icons/AssistantAvatar";
import { BasicAiAvater } from "@/components/icons/BasicAiAvatar";
import { Text2ImageAvater } from "@/components/icons/Text2ImageAvater";
import { CHAT_LAYOUT_SIDEBAR_WIDTH } from "@/const";
import { getBaseModelColor, isChatGptBot } from "@/libs/bot";
import { Bot } from "@/orval/models/backend-api";

type Props = {
  bot: Bot;
};

export const SelectedBotDisplay = ({ bot }: Props) => {
  const AvatarComponent = bot.approach === "text_2_image" ? Text2ImageAvater : BasicAiAvater;
  return (
    <Stack direction="row" spacing={1} alignItems="center">
      {!isChatGptBot(bot) ? (
        <AssistantAvatar size={24} iconUrl={bot.icon_url} iconColor={bot.icon_color} />
      ) : (
        <AvatarComponent size={24} bgColor={getBaseModelColor(bot.model_family)} />
      )}
      <Typography
        variant="h5"
        whiteSpace="nowrap"
        overflow="hidden"
        textOverflow="ellipsis"
        maxWidth={CHAT_LAYOUT_SIDEBAR_WIDTH - 115}
      >
        {bot.name}
      </Typography>
    </Stack>
  );
};
