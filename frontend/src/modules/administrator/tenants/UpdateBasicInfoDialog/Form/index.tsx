import AddIcon from "@mui/icons-material/Add";
import { Box, Button, MenuItem, Stack, Switch, TextField, Typography } from "@mui/material";
import { Controller, useForm } from "react-hook-form";

import { CustomDialogAction } from "@/components/dialogs/CustomDialog/CustomDialogAction";
import { CustomDialogContent } from "@/components/dialogs/CustomDialog/CustomDialogContent";
import { CustomFormSelect } from "@/components/inputs/CustomFormSelect";
import { CustomTextField } from "@/components/inputs/CustomTextField";
import { CustomLabel } from "@/components/labels/CustomLabel";
import { displayAdditionalPlatform } from "@/libs/administrator/platform";
import { displayTenantStatus } from "@/libs/administrator/tenantStatus";
import { getPdfParserLabel } from "@/libs/bot";
import {
  AdditionalPlatform,
  Tenant,
  TenantStatus,
  UpdateTenantParam,
} from "@/orval/models/administrator-api";
import { PdfParser } from "@/orval/models/backend-api";

type Props = {
  tenant: Tenant;
  handleUpdateTenant: (params: UpdateTenantParam) => Promise<void>;
  onClose: () => void;
};

export const UpdateBasicInfoForm = ({ tenant, handleUpdateTenant, onClose }: Props) => {
  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
    setValue,
    watch,
  } = useForm<Tenant>({
    defaultValues: tenant,
  });

  const enableDocumentIntelligence = watch("enable_document_intelligence");
  const allowedIps = watch("allowed_ips");

  const onSubmit = async ({
    name,
    status,
    allowed_ips,
    is_sensitive_masked,
    allow_foreign_region,
    additional_platforms,
    enable_document_intelligence,
    enable_url_scraping,
    enable_llm_document_reader,
    usage_limit,
    enable_api_integrations,
    enable_basic_ai_web_browsing,
    basic_ai_pdf_parser,
    max_attachment_token,
    enable_external_data_integrations,
  }: Tenant) => {
    const newEnableLLMDocumentReader = enable_document_intelligence
      ? enable_llm_document_reader
      : false;
    await handleUpdateTenant({
      name,
      status,
      allowed_ips,
      is_sensitive_masked,
      allow_foreign_region,
      additional_platforms,
      enable_document_intelligence,
      enable_url_scraping,
      enable_llm_document_reader: newEnableLLMDocumentReader,
      usage_limit,
      enable_api_integrations,
      enable_basic_ai_web_browsing,
      basic_ai_pdf_parser,
      max_attachment_token,
      enable_external_data_integrations,
    });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <CustomDialogContent>
        <Stack gap={2}>
          <CustomTextField
            fullWidth
            name="name"
            type="text"
            control={control}
            label="テナント名"
            rules={{ required: "テナント名は必須です" }}
          />
          <CustomTextField
            fullWidth
            name="alias"
            type="text"
            control={control}
            label="エイリアス（編集不可）"
            rules={{ required: "エイリアスは必須です" }}
            disabled
          />
          <CustomTextField
            fullWidth
            name="index_name"
            type="text"
            control={control}
            label="インデックス名（編集不可）"
            rules={{ required: "エイリアスは必須です" }}
            disabled
          />
          <CustomFormSelect
            name="status"
            label="ステータス"
            control={control}
            rules={{ required: "ステータスは必須です" }}
          >
            {Object.entries(TenantStatus).map(([key, value]) => (
              <MenuItem key={key} value={value}>
                {displayTenantStatus(value)}
              </MenuItem>
            ))}
          </CustomFormSelect>

          <Box>
            <CustomLabel label="海外リージョン" />
            <Stack direction="row" alignItems="center" gap={2}>
              <Typography variant="subtitle2">海外リージョンを許可する</Typography>
              <Controller
                name="allow_foreign_region"
                control={control}
                render={({ field }) => (
                  <Switch
                    checked={field.value}
                    onChange={() => {
                      setValue("allow_foreign_region", !field.value);
                    }}
                  />
                )}
              />
            </Stack>
          </Box>

          <Box>
            <CustomFormSelect
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

          <Box>
            <CustomLabel label={getPdfParserLabel(PdfParser.document_intelligence)} />
            <Stack direction="row" alignItems="center" gap={2}>
              <Typography variant="subtitle2">
                {getPdfParserLabel(PdfParser.document_intelligence)}機能をオンにする
              </Typography>
              <Controller
                name="enable_document_intelligence"
                control={control}
                render={({ field }) => (
                  <Switch
                    checked={field.value}
                    onChange={() => {
                      setValue("enable_document_intelligence", !field.value);
                      !field.value && setValue("enable_llm_document_reader", false);
                    }}
                  />
                )}
              />
            </Stack>
          </Box>
          {enableDocumentIntelligence && (
            <Box>
              <CustomLabel label={getPdfParserLabel(PdfParser.llm_document_reader)} />
              <Stack direction="row" alignItems="center" gap={2}>
                <Typography variant="subtitle2">
                  {getPdfParserLabel(PdfParser.llm_document_reader)}機能をオンにする
                </Typography>
                <Controller
                  name="enable_llm_document_reader"
                  control={control}
                  render={({ field }) => (
                    <Switch
                      checked={field.value}
                      onChange={() => {
                        setValue("enable_llm_document_reader", !field.value);
                      }}
                    />
                  )}
                />
              </Stack>
            </Box>
          )}

          <Box>
            <CustomLabel label="API連携" />
            <Stack direction="row" alignItems="center" gap={2}>
              <Typography variant="subtitle2">API連携機能をオンにする</Typography>
              <Controller
                name="enable_api_integrations"
                control={control}
                render={({ field }) => (
                  <Switch
                    checked={field.value}
                    onChange={() => {
                      setValue("enable_api_integrations", !field.value);
                    }}
                  />
                )}
              />
            </Stack>
          </Box>

          <Box>
            <CustomLabel label="URLスクレイピング" />
            <Stack direction="row" alignItems="center" gap={2}>
              <Typography variant="subtitle2">URLスクレイピングをオンにする</Typography>
              <Controller
                name="enable_url_scraping"
                control={control}
                render={({ field }) => (
                  <Switch
                    checked={field.value}
                    onChange={() => {
                      setValue("enable_url_scraping", !field.value);
                    }}
                  />
                )}
              />
            </Stack>
          </Box>

          <Box>
            <CustomLabel label="個人情報検出" />
            <Stack direction="row" alignItems="center" gap={2}>
              <Typography variant="subtitle2">個人情報検出機能をオンにする</Typography>
              <Controller
                name="is_sensitive_masked"
                control={control}
                render={({ field }) => (
                  <Switch
                    checked={field.value}
                    onChange={() => {
                      setValue("is_sensitive_masked", !field.value);
                    }}
                  />
                )}
              />
            </Stack>
          </Box>

          <Box>
            <CustomLabel label="外部データ連携" />
            <Stack direction="row" alignItems="center" gap={2}>
              <Typography variant="subtitle2">外部データ連携機能をオンにする</Typography>
              <Controller
                name="enable_external_data_integrations"
                control={control}
                render={({ field }) => (
                  <Switch
                    checked={field.value}
                    onChange={() => {
                      setValue("enable_external_data_integrations", !field.value);
                    }}
                  />
                )}
              />
            </Stack>
          </Box>

          <Stack gap={allowedIps.length === 0 ? 0 : 2}>
            <Box>
              <CustomLabel label="許可IPアドレス" />
              <Stack gap={1}>
                {allowedIps.map((allowedIp, index) => (
                  <Stack direction="row" key={index} gap={2}>
                    <TextField
                      fullWidth
                      name={`allowed_ips.${index}`}
                      type="text"
                      size="small"
                      value={allowedIp}
                      onChange={e => {
                        const newAllowedIps = allowedIps.map((ip, i) =>
                          i === index ? e.target.value : ip,
                        );
                        setValue("allowed_ips", newAllowedIps);
                      }}
                    />
                    <Button
                      variant="contained"
                      color="error"
                      onClick={() => {
                        const newAllowedIps = allowedIps.filter((_, i) => i !== index);
                        setValue("allowed_ips", newAllowedIps);
                      }}
                    >
                      削除
                    </Button>
                  </Stack>
                ))}
              </Stack>
            </Box>
            <Button
              variant="outlined"
              color="primary"
              onClick={() => {
                setValue("allowed_ips", [...allowedIps, ""]);
              }}
              startIcon={<AddIcon />}
              sx={{
                width: "fit-content",
              }}
            >
              追加
            </Button>
          </Stack>
        </Stack>
      </CustomDialogContent>
      <CustomDialogAction onClose={onClose} buttonText="保存" loading={isSubmitting} />
    </form>
  );
};
