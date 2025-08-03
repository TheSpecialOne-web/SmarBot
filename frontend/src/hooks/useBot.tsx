import { useContext } from "react";

import { BotContext } from "@/contexts/BotContext";

export const useBot = () => {
  const {
    bots,
    reorderBots,
    assistants,
    chatGptBots,
    searchChatBots,
    dataChatBots,
    fetchBots,
    isLoadingFetchBots,
  } = useContext(BotContext);

  return {
    bots,
    reorderBots,
    assistants,
    chatGptBots,
    searchChatBots,
    dataChatBots,
    fetchBots,
    isLoadingFetchBots,
  };
};
