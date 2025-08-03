import { Grid, Paper, Stack, Typography } from "@mui/material";
import { Fragment } from "react";

import { PrimaryButton } from "@/components/buttons/PrimaryButton";
import { RefreshButton } from "@/components/buttons/RefreshButton";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { CircularLoading } from "@/components/loadings/CircularLoading";
import { useDisclosure } from "@/hooks/useDisclosure";
import { displayAdditionalPlatform } from "@/libs/administrator/platform";
import { displayTenantStatus } from "@/libs/administrator/tenantStatus";
import { getPdfParserLabel } from "@/libs/bot";
import { UpdateBasicInfoDialog } from "@/modules/administrator/tenants/UpdateBasicInfoDialog";
import { Tenant } from "@/orval/models/administrator-api";
import { PdfParser } from "@/orval/models/backend-api";

import { BasicInfoItem } from "./Item";

type Props = {
  tenant: Tenant;
  refetch: () => void;
  isLoading: boolean;
};

export const TenantBasicInfo = ({ tenant, refetch, isLoading }: Props) => {
  const {
    isOpen: isOpenUpdateTenantDialog,
    open: openUpdateTenantDialog,
    close: closeUpdateTenantDialog,
  } = useDisclosure({});

  const infoItems = [
    { title: "テナントID", content: tenant.id },
    { title: "テナント名", content: tenant.name },
    {
      title: "インデックス名",
      content: `${tenant.index_name}（${
        // Azure AI Searchのサービス名を取得
        tenant.search_service_endpoint?.replace("https://", "").replace(".search.windows.net", "")
      }）`,
    },
    { title: "コンテナ名", content: tenant.container_name },
    { title: "エイリアス", content: tenant.alias },
    { title: "ステータス", content: displayTenantStatus(tenant.status) },
    {
      title: "海外リージョン",
      content: tenant.allow_foreign_region ? "有効" : "無効",
    },
    {
      title: "追加のプラットフォーム",
      content: tenant.additional_platforms
        ?.map(platform => displayAdditionalPlatform(platform))
        .join(", "),
    },
    {
      title: getPdfParserLabel(PdfParser.document_intelligence),
      content: tenant.enable_document_intelligence ? "有効" : "無効",
    },
    {
      title: getPdfParserLabel(PdfParser.llm_document_reader),
      content: tenant.enable_llm_document_reader ? "有効" : "無効",
    },
    {
      title: "API連携",
      content: tenant.enable_api_integrations ? "有効" : "無効",
    },
    {
      title: "URLスクレイピング",
      content: tenant.enable_url_scraping ? "有効" : "無効",
    },
    {
      title: "個人情報保護",
      content: tenant.is_sensitive_masked ? "有効" : "無効",
    },
    {
      title: "外部データ連携",
      content: tenant.enable_external_data_integrations ? "有効" : "無効",
    },
    {
      title: "許可されたIPアドレス",
      content: tenant.allowed_ips?.map(ip => (
        <Fragment key={ip}>
          {ip}
          <br />
        </Fragment>
      )),
    },
  ];

  return (
    <>
      <ContentHeader>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h4">基本情報</Typography>
          <Stack direction="row" gap={2}>
            <PrimaryButton text="編集" onClick={openUpdateTenantDialog} />
            <RefreshButton onClick={refetch} />
          </Stack>
        </Stack>
      </ContentHeader>
      <Paper
        sx={{
          p: 2,
          borderRadius: "4px",
        }}
        variant="outlined"
      >
        {isLoading ? (
          <CircularLoading />
        ) : (
          <Grid container spacing={2}>
            {infoItems.map(item => (
              <BasicInfoItem key={item.title} title={item.title} content={item.content} />
            ))}
          </Grid>
        )}
      </Paper>
      <UpdateBasicInfoDialog
        tenant={tenant}
        open={isOpenUpdateTenantDialog}
        onClose={closeUpdateTenantDialog}
        refetch={refetch}
      />
    </>
  );
};
