import { Spacer } from "@/components/spacers/Spacer";
import { useGetBotPromptTemplates } from "@/orval/backend-api";
import { Bot, BotPromptTemplate } from "@/orval/models/backend-api";

import { BotIntroduction } from "../BotIntroduction";
import { PromptTemplateCards } from "../PromptTemplateCards";

type Props = {
  onInput: (question: string) => void;
  bot: Bot;
  showPromptTemplates?: boolean;
  isEmbedded?: boolean;
};

export const AssistantChatFirstView = ({
  onInput,
  bot,
  showPromptTemplates = true,
  isEmbedded = false,
}: Props) => {
  const { data, isValidating: loadingGetPromptTemplates } = useGetBotPromptTemplates(bot.id, {
    swr: {
      enabled: showPromptTemplates,
    },
  });
  const promptTemplates = data?.bot_prompt_templates || [];

  return (
    <>
      <BotIntroduction bot={bot} isEmbedded={isEmbedded} />
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
