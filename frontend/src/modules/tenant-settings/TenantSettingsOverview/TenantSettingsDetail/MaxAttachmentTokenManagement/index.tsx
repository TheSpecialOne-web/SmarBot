import { Skeleton, Stack, Typography } from "@mui/material";
import { useEffect } from "react";
import { useForm } from "react-hook-form";

import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useUpdateTenantMaxAttachmentToken } from "@/orval/backend-api";
import { Tenant, UpdateTenantMaxAttachmentTokenParam } from "@/orval/models/backend-api";

type Props = {
  tenant: Tenant;
  refetch: () => void;
  isLoadingGetTenant: boolean;
};

const GPT_MAX_ATTACHMENT_TOKEN = 100000;

export const MaxAttachmentTokenManagement = ({ tenant, refetch, isLoadingGetTenant }: Props) => {
  const { trigger: updateTenantMaxAttachmentToken } = useUpdateTenantMaxAttachmentToken(tenant.id);

  const { enqueueErrorSnackbar, enqueueSuccessSnackbar } = useCustomSnackbar();

  const {
    handleSubmit,
    control,
    formState: { isSubmitting },
    reset,
  } = useForm<UpdateTenantMaxAttachmentTokenParam>({
    defaultValues: {
      max_attachment_token: tenant.max_attachment_token,
    },
  });

  const handleUpdate = async ({ max_attachment_token }: UpdateTenantMaxAttachmentTokenParam) => {
    if (isNaN(max_attachment_token)) {
      enqueueErrorSnackbar({ message: "有効な数値を入力してください。" });
      return;
    }

    try {
      await updateTenantMaxAttachmentToken({ max_attachment_token });
      refetch();
      enqueueSuccessSnackbar({ message: "ファイル添付機能の最大トークン数を更新しました" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({
        message: errMsg || "ファイル添付機能の最大トークン数の更新に失敗しました。",
      });
    }
  };

  useEffect(() => {
    reset({ max_attachment_token: tenant.max_attachment_token });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenant]);

  return (
    <Stack spacing={2}>
      <Stack spacing={1}>
        <Typography variant="h5">ファイル添付機能の使用時に与える最大トークン数</Typography>
        <Typography variant="subtitle2">
          ファイル添付機能を使用する際の最大トークン数を設定します。
          <br />
          最大トークン数は全ての基盤モデル、アシスタントに適用されます。最大で
          {GPT_MAX_ATTACHMENT_TOKEN.toLocaleString()}トークンまで設定可能です。
        </Typography>
      </Stack>
      <form onSubmit={handleSubmit(handleUpdate)}>
        <Stack direction="row" alignItems="center" width="100%" spacing={2}>
          {isLoadingGetTenant ? (
            <Skeleton variant="rectangular" height={36} sx={{ flex: 1 }} />
          ) : (
            <CustomTextField
              name="max_attachment_token"
              control={control}
              type="number"
              rules={{
                required: "必須項目です。",
                min: {
                  value: 0,
                  message: "0以上の数値を入力してください。",
                },
                max: {
                  value: GPT_MAX_ATTACHMENT_TOKEN,
                  message: `${GPT_MAX_ATTACHMENT_TOKEN}以下の数値を入力してください。`,
                },
              }}
              fullWidth
              boxSx={{ flex: 1 }}
            />
          )}
          <PrimaryButton
            text="保存"
            type="submit"
            disabled={isSubmitting || isLoadingGetTenant}
            loading={isSubmitting}
          />
        </Stack>
      </form>
    </Stack>
  );
};
