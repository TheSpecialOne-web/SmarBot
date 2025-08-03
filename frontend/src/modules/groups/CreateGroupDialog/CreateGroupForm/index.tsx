import { Autocomplete, TextField } from "@mui/material";
import { Controller, useForm } from "react-hook-form";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { CustomLabel } from "@/components/labels/CustomLabel";
import { Spacer } from "@/components/spacers/Spacer";
import { CreateGroupParam, User } from "@/orval/models/backend-api";

type Props = {
  users: User[];
  onSubmit: (params: CreateGroupParam) => void;
  onClose: () => void;
};

export const CreateGroupForm = ({ users, onSubmit, onClose }: Props) => {
  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<CreateGroupParam>();

  const getOptionLabel = (userId: number) => {
    const user = users.find(user => user.id === userId);
    if (!user) return "";

    return `${user.name} (${user.email})`;
  };

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)}>
      <CustomDialogContent>
        <CustomTextField
          control={control}
          rules={{ required: "グループ名は必須です" }}
          label="グループ名"
          autoFocus
          fullWidth
          name="name"
          type="text"
        />
        <Spacer px={8} />

        <CustomLabel label="グループ管理者" required />
        <Controller
          name="group_admin_user_id"
          control={control}
          render={({ field: { onChange, value } }) => (
            <Autocomplete<User["id"], false, true>
              options={users.map(({ id }) => id)}
              getOptionLabel={getOptionLabel}
              disableClearable
              fullWidth
              size="small"
              renderInput={params => <TextField {...params} size="small" />}
              value={value}
              onChange={(_, data) => onChange(data)}
            />
          )}
        />
      </CustomDialogContent>
      <CustomDialogAction onClose={onClose} buttonText="作成" loading={isSubmitting} />
    </form>
  );
};
