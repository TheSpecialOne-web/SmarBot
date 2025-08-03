import { Box, MenuItem, Select, Stack, Typography } from "@mui/material";
import { useState } from "react";

import { ConfirmDialog } from "@/components/dialogs/ConfirmDialog";
import { CustomLabel } from "@/components/labels/CustomLabel";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { groupRoleToJapanese } from "@/libs/group";
import { useUpdateUserGroupRole } from "@/orval/backend-api";
import { GroupRole, GroupUser } from "@/orval/models/backend-api";

type Props = {
  open: boolean;
  groupId: number;
  groupUser: GroupUser;
  onClose: () => void;
  refetch: () => void;
};

export const UpdateUserGroupRoleDialog = ({
  open,
  groupId,
  groupUser,
  onClose,
  refetch,
}: Props) => {
  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();
  const { trigger, isMutating } = useUpdateUserGroupRole(groupId, groupUser.id);

  const [groupRole, setGroupRole] = useState<GroupRole>(groupUser.group_role);

  const updateRole = async () => {
    try {
      await trigger({ role: groupRole });
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "権限を変更しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "権限の変更に失敗しました。" });
    }
  };

  return (
    <ConfirmDialog
      open={open}
      color="info"
      onClose={onClose}
      title="グループ権限の変更"
      content={
        <Stack width="100%" gap={4}>
          <Typography>
            <Typography component="span" fontWeight={600}>
              {groupUser.name}
            </Typography>
            のグループ権限を変更します。
          </Typography>
          <Stack width="100%" alignItems="flex-start" gap={1}>
            <Typography>
              現在のグループ権限:{" "}
              <Typography component="span" fontWeight={600}>
                {groupRoleToJapanese(groupUser.group_role)}
              </Typography>
            </Typography>
            <Box width="100%">
              <CustomLabel label="グループ権限" required />
              <Select
                value={groupRole}
                onChange={e => setGroupRole(e.target.value as GroupRole)}
                size="small"
                fullWidth
                sx={{
                  textAlign: "left",
                }}
              >
                {Object.values(GroupRole).map(groupRole => (
                  <MenuItem key={groupRole} value={groupRole}>
                    {groupRoleToJapanese(groupRole)}
                  </MenuItem>
                ))}
              </Select>
            </Box>
          </Stack>
        </Stack>
      }
      buttonText="保存"
      onSubmit={updateRole}
      isLoading={isMutating}
    />
  );
};
