import { useState } from "react";
import { FormProvider, useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";

import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { getErrorMessage } from "@/libs/error";
import { deleteBotIcon, updateBot, uploadBotIcon, useGetBots } from "@/orval/backend-api";
import { Bot, BotStatus, UpdateBotParam, UserTenant } from "@/orval/models/backend-api";

import { PreviewConversationDrawer } from "../PreviewConversationDrawer";
import { UpdateAssistantForm } from "../UpdateAssistantForm";

type Props = {
  bot: Bot;
  tenant: UserTenant;
  groupId?: number;
};

export const UpdateAssistantContents = ({ bot, tenant, groupId }: Props) => {
  const [iconUrl, setIconUrl] = useState<string | null>(bot.icon_url || null);

  const useFormMethods = useForm<UpdateBotParam>({
    defaultValues: {
      ...bot,
      max_conversation_turns: bot.max_conversation_turns === null ? 0 : bot.max_conversation_turns,
    },
  });

  const { mutate: refetchBots } = useGetBots({ status: [BotStatus.active] });
  const { watch } = useFormMethods;
  const navigate = useNavigate();
  const { enqueueSuccessSnackbar, enqueueErrorSnackbar } = useCustomSnackbar();

  const handleUpdateBot = async (
    data: UpdateBotParam,
    icon: File | null,
    currentIconUrl: string | null,
  ) => {
    try {
      const paramsForUpdate = {
        ...data,
        max_conversation_turns:
          data.max_conversation_turns === 0 ? null : data.max_conversation_turns,
      };
      await Promise.all([
        updateBot(bot.id, paramsForUpdate),
        icon ? uploadBotIcon(bot.id, { file: icon }) : Promise.resolve(),
        !icon && !currentIconUrl ? deleteBotIcon(bot.id) : Promise.resolve(),
      ]);
      enqueueSuccessSnackbar({ message: "アシスタントを更新しました。" });
      navigate(
        groupId ? `/main/groups/${groupId}/assistants/${bot.id}` : `/main/assistants/${bot.id}`,
      );
      refetchBots();
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({
        message: errMsg || "アシスタントの更新に失敗しました。",
      });
    }
  };

  const {
    isOpen: isOpenPreviewConversationDrawer,
    open: openPreviewConversationDrawer,
    close: closePreviewConversationDrawer,
  } = useDisclosure({});

  return (
    <>
      <FormProvider {...useFormMethods}>
        <UpdateAssistantForm
          onSubmit={handleUpdateBot}
          handleOpenPreviewConversationDrawer={openPreviewConversationDrawer}
          allowedModelFamilies={tenant.allowed_model_families}
          enableDocumentIntelligence={tenant.enable_document_intelligence}
          enableLLMDocumentReader={tenant.enable_llm_document_reader}
          bot={bot}
          iconUrl={iconUrl}
          setIconUrl={setIconUrl}
        />
      </FormProvider>
      <PreviewConversationDrawer
        approach={watch("approach")}
        name={watch("name")}
        description={watch("description")}
        exampleQuestions={watch("example_questions")}
        responseSystemPrompt={watch("system_prompt")}
        responseGeneratorModelFamily={watch("model_family")}
        iconUrl={iconUrl || undefined}
        iconColor={watch("icon_color")}
        open={isOpenPreviewConversationDrawer}
        onClose={closePreviewConversationDrawer}
      />
    </>
  );
};
