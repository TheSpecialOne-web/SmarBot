import { Container } from "@mui/material";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { Breadcrumbs } from "@/components/breadcrumbs/Breadcrumbs";
import { Spacer } from "@/components/spacers/Spacer";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useUserInfo } from "@/hooks/useUserInfo";
import { getErrorMessage } from "@/libs/error";
import { getTextGenerationModelFamiliesFromAllowedModelFamilies } from "@/libs/model";
import { getIsTenantAdmin } from "@/libs/permission";
import { CreateAssistantForm } from "@/modules/assistants/CreateAssistantForm";
import { createBot, uploadBotIcon, useGetGroup, useGetGroups } from "@/orval/backend-api";
import { CreateBotParam } from "@/orval/models/backend-api";

const getBreadcrumbItems = (groupId?: number) => [
  {
    label: "アシスタント",
    href: groupId ? `#/main/groups/${groupId}/assistants` : "#/main/assistants",
  },
  { label: "新規作成" },
];

export const AssistantsCreatePage = () => {
  const [iconUrl, setIconUrl] = useState<string | null>(null);

  const navigate = useNavigate();
  const { enqueueSuccessSnackbar, enqueueErrorSnackbar } = useCustomSnackbar();
  const { userInfo, fetchUserInfo } = useUserInfo();

  const params = useParams<{ groupId: string }>();
  const paramGroupId = params.groupId ? Number(params.groupId) : undefined;

  const { data: groupsData, error: getGroupsError } = useGetGroups({
    swr: { enabled: !paramGroupId },
  });
  if (getGroupsError) {
    const errMsg = getErrorMessage(getGroupsError);
    enqueueErrorSnackbar({ message: errMsg || "グループの取得に失敗しました。" });
  }
  const groups = groupsData?.groups ?? [];

  const { data: defaultGroup, error: getDefaultGroupError } = useGetGroup(paramGroupId!, {
    swr: { enabled: Boolean(paramGroupId) },
  });
  if (getDefaultGroupError) {
    const errMsg = getErrorMessage(getDefaultGroupError);
    enqueueErrorSnackbar({ message: errMsg || "グループの取得に失敗しました。" });
  }

  const handleCreateBot = async ({
    createBotParam,
    groupId,
    icon,
  }: {
    createBotParam: CreateBotParam;
    groupId: number;
    icon: File | null;
  }) => {
    try {
      const paramsForCreate = {
        ...createBotParam,
        max_conversation_turns:
          createBotParam.max_conversation_turns === 0
            ? null
            : createBotParam.max_conversation_turns,
      };
      const newBot = await createBot(groupId, paramsForCreate);
      if (icon) {
        try {
          await uploadBotIcon(newBot.id, { file: icon });
        } catch (e) {
          const errMsg = getErrorMessage(e);
          enqueueErrorSnackbar({
            message: errMsg || "アシスタントのアイコンのアップロードに失敗しました。",
          });
          return;
        }
      }
      enqueueSuccessSnackbar({ message: "アシスタントを作成しました。" });
      if (!getIsTenantAdmin(userInfo)) {
        fetchUserInfo();
      }
      navigate(paramGroupId ? `/main/groups/${paramGroupId}/assistants` : "/main/assistants");
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({
        message: errMsg || "アシスタントの作成に失敗しました。",
      });
    }
  };

  const allowedTextGenerationModelFamilies = getTextGenerationModelFamiliesFromAllowedModelFamilies(
    userInfo.tenant.allowed_model_families,
  );

  return (
    <Container sx={{ pt: 2, pb: 4 }}>
      <Breadcrumbs items={getBreadcrumbItems(paramGroupId)} />

      <Spacer px={28} />

      {(paramGroupId && defaultGroup) || !paramGroupId ? (
        <CreateAssistantForm
          onSubmit={handleCreateBot}
          groups={groups}
          defaultGroup={defaultGroup}
          defaultModelFamily={allowedTextGenerationModelFamilies[0]}
          allowedModelFamilies={userInfo.tenant.allowed_model_families}
          enableDocumentIntelligence={userInfo.tenant.enable_document_intelligence}
          enableLLMDocumentReader={userInfo.tenant.enable_llm_document_reader}
          iconUrl={iconUrl}
          setIconUrl={setIconUrl}
        />
      ) : null}
    </Container>
  );
};
