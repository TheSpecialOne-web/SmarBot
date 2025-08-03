import AddOutlinedIcon from "@mui/icons-material/AddOutlined";
import AutoStoriesOutlinedIcon from "@mui/icons-material/AutoStoriesOutlined";
import { Stack, Typography } from "@mui/material";
import { useState } from "react";

import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { RefreshButton } from "@/components/buttons/RefreshButton";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { CustomTableSkeleton } from "@/components/loadings/TableSkeletonLoading";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { useDisclosure } from "@/hooks/useDisclosure";
import { getErrorMessage } from "@/libs/error";
import { useGetBots, useGetTenantGroups } from "@/orval/administrator-api";
import { Bot, Tenant } from "@/orval/models/administrator-api";

import { BotsTable } from "../BotsTable";
import { CreateBotDialog } from "../CreateBotDialog";
import { CreateBotFromTemplateDialog } from "../CreateBotFromTemplateDialog";
import { DeleteBotDialog } from "../DeleteBotDialog";
import { UpdateBotDialog } from "../UpdateBotDialog";

type Props = {
  tenant: Tenant;
};

export const BotsManagement = ({ tenant }: Props) => {
  const { enqueueErrorSnackbar } = useCustomSnackbar();
  const [botToUpdate, setBotToUPdate] = useState<Bot | null>();
  const [botToDelete, setBotToDelete] = useState<Bot>();

  const {
    data: botsData,
    error: botsError,
    isValidating: isLoadingBots,
    mutate: refetchBots,
  } = useGetBots(tenant.id);
  if (botsError) {
    const errMsg = getErrorMessage(botsError);
    enqueueErrorSnackbar({ message: errMsg || "ボットの取得に失敗しました。" });
  }
  const bots = botsData?.bots ?? [];

  const {
    data: groupsData,
    error: getGroupsError,
    mutate: refetchGroups,
    isValidating: isLoadingGroups,
  } = useGetTenantGroups(tenant.id);
  if (getGroupsError) {
    const errMsg = getErrorMessage(getGroupsError);
    enqueueErrorSnackbar({ message: errMsg || "グループの取得に失敗しました。" });
  }
  const groups = groupsData?.groups ?? [];

  const {
    isOpen: isOpenCreateBotDialog,
    open: openCreateBotDialog,
    close: closeCreateBotDialog,
  } = useDisclosure({});

  const {
    isOpen: isOpenDeleteBotDialog,
    open: openDeleteBotDialog,
    close: closeDeleteBotDialog,
  } = useDisclosure({});

  const {
    isOpen: isOpenCreateBotFromTemplateDialog,
    open: openCreateBotFromTemplateDialog,
    close: closeCreateBotFromTemplateDialog,
  } = useDisclosure({});

  const {
    isOpen: isOpenUpdateBotDialog,
    open: openUpdateBotDialog,
    close: closeUpdateBotDialog,
  } = useDisclosure({
    onClose: () => {
      setBotToUPdate(null);
    },
  });

  const handleOpenDeleteBotDialog = (bot: Bot) => {
    setBotToDelete(bot);
    openDeleteBotDialog();
  };

  const handleOpenUpdateBotDialog = (bot: Bot) => {
    setBotToUPdate(bot);
    openUpdateBotDialog();
  };

  const refetch = () => {
    refetchBots();
    refetchGroups();
  };

  const isLoading = isLoadingBots || isLoadingGroups;

  return (
    <>
      <ContentHeader>
        <Stack direction="row" justifyContent="space-between">
          <Typography variant="h4" sx={{ flexGrow: 1 }}>
            ボット
          </Typography>
          <Stack direction="row" gap={2}>
            <RefreshButton onClick={refetch} />
            <PrimaryButton
              text={<Typography variant="button">テンプレートから作成</Typography>}
              startIcon={<AutoStoriesOutlinedIcon />}
              onClick={openCreateBotFromTemplateDialog}
            />
            <PrimaryButton
              text={<Typography variant="button">新規作成</Typography>}
              startIcon={<AddOutlinedIcon />}
              onClick={openCreateBotDialog}
            />
          </Stack>
        </Stack>
      </ContentHeader>
      {isLoading ? (
        <CustomTableSkeleton />
      ) : (
        <BotsTable
          bots={bots}
          onClickUpdateIcon={handleOpenUpdateBotDialog}
          onClickDeleteIcon={handleOpenDeleteBotDialog}
        />
      )}

      <CreateBotDialog
        open={isOpenCreateBotDialog}
        onClose={closeCreateBotDialog}
        refetch={refetch}
        tenant={tenant}
        groups={groups}
      />

      <CreateBotFromTemplateDialog
        open={isOpenCreateBotFromTemplateDialog}
        onClose={closeCreateBotFromTemplateDialog}
        refetch={refetch}
        tenant={tenant}
        groups={groups}
      />

      {botToUpdate && (
        <UpdateBotDialog
          open={isOpenUpdateBotDialog}
          tenant={tenant}
          bot={botToUpdate}
          onClose={closeUpdateBotDialog}
          refetch={refetch}
        />
      )}

      {botToDelete && (
        <DeleteBotDialog
          open={isOpenDeleteBotDialog}
          tenant={tenant}
          bot={botToDelete}
          onClose={closeDeleteBotDialog}
          refetch={refetch}
        />
      )}
    </>
  );
};
