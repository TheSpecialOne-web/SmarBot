import { Paper, Skeleton, Stack, Typography } from "@mui/material";
import { BarChart } from "@mui/x-charts";
import dayjs from "dayjs";
import { FormProvider, useForm } from "react-hook-form";

import { RefreshButton } from "@/components/buttons/RefreshButton";
import { HorizontalStackBar } from "@/components/charts/HorizontalStackBar";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useGetTenantTokenCount } from "@/orval/administrator-api";
import { Tenant } from "@/orval/models/administrator-api";
import {
  API_KEY_COLOR,
  PDF_PARSER_TOKEN_CONSUMPTION_COLOR,
  USER_TOKEN_CONSUMPTION_COLOR,
} from "@/theme";
import { numberToString } from "@/utils/formatNumber";
import { showOldPricingPlan } from "@/utils/isOldPricingPlan";

import { SelectDateForm, SelectDateFormParams } from "../SelectDateForm";

type Props = {
  tenant: Tenant;
  isLoadingGetTenant: boolean;
};

export const TokenConsumption = ({ tenant, isLoadingGetTenant }: Props) => {
  const { enqueueErrorSnackbar } = useCustomSnackbar();

  const useFormMethods = useForm<SelectDateFormParams>({
    defaultValues: {
      year: new Date().getFullYear(),
      month: new Date().getMonth() + 1,
    },
  });
  const { watch } = useFormMethods;

  const {
    data: tokenCountData,
    isValidating: isLoadingGetTenantTokenCount,
    mutate: fetchTenantTokenCount,
    error: getTenantTokenCountError,
  } = useGetTenantTokenCount(tenant.id, {
    start_date_time: dayjs()
      .year(watch("year"))
      .month(watch("month") - 1)
      .startOf("month")
      .toISOString(),
    end_date_time: dayjs().year(watch("year")).month(watch("month")).startOf("month").toISOString(),
  });

  const isOldPricingPlan = showOldPricingPlan(dayjs().year(watch("year")).month(watch("month")));

  const totalUsersCount = tokenCountData?.total_users_count ?? 0;
  const totalApiKeysCount = tokenCountData?.total_api_keys_count ?? 0;
  const totalPdfParsersCount = isOldPricingPlan ? 0 : tokenCountData?.total_pdf_parsers_count ?? 0;
  const totalTokenCount = totalUsersCount + totalApiKeysCount + totalPdfParsersCount;
  const userTokenCountsTop10 = tokenCountData?.users_tokens?.slice(0, 10) ?? [];
  const apiTokenCountsTop10 = tokenCountData?.api_keys_tokens?.slice(0, 10) ?? [];
  const botPdfParserCountsTop10 = tokenCountData?.bot_pdf_parsers_tokens?.slice(0, 10) ?? [];
  if (getTenantTokenCountError) {
    const errMsg = getErrorMessage(getTenantTokenCountError);
    enqueueErrorSnackbar({ message: errMsg || "トークン数の取得に失敗しました。" });
  }

  const freeTokenLimit = tenant.usage_limit.free_token;
  const additionalTokenLimit = tenant.usage_limit.additional_token;
  const totalTokenLimit = freeTokenLimit + additionalTokenLimit;
  const usetTokenConsumptionPercent = (totalUsersCount / totalTokenLimit) * 100;
  const apiTokenConsumptionPercent = (totalApiKeysCount / totalTokenLimit) * 100;
  const pdfParserTokenConsumptionPercent = (totalPdfParsersCount / totalTokenLimit) * 100;

  const chartTickMaxLength = 6;

  const tokenStackData = [
    {
      label: "ユーザーによる消費",
      percent: usetTokenConsumptionPercent,
      color: USER_TOKEN_CONSUMPTION_COLOR,
    },
    {
      label: "API連携による消費",
      percent: apiTokenConsumptionPercent,
      color: API_KEY_COLOR,
    },
    ...(isOldPricingPlan
      ? []
      : [
          {
            label: "ドキュメント読み取りオプションによる消費",
            percent: pdfParserTokenConsumptionPercent,
            color: PDF_PARSER_TOKEN_CONSUMPTION_COLOR,
          },
        ]),
  ];

  return (
    <>
      <ContentHeader>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h4">消費トークン数</Typography>
          <RefreshButton onClick={fetchTenantTokenCount} />
        </Stack>
      </ContentHeader>
      <Paper
        sx={{
          p: 2,
          borderRadius: "0 0 4px 4px",
        }}
        variant="outlined"
      >
        <Stack gap={3}>
          <FormProvider {...useFormMethods}>
            <SelectDateForm disabled={isLoadingGetTenantTokenCount} />
          </FormProvider>
          <Stack gap={1}>
            {isLoadingGetTenant || isLoadingGetTenantTokenCount ? (
              <>
                <Skeleton animation="pulse" variant="text" width={100} height={24} />
                <Skeleton animation="pulse" variant="text" width="100%" height={4} />
              </>
            ) : (
              <>
                <Typography fontWeight="bold">
                  {numberToString(totalTokenCount)} / {numberToString(totalTokenLimit)}{" "}
                  <Typography component="span" fontSize="small" fontWeight="bold">
                    トークン
                  </Typography>
                  <Typography>
                    (無料枠: {numberToString(freeTokenLimit)} + 追加購入:{" "}
                    {numberToString(additionalTokenLimit)})
                  </Typography>
                </Typography>
                <HorizontalStackBar data={tokenStackData} showTotal={true} />
                {isLoadingGetTenant || isLoadingGetTenantTokenCount ? (
                  <Skeleton animation="pulse" variant="rounded" width="100%" height={72} />
                ) : (
                  <>
                    {totalUsersCount > 0 && (
                      <BarChart
                        height={300}
                        colors={[USER_TOKEN_CONSUMPTION_COLOR]}
                        margin={{ left: 75 }}
                        series={[{ data: userTokenCountsTop10.map(v => v.count) }]}
                        xAxis={[
                          {
                            data: userTokenCountsTop10.map(v => v.user_name),
                            scaleType: "band",
                            valueFormatter: (value: string, context) => {
                              return context.location === "tick" &&
                                value.length > chartTickMaxLength
                                ? `${value.slice(0, chartTickMaxLength)}...`
                                : value;
                            },
                          },
                        ]}
                      />
                    )}
                    {totalApiKeysCount > 0 && (
                      <BarChart
                        height={300}
                        colors={[API_KEY_COLOR]}
                        margin={{ left: 75 }}
                        series={[{ data: apiTokenCountsTop10.map(v => v.count) }]}
                        xAxis={[
                          {
                            data: apiTokenCountsTop10.map(v => v.name),
                            scaleType: "band",
                            valueFormatter: (value: string, context) => {
                              return context.location === "tick" &&
                                value.length > chartTickMaxLength
                                ? `${value.slice(0, chartTickMaxLength)}...`
                                : value;
                            },
                          },
                        ]}
                      />
                    )}
                    {!isOldPricingPlan && totalPdfParsersCount > 0 && (
                      <BarChart
                        height={300}
                        colors={[PDF_PARSER_TOKEN_CONSUMPTION_COLOR]}
                        margin={{ left: 75 }}
                        series={[{ data: botPdfParserCountsTop10.map(v => v.count) }]}
                        xAxis={[
                          {
                            data: botPdfParserCountsTop10.map(v => v.bot_name),
                            scaleType: "band",
                            valueFormatter: (value: string, context) => {
                              return context.location === "tick" &&
                                value.length > chartTickMaxLength
                                ? `${value.slice(0, chartTickMaxLength)}...`
                                : value;
                            },
                          },
                        ]}
                      />
                    )}
                  </>
                )}
              </>
            )}
          </Stack>
        </Stack>
      </Paper>
    </>
  );
};
