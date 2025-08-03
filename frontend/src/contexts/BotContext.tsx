import { createContext, ReactNode } from "react";

import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useLocalStorage } from "@/hooks/useLocalStorage";
import { useUserInfo } from "@/hooks/useUserInfo";
import { isChatGptBot, isUrsaBot } from "@/libs/bot";
import { getErrorMessage } from "@/libs/error";
import { useGetBots } from "@/orval/backend-api";
import { Bot, BotStatus, BotWithGroups, TenantStatus } from "@/orval/models/backend-api";

type BotContextType = {
  bots: Bot[];
  reorderBots: (bot: Bot) => void;
  // chatGPTボット
  chatGptBots: Bot[];
  // chatGPT以外のボット
  assistants: Bot[];
  // 資料検索とchatGPT以外のボット
  dataChatBots: Bot[];
  // 資料検索ボット
  searchChatBots: Bot[];
  fetchBots: () => void;
  isLoadingFetchBots: boolean;
};

export const BotContext = createContext<BotContextType>({
  bots: [],
  reorderBots: () => {},
  assistants: [],
  chatGptBots: [],
  dataChatBots: [],
  searchChatBots: [],
  fetchBots: async () => {},
  isLoadingFetchBots: true,
});

export const BotContextProvider = ({ children }: { children: ReactNode }) => {
  const { userInfo } = useUserInfo();
  const { enqueueErrorSnackbar } = useCustomSnackbar();

  const [storedBotIdsOrder, setStoredBotIdsOrder] = useLocalStorage<number[]>("botsOrder", []);
  const onSuccessGetBots = (data: BotWithGroups) => {
    setStoredBotIdsOrder(prev => {
      const botIdsToAdd = data.bots.filter(bot => !prev.includes(bot.id)).map(bot => bot.id);
      const botIdsToRemove = prev.filter(id => !data.bots.some(bot => bot.id === id));
      return [...botIdsToAdd, ...prev.filter(id => !botIdsToRemove.includes(id))];
    });
  };

  const {
    data: botsData,
    isValidating: isLoadingFetchBots,
    error: getBotsError,
    mutate: getBots,
  } = useGetBots(
    {
      status: [BotStatus.active],
    },
    {
      swr: {
        enabled: !userInfo.tenant.ip_blocked && userInfo.tenant.status !== TenantStatus.suspended,
        onSuccess: onSuccessGetBots,
        swrKey: "BotContext.getBots", // 他の useGetBots と区別するためのキー
      },
    },
  );
  const bots = botsData?.bots ?? [];
  if (getBotsError) {
    const errMsg = getErrorMessage(getBotsError);
    enqueueErrorSnackbar({ message: errMsg || "基盤モデルとアシスタントの取得に失敗しました。" });
  }

  const reorderBots = (bot: Bot) => {
    setStoredBotIdsOrder(prev => [bot.id, ...prev.filter(id => id !== bot.id)]);
  };

  const orderedBots = bots.sort(
    (a, b) => storedBotIdsOrder.indexOf(a.id) - storedBotIdsOrder.indexOf(b.id),
  );

  return (
    <BotContext.Provider
      value={{
        bots,
        reorderBots,
        assistants: orderedBots?.filter(bot => !isChatGptBot(bot)),
        dataChatBots: orderedBots?.filter(bot => !isChatGptBot(bot) && !isUrsaBot(bot)),
        chatGptBots: orderedBots?.filter(bot => isChatGptBot(bot)),
        searchChatBots: orderedBots?.filter(bot => isUrsaBot(bot)),
        fetchBots: getBots,
        isLoadingFetchBots,
      }}
    >
      {children}
    </BotContext.Provider>
  );
};
