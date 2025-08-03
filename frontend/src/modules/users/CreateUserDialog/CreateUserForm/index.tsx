import { Stack } from "@mui/material";
import { useForm } from "react-hook-form";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { CreateUserParam } from "@/orval/models/backend-api";

type Props = {
  onSubmit: (params: CreateUserParam) => void;
  onClose: () => void;
};

export const CreateUserForm = ({ onSubmit, onClose }: Props) => {
  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<CreateUserParam>();

  return (
    <form noValidate onSubmit={handleSubmit(onSubmit)}>
      <CustomDialogContent>
        <Stack gap={2}>
          <CustomTextField
            name="name"
            label="ユーザー名"
            rules={{
              required: "ユーザー名は必須項目です。",
            }}
            control={control}
            autoFocus
            fullWidth
            type="text"
          />

          <CustomTextField
            rules={{
              required: "メールアドレスは必須項目です。",
              pattern: {
                value: /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]{2,}$/,
                message: "メールアドレスの形式が正しくありません",
              },
            }}
            control={control}
            fullWidth
            placeholder="neoaichat@example.com"
            name="email"
            label="メールアドレス"
            type="email"
          />
        </Stack>
      </CustomDialogContent>
      <CustomDialogAction onClose={onClose} loading={isSubmitting} buttonText="作成" />
    </form>
  );
};
