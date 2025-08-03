import { Container, Grid, Skeleton, Stack, Typography } from "@mui/material";
import { useFlags } from "launchdarkly-react-client-sdk";
import { useState } from "react";
import { useParams } from "react-router-dom";

import { Breadcrumbs } from "@/components/breadcrumbs/Breadcrumbs";
import { Spacer } from "@/components/spacers/Spacer";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { useUserInfo } from "@/hooks/useUserInfo";
import { getErrorMessage } from "@/libs/error";
import { AssistantTemplateCard } from "@/modules/assistants/AssistantTemplateCard";
import { CreateAssistantFromTemplateDialog } from "@/modules/assistants/CreateAssistantFromTemplateDialog";
import { useGetBotTemplates, useGetGroup, useGetGroups } from "@/orval/backend-api";
import { BotTemplate } from "@/orval/models/backend-api";

const getBreadcrumbItems = (groupId?: number) => [
  {
    label: "アシスタント",
    href: groupId ? `#/main/groups/${groupId}/assistants` : "#/main/assistants",
  },
  { label: "テンプレートから作成" },
];

export const CreateAssistantFromTemplatesPage = () => {
  const { useAssistantTemplate } = useFlags();
  const { userInfo } = useUserInfo();
  const { enqueueErrorSnackbar } = useCustomSnackbar();

  const params = useParams<{ groupId: string }>();
  const groupId = params.groupId ? Number(params.groupId) : undefined;

  const { data: groupsData, error: getGroupsError } = useGetGroups({
    swr: { enabled: !groupId },
  });
  if (getGroupsError) {
    const errMsg = getErrorMessage(getGroupsError);
    enqueueErrorSnackbar({ message: errMsg || "グループの取得に失敗しました。" });
  }
  const groups = groupsData?.groups ?? [];

  const { data: defaultGroup, error: getDefaultGroupError } = useGetGroup(groupId!, {
    swr: { enabled: Boolean(groupId) },
  });
  if (getDefaultGroupError) {
    const errMsg = getErrorMessage(getDefaultGroupError);
    enqueueErrorSnackbar({ message: errMsg || "グループの取得に失敗しました。" });
  }

  const { data, isValidating: isLoadingGetBotTemplates } = useGetBotTemplates({
    swr: { enabled: useAssistantTemplate },
  });
  const templates = data?.bot_templates || [];

  const { isOpen, open, close } = useDisclosure({});
  const [selectedBotTemplate, setSelectedBotTemplate] = useState<BotTemplate>();

  const handleSelectBotTemplate = (botTemplate: BotTemplate) => {
    setSelectedBotTemplate(botTemplate);
    open();
  };

  if (!useAssistantTemplate) {
    return null;
  }

  return (
    <>
      <Container
        sx={{
          pt: 2,
          pb: 4,
        }}
      >
        <Breadcrumbs items={getBreadcrumbItems(groupId)} />

        <Spacer px={28} />
        <Typography variant="h3" mb={2}>
          アシスタントテンプレート
        </Typography>
        {isLoadingGetBotTemplates ? (
          <Grid container spacing={3}>
            {Array.from({ length: 6 }).map((_, index) => (
              <Grid item xs={12} md={6} lg={4} key={index}>
                <Skeleton height={150} />
              </Grid>
            ))}
          </Grid>
        ) : templates.length === 0 ? (
          <>
            <Spacer px={256} />
            <Stack direction="row" justifyContent="center">
              <Typography>利用可能なテンプレートがありません。</Typography>
            </Stack>
          </>
        ) : (
          <Grid container spacing={3}>
            {templates.map((template, index) => (
              <Grid item xs={12} md={6} lg={4} key={index}>
                <AssistantTemplateCard
                  botTemplate={template}
                  handleSelectBotTemplate={() => handleSelectBotTemplate(template)}
                />
              </Grid>
            ))}
          </Grid>
        )}
      </Container>
      {selectedBotTemplate && (
        <CreateAssistantFromTemplateDialog
          groups={groups}
          defaultGroup={defaultGroup}
          open={isOpen}
          onClose={close}
          tenant={userInfo.tenant}
          botTemplate={selectedBotTemplate}
        />
      )}
    </>
  );
};
