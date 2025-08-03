import { Stack, Typography } from "@mui/material";

import { BasicAiAvater } from "@/components/icons/BasicAiAvatar";
import { Text2ImageAvater } from "@/components/icons/Text2ImageAvater";
import { getBaseModelColor } from "@/libs/bot";
import { Bot } from "@/orval/models/backend-api";

type Props = {
  bot: Bot;
};

export const BasicAiBotProfile = ({ bot }: Props) => {
  const AvatarComponent = bot.approach === "text_2_image" ? Text2ImageAvater : BasicAiAvater;

  return (
    <Stack direction="row" alignItems="center" justifyContent="space-between" width="100%">
      <Stack direction="row" spacing={1} alignItems="center">
        <AvatarComponent size={24} bgColor={getBaseModelColor(bot.model_family)} />
        <Typography variant="h6" whiteSpace="pre-wrap">
          {bot.name}
        </Typography>
      </Stack>
    </Stack>
  );
};
