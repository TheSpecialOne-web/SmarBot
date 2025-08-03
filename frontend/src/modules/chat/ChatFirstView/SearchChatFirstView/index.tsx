import { Spacer } from "@/components/spacers/Spacer";
import { BotIntroduction } from "@/modules/chat/ChatFirstView/BotIntroduction";
import { PromptTemplateCards } from "@/modules/chat/ChatFirstView/PromptTemplateCards";
import { useGetBotPromptTemplates } from "@/orval/backend-api";
import { Bot, BotPromptTemplate } from "@/orval/models/backend-api";

type Props = {
  onInput: (question: string) => void;
  bot: Bot;
  showPromptTemplates?: boolean;
};

export const SearchChatFirstView = ({ onInput, bot, showPromptTemplates = true }: Props) => {
  const { data, isValidating: loadingGetPromptTemplates } = useGetBotPromptTemplates(bot.id, {
    swr: {
      enabled: showPromptTemplates,
    },
  });
  const promptTemplates = data?.bot_prompt_templates || [];

  return (
    <>
      <BotIntroduction bot={bot} />
      <Spacer px={24} />
      {showPromptTemplates && (
        <PromptTemplateCards<BotPromptTemplate>
          promptTemplates={promptTemplates}
          onInput={onInput}
          loading={loadingGetPromptTemplates}
        />
      )}
    </>
  );
};
