import { Typography } from "@mui/material";

import { Bot } from "@/orval/models/backend-api";

import { BotChatBase } from "../../BotChatBase";

type Props = {
  errorMessage: string;
  bot: Bot;
  isEmbedded?: boolean;
};

export const AnswerError = ({ errorMessage, bot, isEmbedded }: Props) => {
  return (
    <BotChatBase bot={bot} isEmbedded={isEmbedded}>
      <Typography color="error">{errorMessage}</Typography>
    </BotChatBase>
  );
};
