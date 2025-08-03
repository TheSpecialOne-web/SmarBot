import { Stack, Typography } from "@mui/material";

import { AssistantAvatar } from "@/components/icons/AssistantAvatar";
import { Bot } from "@/orval/models/backend-api";

type Props = {
  bot: Bot;
};

export const BotProfile = ({ bot }: Props) => {
  return (
    <Stack direction="row" spacing={1} alignItems="center">
      <AssistantAvatar size={24} iconUrl={bot.icon_url} iconColor={bot.icon_color} />
      <Typography variant="h6" whiteSpace="pre-wrap">
        {bot.name}
      </Typography>
    </Stack>
  );
};
