import { Container, Stack, Typography } from "@mui/material";
import { useState } from "react";

import { Breadcrumbs } from "@/components/breadcrumbs/Breadcrumbs";
import { RefreshButton } from "@/components/buttons/RefreshButton";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { CustomTableSkeleton } from "@/components/loadings/TableSkeletonLoading";
import { Spacer } from "@/components/spacers/Spacer";
import { useDisclosure } from "@/hooks/useDisclosure";
import { isAssistant } from "@/libs/bot";
import { ArchivedAssistantsWithGroupTable } from "@/modules/assistants/ArchivedAssistantsWithGroupTable";
import { DeleteAssistantDialog } from "@/modules/assistants/DeleteAssistantDialog";
import { RestoreAssistantDialog } from "@/modules/assistants/RestoreAssistantDialog";
import { useGetBots } from "@/orval/backend-api";
import { Bot, BotStatus } from "@/orval/models/backend-api";

const breadcrumbsItems = [
  {
    label: "アシスタント",
    href: "#/main/assistants",
  },
  {
    label: "アーカイブ済みアシスタント",
  },
];

export const ArchivedAssistantsPage = () => {
  const {
    data,
    mutate: fetchBots,
    isValidating: isLoadingGetBots,
  } = useGetBots({
    status: [BotStatus.archived, BotStatus.deleting],
  });

  const assistants = data?.bots?.filter(bot => isAssistant(bot)) ?? [];

  const [assistantToRestore, setAssistantToRestore] = useState<Bot | null>(null);
  const [assistantToDelete, setAssistantToDelete] = useState<Bot | null>(null);

  const {
    isOpen: restoreAssistantDialogOpen,
    open: openRestoreAssistantDialog,
    close: closeRestoreAssistantDialog,
  } = useDisclosure({});
  const {
    isOpen: deleteAssistantDialogOpen,
    open: openDeleteAssistantDialog,
    close: closeDeleteAssistantDialog,
  } = useDisclosure({});

  const handleOpenRestoreAssistantDialog = (bot: Bot) => {
    setAssistantToRestore(bot);
    openRestoreAssistantDialog();
  };
  const handleOpenDeleteAssistantDialog = (bot: Bot) => {
    setAssistantToDelete(bot);
    openDeleteAssistantDialog();
  };

  return (
    <Container sx={{ py: 4 }}>
      <Breadcrumbs items={breadcrumbsItems} />

      <Spacer px={16} />

      {isLoadingGetBots ? (
        <CustomTableSkeleton />
      ) : (
        <>
          <ContentHeader>
            <Stack direction="row" alignItems="center">
              <Typography variant="h4" sx={{ flexGrow: 1 }}>
                アーカイブ済みアシスタント
              </Typography>
              <RefreshButton onClick={fetchBots} />
            </Stack>
          </ContentHeader>
          <ArchivedAssistantsWithGroupTable
            bots={assistants}
            onClickRestore={handleOpenRestoreAssistantDialog}
            onClickDelete={handleOpenDeleteAssistantDialog}
          />
        </>
      )}
      {assistantToRestore && (
        <RestoreAssistantDialog
          open={restoreAssistantDialogOpen}
          onClose={closeRestoreAssistantDialog}
          bot={assistantToRestore}
          refetch={fetchBots}
        />
      )}
      {assistantToDelete && (
        <DeleteAssistantDialog
          open={deleteAssistantDialogOpen}
          onClose={closeDeleteAssistantDialog}
          bot={assistantToDelete}
          refetch={fetchBots}
        />
      )}
    </Container>
  );
};
