import { Container } from "@mui/material";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { ContentHeader } from "@/components/headers/ContentHeader";
import { CustomTableSkeleton } from "@/components/loadings/TableSkeletonLoading";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { useUserInfo } from "@/hooks/useUserInfo";
import { isAssistant } from "@/libs/bot";
import { getErrorMessage } from "@/libs/error";
import { getIsTenantAdmin } from "@/libs/permission";
import { ArchiveAssistantDialog } from "@/modules/assistants/ArchiveAssistantDialog";
import { AssistantsTableHeader } from "@/modules/assistants/AssistantsTableHeader";
import { AssistantsWithGroupTable } from "@/modules/assistants/AssistantsWithGroupTable";
import { UpdateBotGroupDialog } from "@/modules/assistants/UpdateBotGroupDialog";
import { useGetBots, useGetGroups } from "@/orval/backend-api";
import { BotStatus, BotWithGroup } from "@/orval/models/backend-api";

export const AssistantsPage = () => {
  const { enqueueErrorSnackbar } = useCustomSnackbar();

  const { userInfo } = useUserInfo();
  const isTenantAdmin = getIsTenantAdmin(userInfo);

  const {
    data: botsData,
    error: getBotsError,
    mutate: fetchBots,
    isValidating: isLoadingGetBots,
  } = useGetBots({ status: [BotStatus.active] });
  if (getBotsError) {
    const errMsg = getErrorMessage(getBotsError);
    enqueueErrorSnackbar({ message: errMsg || "アシスタントの取得に失敗しました。" });
  }
  const assistants = botsData?.bots?.filter(bot => isAssistant(bot)) ?? [];

  const {
    data: groupsData,
    error: getGroupsError,
    mutate: fetchGroups,
  } = useGetGroups({ swr: { enabled: isTenantAdmin } });
  if (getGroupsError) {
    const errMsg = getErrorMessage(getGroupsError);
    enqueueErrorSnackbar({ message: errMsg || "グループの取得に失敗しました。" });
  }
  const groups = groupsData?.groups ?? [];

  const navigate = useNavigate();
  const handleStartChat = (bot: BotWithGroup) => {
    navigate(`/main/chat?botId=${bot.id}`);
  };

  const [botToArchive, setBotToArchive] = useState<BotWithGroup | null>(null);
  const [botToUpdateBotGroup, setBotToUpdateBotGroup] = useState<BotWithGroup | null>(null);

  const {
    isOpen: isOpenArchiveAssistantDialog,
    open: openArchiveAssistantDialog,
    close: closeArchiveAssistantDialog,
  } = useDisclosure({
    onClose: () => setBotToArchive(null),
  });

  const {
    isOpen: isOpenUpdateBotGroupDialog,
    open: openUpdateBotGroupDialog,
    close: closeUpdateBotGroupDialog,
  } = useDisclosure({
    onClose: () => setBotToUpdateBotGroup(null),
  });

  const handleOpenArchiveAssistantDialog = (bot: BotWithGroup) => {
    setBotToArchive(bot);
    openArchiveAssistantDialog();
  };

  const handleOpenChangeBotGroupDialog = (bot: BotWithGroup) => {
    setBotToUpdateBotGroup(bot);
    openUpdateBotGroupDialog();
  };

  const refetch = () => {
    fetchBots();
    fetchGroups();
  };

  if (isLoadingGetBots) {
    return (
      <Container sx={{ py: 4 }}>
        <CustomTableSkeleton />
      </Container>
    );
  }

  return (
    <Container sx={{ py: 4 }}>
      <ContentHeader>
        <AssistantsTableHeader refetch={refetch} />
      </ContentHeader>
      <AssistantsWithGroupTable
        bots={assistants}
        onClickStartChat={handleStartChat}
        onClickArchive={handleOpenArchiveAssistantDialog}
        onClickUpdateBotGroup={handleOpenChangeBotGroupDialog}
        isTenantAdmin={isTenantAdmin}
      />

      {botToArchive && (
        <ArchiveAssistantDialog
          open={isOpenArchiveAssistantDialog}
          onClose={closeArchiveAssistantDialog}
          bot={botToArchive}
          refetch={refetch}
        />
      )}

      {botToUpdateBotGroup && (
        <UpdateBotGroupDialog
          open={isOpenUpdateBotGroupDialog}
          onClose={closeUpdateBotGroupDialog}
          bot={botToUpdateBotGroup}
          groups={groups}
          refetch={refetch}
        />
      )}
    </Container>
  );
};
