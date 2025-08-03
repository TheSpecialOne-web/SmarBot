import { Box, MenuItem, Stack, Switch, Typography } from "@mui/material";
import { Controller, useForm } from "react-hook-form";

import { CustomDialog } from "@/components/dialogs/CustomDialog";
import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomFormSelect } from "@/components/inputs/CustomFormSelect";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { CustomLabel } from "@/components/labels/CustomLabel";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { displayAdditionalPlatform } from "@/libs/administrator/platform";
import { getPdfParserLabel } from "@/libs/bot";
import { getErrorMessage } from "@/libs/error";
import { useCreateTenant } from "@/orval/administrator-api";
import { AdditionalPlatform, CreateTenantParam } from "@/orval/models/administrator-api";
import { PdfParser } from "@/orval/models/backend-api";

type Props = {
  open: boolean;
  onClose: () => void;
  refetch: () => void;
};

export const CreateTenantDialog = ({ open, onClose, refetch }: Props) => {
  const { enqueueSuccessSnackbar, enqueueErrorSnackbar } = useCustomSnackbar();
  const { trigger: createTenant } = useCreateTenant();

  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<CreateTenantParam>({
    defaultValues: {
      name: "",
      alias: "",
      admin_name: "",
      admin_email: "",
      enable_document_intelligence: true,
      allow_foreign_region: true,
      additional_platforms: [AdditionalPlatform.gcp],
    },
  });

  const onSubmit = async ({
    name,
    alias,
    admin_name,
    admin_email,
    enable_document_intelligence,
    allow_foreign_region,
    additional_platforms,
  }: CreateTenantParam) => {
    try {
      await createTenant({
        name,
        alias,
        admin_name,
        admin_email,
        enable_document_intelligence,
        allow_foreign_region,
        additional_platforms,
      });
      refetch();
      onClose();
      enqueueSuccessSnackbar({ message: "テナントを作成しました。" });
    } catch (e) {
      const errMsg = getErrorMessage(e);
      enqueueErrorSnackbar({ message: errMsg || "不明なエラーが発生しました。" });
    }
  };

  return (
    <CustomDialog open={open} title="テナント作成" onClose={onClose}>
      <form noValidate onSubmit={handleSubmit(onSubmit)}>
        <CustomDialogContent>
          <Stack gap={2} direction="column">
            <CustomTextField
              label="テナント名"
              autoFocus
              rules={{
                required: "テナント名は必須項目です。",
              }}
              fullWidth
              control={control}
              name="name"
              type="text"
            />
            <CustomTextField
              label="エイリアス"
              rules={{
                required: "エイリアスは必須項目です。",
              }}
              fullWidth
              control={control}
              name="alias"
              type="text"
            />
            <CustomTextField
              control={control}
              rules={{
                required: "組織管理者名は必須項目です。",
              }}
              label="組織管理者名"
              fullWidth
              name="admin_name"
              type="text"
            />

            <CustomTextField
              label="メールアドレス"
              control={control}
              fullWidth
              rules={{
                required: "メールアドレスは必須項目です。",
                pattern: {
                  value: /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]{2,}$/,
                  message: "メールアドレスの形式が正しくありません",
                },
              }}
              placeholder="neoaichat@example.com"
              name="admin_email"
              type="email"
            />
            <Box>
              <CustomLabel label={getPdfParserLabel(PdfParser.document_intelligence)} required />
              <Stack direction="row" alignItems="center" gap={2}>
                <Typography variant="body2">
                  {getPdfParserLabel(PdfParser.document_intelligence)}をオンにする
                </Typography>
                <Controller
                  name="enable_document_intelligence"
                  control={control}
                  render={({ field }) => (
                    <Switch
                      checked={field.value}
                      onChange={e => {
                        field.onChange(e.target.checked);
                      }}
                    />
                  )}
                />
              </Stack>
            </Box>
            <Box>
              <CustomLabel label="海外リージョンの利用" required />
              <Stack direction="row" alignItems="center" gap={2}>
                <Typography variant="body2">海外リージョンの利用を許可する</Typography>
                <Controller
                  name="allow_foreign_region"
                  control={control}
                  render={({ field }) => (
                    <Switch
                      checked={field.value}
                      onChange={e => {
                        field.onChange(e.target.checked);
                      }}
                    />
                  )}
                />
              </Stack>
            </Box>
            <Box>
              <CustomFormSelect<CreateTenantParam>
                name="additional_platforms"
                label="追加のプラットフォーム"
                control={control}
                multiple
              >
                {Object.entries(AdditionalPlatform).map(([key, value]) => (
                  <MenuItem key={key} value={value}>
                    {displayAdditionalPlatform(value)}
                  </MenuItem>
                ))}
              </CustomFormSelect>
            </Box>
          </Stack>
        </CustomDialogContent>
        <CustomDialogAction onClose={onClose} loading={isSubmitting} buttonText="作成" />
      </form>
    </CustomDialog>
  );
};
