import { User } from "@auth0/auth0-react";
import { MenuItem, Stack, Typography } from "@mui/material";
import { useForm } from "react-hook-form";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomFormSelect } from "@/components/inputs/CustomFormSelect";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { CustomLabel } from "@/components/labels/CustomLabel";
import { Role } from "@/orval/models/backend-api";

export type UserInfoParam = {
  name: string;
  role: Role;
};

type Props = {
  user: User;
  onSubmit: (param: UserInfoParam) => void;
  onClose: () => void;
  canUpdateRole: boolean;
};

export const UpdateUserForm = ({ user, onSubmit, onClose, canUpdateRole }: Props) => {
  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<UserInfoParam>({
    defaultValues: {
      name: user.name,
      role: user.roles.includes("admin") ? "admin" : "user",
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <CustomDialogContent>
        <Stack direction="column" gap={2}>
          <Stack>
            <CustomLabel label="メールアドレス" />
            <Typography>{user.email}</Typography>
          </Stack>
          <CustomTextField
            name="name"
            label="ユーザー名"
            type="text"
            control={control}
            fullWidth
            rules={{ required: "ユーザー名は必須です" }}
          />
          {canUpdateRole && (
            <CustomFormSelect name="role" label="役割" control={control}>
              <MenuItem value="admin">組織管理者</MenuItem>
              <MenuItem value="user">一般ユーザー</MenuItem>
            </CustomFormSelect>
          )}
        </Stack>
      </CustomDialogContent>
      <CustomDialogAction onClose={onClose} buttonText="保存" loading={isSubmitting} />
    </form>
  );
};
