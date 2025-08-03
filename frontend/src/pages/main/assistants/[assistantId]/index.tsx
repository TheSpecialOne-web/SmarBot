import QuestionAnswerIcon from "@mui/icons-material/QuestionAnswer";
import { Box, Container, Stack, Tab, Tabs } from "@mui/material";
import { useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

import { Breadcrumbs, BreadcrumbsItem } from "@/components/breadcrumbs/Breadcrumbs";
import { FloatIconButton } from "@/components/buttons/FloatIconButton";
import { CustomTableSkeleton } from "@/components/loadings/TableSkeletonLoading";
import { Spacer } from "@/components/spacers/Spacer";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useUserInfo } from "@/hooks/useUserInfo";
import { getErrorMessage } from "@/libs/error";
import { getHasWritePolicy } from "@/libs/policy";
import { AssistantOverview } from "@/modules/assistants/AssistantOverview";
import { DocumentManagement } from "@/modules/assistants/DocumentManagement";
import { PromptTemplateManagement } from "@/modules/assistants/PromptTemplateManagement";
import { QuestionAnswerManagement } from "@/modules/assistants/QuestionAnswerManagement";
import { TermManagement } from "@/modules/assistants/TermManagement";
import { useGetBot } from "@/orval/backend-api";
import { Approach, BotStatus } from "@/orval/models/backend-api";

const TAB_KEYS = ["overview", "document", "term", "prompt_template", "question_answer"] as const;
type TabKey = (typeof TAB_KEYS)[number];

const getBreadcrumbsItems = ({
  botName,
  isArchived,
  groupId,
}: {
  botName: string;
  isArchived: boolean;
  groupId?: number;
}): BreadcrumbsItem[] => [
  {
    label: isArchived ? "アーカイブ済みアシスタント" : "アシスタント",
    href: isArchived
      ? groupId
        ? `#/main/groups/${groupId}/assistants/archived`
        : "#/main/assistants/archived"
      : groupId
      ? `#/main/groups/${groupId}/assistants`
      : "#/main/assistants",
  },
  {
    label: botName,
  },
];

const getValidTabKeyFromQuery = (queryParam: string | null): TabKey => {
  if (queryParam && TAB_KEYS.includes(queryParam as TabKey)) {
    return queryParam as TabKey;
  }
  return "overview";
};

export const AssistantDetailPage = () => {
  const { userInfo } = useUserInfo();
  const params = useParams<{ assistantId: string; groupId: string }>();
  const [searchParams] = useSearchParams();
  const { enqueueErrorSnackbar } = useCustomSnackbar();
  const navigate = useNavigate();

  const assistantId = Number(params.assistantId);
  const groupId = params.groupId ? Number(params.groupId) : undefined;

  const {
    data: botData,
    error: getBotError,
    isValidating: isGetBotValidating,
    mutate: refetchBot,
  } = useGetBot(assistantId, { swr: { enabled: !Number.isNaN(assistantId) } });
  if (getBotError) {
    const errMsg = getErrorMessage(getBotError);
    enqueueErrorSnackbar({ message: errMsg || "アシスタントの取得に失敗しました。" });
  }

  const botName = botData?.name ?? "";

  const tabKeyQueryParam = searchParams.get("tabKey");
  const defaultTabKey = getValidTabKeyFromQuery(tabKeyQueryParam);
  const [tabKey, setTabKey] = useState<TabKey>(defaultTabKey);

  const handleChangeTab = (_: unknown, newTabKey: TabKey) => {
    setTabKey(newTabKey);
    navigate(`?tabKey=${newTabKey}`);
  };
  if (isGetBotValidating || !botData) {
    return (
      <Container sx={{ py: 4 }}>
        <CustomTableSkeleton />
      </Container>
    );
  }

  const hasWritePolicy = getHasWritePolicy(botData, userInfo);

  const onClickStartChat = () => {
    navigate(`/main/chat?botId=${assistantId}`);
  };

  return (
    <Container sx={{ pt: 2, pb: 12 }}>
      <Stack direction="row" gap={1.5} alignItems={"center"}>
        <Breadcrumbs
          items={getBreadcrumbsItems({
            botName,
            isArchived: botData.status === BotStatus.archived,
            groupId,
          })}
        />
        {botData.status === BotStatus.active && (
          <FloatIconButton
            icon={
              <QuestionAnswerIcon
                sx={{
                  color: "primary.main",
                  fontSize: "16px",
                }}
              />
            }
            tooltipTitle={"チャットを始める"}
            onClick={onClickStartChat}
          />
        )}
      </Stack>

      <Spacer px={14} />

      <Tabs value={tabKey} onChange={handleChangeTab}>
        <Tab value="overview" label="概要" sx={{ fontWeight: "bold" }} />
        {botData && botData.approach !== Approach.custom_gpt && (
          <Tab value="document" label="ドキュメント" sx={{ fontWeight: "bold" }} />
        )}
        {botData.approach !== Approach.custom_gpt && (
          <Tab value="question_answer" label="FAQ" sx={{ fontWeight: "bold" }} />
        )}
        {botData && botData.approach !== Approach.custom_gpt && (
          <Tab value="term" label="用語集" sx={{ fontWeight: "bold" }} />
        )}
        {botData && <Tab value="prompt_template" label="質問例" sx={{ fontWeight: "bold" }} />}
      </Tabs>

      <Spacer px={14} />

      <Box>
        {tabKey === "overview" && (
          <AssistantOverview
            selectedBot={botData}
            isLoadingSelectBot={isGetBotValidating}
            isEditButtonVisible={hasWritePolicy}
            refetch={refetchBot}
            enableDocumentIntelligence={userInfo.tenant.enable_document_intelligence}
          />
        )}
        {tabKey === "document" && (
          <DocumentManagement selectedBot={botData} hasWritePolicy={hasWritePolicy} />
        )}
        {tabKey === "prompt_template" && (
          <PromptTemplateManagement bot={botData} hasWritePolicy={hasWritePolicy} />
        )}
        {tabKey === "term" && (
          <TermManagement selectedBot={botData} hasWritePolicy={hasWritePolicy} />
        )}
        {tabKey === "question_answer" && (
          <QuestionAnswerManagement botId={botData.id} hasWritePolicy={hasWritePolicy} />
        )}
      </Box>
    </Container>
  );
};
