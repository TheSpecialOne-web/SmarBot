import { Container } from "@mui/material";
import { useParams } from "react-router-dom";

import { Breadcrumbs, BreadcrumbsItem } from "@/components/breadcrumbs/Breadcrumbs";
import { Spacer } from "@/components/spacers/Spacer";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useUserInfo } from "@/hooks/useUserInfo";
import { getErrorMessage } from "@/libs/error";
import { UpdateAssistantContents } from "@/modules/assistants/UpdateAssistantContents";
import { useGetBot } from "@/orval/backend-api";
import { Bot } from "@/orval/models/backend-api";

const getBreadcrumbsItems = ({
  bot,
  groupId,
}: {
  bot: Bot;
  groupId?: number;
}): BreadcrumbsItem[] => [
  {
    label: "アシスタント",
    href: groupId ? `#/main/groups/${groupId}/assistants` : `#/main/assistants`,
  },
  {
    label: bot.name,
    href: groupId ? `#/main/groups/${groupId}/assistants/${bot.id}` : `#/main/assistants/${bot.id}`,
  },
  {
    label: "編集",
  },
];

export const AssistantsEditPage = () => {
  const { enqueueErrorSnackbar } = useCustomSnackbar();

  const { userInfo } = useUserInfo();

  const params = useParams<{ assistantId: string; groupId: string }>();
  const assistantId = parseInt(params.assistantId || "");
  const groupId = params.groupId ? Number(params.groupId) : undefined;
  const { data: bot, error } = useGetBot(assistantId);
  if (error) {
    const errMsg = getErrorMessage(error);
    enqueueErrorSnackbar({ message: errMsg || "アシスタントの取得に失敗しました。" });
  }

  if (!bot) {
    return null;
  }

  return (
    <Container sx={{ pt: 2, pb: 4 }}>
      <Breadcrumbs items={getBreadcrumbsItems({ bot, groupId })} />
      <Spacer px={28} />
      <UpdateAssistantContents bot={bot} tenant={userInfo.tenant} groupId={groupId} />
    </Container>
  );
};
