import { Autocomplete, Box, Stack, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { useAsyncFn } from "react-use";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { CustomLabel } from "@/components/labels/CustomLabel";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { updateBotGroup } from "@/orval/backend-api";
import { BotWithGroup, Group } from "@/orval/models/backend-api";

type Props = {
  open: boolean;
  bot: BotWithGroup;
  groups: Group[];
  onClose: () => void;
  refetch: () => void;
};

export const UpdateBotGroupDialog = ({ open, onClose, bot, groups, refetch }: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const [selectedGroup, setSelectedGroup] = useState<Group | undefined>(
    groups.find(group => group.id === bot.group_id),
  );

  const [{ loading: isLoadingUpdateBotGroup }, handleUpdateBotGroup] = useAsyncFn(
    async ({ group }: { group: Group }) => {
      try {
        await updateBotGroup(bot.id, {
          group_id: group.id,
        });
        refetch();
        onClose();
        enqueueSuccessSnackbar({ message: "所属グループの変更に成功しました" });
      } catch (e) {
        enqueueErrorSnackbar({ message: getErrorMessage(e) || "所属グループの変更に失敗しました" });
      }
    },
  );

  return (
    <ConfirmDialog
      color="info"
      open={open}
      onClose={onClose}
      title="所属グループの変更"
      content={
        <Stack width="100%" gap={4}>
          <Typography>
            <Typography component="span" fontWeight={600}>
              {bot.name}
            </Typography>
            の所属グループを変更します。
          </Typography>
          <Stack width="100%" alignItems="flex-start" gap={1}>
            <Typography>
              現在の所属グループ:{" "}
              <Typography component="span" fontWeight={600}>
                {bot.group_name}
              </Typography>
            </Typography>
            <Box width="100%">
              <CustomLabel label="変更後の所属グループ" required />
              <Autocomplete<Group, false, true>
                options={groups}
                getOptionLabel={option => option.name}
                disableClearable
                fullWidth
                size="small"
                renderInput={params => <TextField {...params} size="small" />}
                value={selectedGroup}
                onChange={(_, value) => setSelectedGroup(value)}
              />
            </Box>
          </Stack>
        </Stack>
      }
      buttonText="保存"
      onSubmit={() => selectedGroup && handleUpdateBotGroup({ group: selectedGroup })}
      isLoading={isLoadingUpdateBotGroup}
      disabled={selectedGroup && selectedGroup.id === bot.group_id}
    />
  );
};
