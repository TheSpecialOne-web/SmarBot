import { Stack } from "@mui/material";

import { AssistantAvatar } from "@/components/icons/AssistantAvatar";
import { getTextGenerationModelFamiliesFromAllowedModelFamilies } from "@/libs/administrator/model";
import { CreateBotParam, ModelFamilies, Tenant } from "@/orval/models/administrator-api";

import { BotParamField } from "./BotParamField";

type Props = {
  createBotParams: CreateBotParam;
  iconUrl: string | null;
  tenantName: Tenant["name"];
  allowedModelFamilies: ModelFamilies;
};

export const ConfirmCreateBot = ({
  createBotParams,
  iconUrl,
  tenantName,
  allowedModelFamilies,
}: Props) => {
  const allowedTextGenerationModelFamilies =
    getTextGenerationModelFamiliesFromAllowedModelFamilies(allowedModelFamilies);

  return (
    <>
      <Stack gap={2}>
        <AssistantAvatar
          size={60}
          iconUrl={iconUrl ? undefined : createBotParams.icon_url}
          iconColor={createBotParams.icon_color}
        />
        <BotParamField title="テナント名" value={tenantName} />
        <BotParamField title="ボット名" value={createBotParams.name} />
        <BotParamField title="説明" value={createBotParams.description} />
        <BotParamField
          title="回答生成モデル"
          value={
            allowedTextGenerationModelFamilies.find(
              mf => mf === createBotParams.response_generator_model_family,
            ) || allowedTextGenerationModelFamilies[0]
          }
        />
        <BotParamField title="ドキュメント読み取りオプション" value={createBotParams.pdf_parser} />
        <BotParamField title="アプローチ" value={createBotParams.approach} />
        <BotParamField
          title="取得するチャンク数"
          value={
            createBotParams.approach_variables.find(variable => variable.name === "document_limit")
              ?.value || ""
          }
        />
        <BotParamField
          title="関連する質問の生成"
          value={createBotParams.enable_follow_up_questions ? "有効" : "無効"}
        />
        <BotParamField
          title="Web検索"
          value={createBotParams.enable_web_browsing ? "有効" : "無効"}
        />
      </Stack>
    </>
  );
};
