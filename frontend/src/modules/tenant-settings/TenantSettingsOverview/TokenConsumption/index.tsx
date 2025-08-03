import { Paper, Skeleton, Stack, Typography } from "@mui/material";
import { BarChart } from "@mui/x-charts";
import dayjs from "dayjs";
import { FormProvider, useForm } from "react-hook-form";

import { RefreshButton } from "@/components/buttons/RefreshButton";
import { HorizontalStackBar } from "@/components/charts/HorizontalStackBar";
import { ContentHeader } from "@/components/headers/ContentHeader";
import { useCustomSnackbar } from "@/hooks/useCustomSnackbar";
import { getErrorMessage } from "@/libs/error";
import { useGetBots, useGetTenantTokenCount } from "@/orval/backend-api";
import { BotStatus, Tenant } from "@/orval/models/backend-api";
import {
  API_KEY_COLOR,
  PDF_PARSER_TOKEN_CONSUMPTION_COLOR,
  USER_TOKEN_CONSUMPTION_COLOR,
} from "@/theme";
import { numberToString } from "@/utils/formatNumber";
import { showOldPricingPlan } from "@/utils/isOldPricingPlan";

import { SelectDateAndBotForm, SelectDateAndBotFormParams } from "../SelectDateAndBotForm";

type Props = {
  tenant: Tenant;
  isLoadingGetTenant: boolean;
};

export const TokenConsumption = ({ tenant, isLoadingGetTenant }: Props) => {
  const { enqueueErrorSnackbar } = useCustomSnackbar();

  const { data, isLoading: isLoadingGetBots, error } = useGetBots({ status: [BotStatus.active] });

  const useFormMethods = useForm<SelectDateAndBotFormParams>({
    defaultValues: {
      botId: "all",
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
    bot_id: watch("botId") === "all" ? undefined : Number(watch("botId")),
    start_date_time: dayjs()
      .year(watch("year"))
      .month(watch("month") - 1)
      .startOf("month")
      .toISOString(),
    end_date_time: dayjs().year(watch("year")).month(watch("month")).startOf("month").toISOString(),
  });

  const bots = data?.bots ?? [];
  if (error) {
    const errMsg = getErrorMessage(error);
    enqueueErrorSnackbar({ message: errMsg || "アシスタントの取得に失敗しました。" });
  }

  const isOldPricingPlan = showOldPricingPlan(dayjs().year(watch("year")).month(watch("month")));

  const totalUsersCount = tokenCountData?.total_users_count ?? 0;
  const totalApiKeysCount = tokenCountData?.total_api_keys_count ?? 0;
  const totalPdfParsersCount = isOldPricingPlan ? 0 : tokenCountData?.total_pdf_parsers_count ?? 0;
  const totalTokenCount = totalUsersCount + totalApiKeysCount + totalPdfParsersCount;
  const totalTokenLimit = tenant.usage_limit.free_token + tenant.usage_limit.additional_token;
  const userTokenCountsTop10 = tokenCountData?.users_tokens?.slice(0, 10) ?? [];
  const apiTokenCountsTop10 = tokenCountData?.api_keys_tokens?.slice(0, 10) ?? [];
  const botPdfParserCountsTop10 = tokenCountData?.bot_pdf_parsers_tokens?.slice(0, 10) ?? [];
  if (getTenantTokenCountError) {
    const errMsg = getErrorMessage(getTenantTokenCountError);
    enqueueErrorSnackbar({ message: errMsg || "トークン数の取得に失敗しました。" });
  }

  const userTokenConsumptionPercent = (totalUsersCount / totalTokenLimit) * 100;
  const apiKeyTokenConsumptionPercent = (totalApiKeysCount / totalTokenLimit) * 100;
  const pdfParserTokenConsumptionPercent = (totalPdfParsersCount / totalTokenLimit) * 100;

  const chartTickMaxLength = 6;

  const tokenStackData = [
    {
      label: "ユーザーによる消費",
      percent: userTokenConsumptionPercent,
      color: USER_TOKEN_CONSUMPTION_COLOR,
    },
    {
      label: "API連携による消費",
      percent: apiKeyTokenConsumptionPercent,
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
          padding: 2,
          borderRadius: "0 0 4px 4px",
        }}
        variant="outlined"
      >
        <Stack gap={3}>
          <FormProvider {...useFormMethods}>
            <SelectDateAndBotForm
              disabled={isLoadingGetTenantTokenCount}
              isLoadingGetBots={isLoadingGetBots}
              bots={bots}
            />
          </FormProvider>
          <Stack gap={1}>
            {isLoadingGetTenant || isLoadingGetTenantTokenCount ? (
              <Skeleton animation="pulse" variant="text" width={100} height={24} />
            ) : (
              <Typography variant="body1" fontWeight="bold">
                {numberToString(totalTokenCount)} / {numberToString(totalTokenLimit)}{" "}
                <Typography component="span" variant="body2">
                  トークン
                </Typography>
              </Typography>
            )}
            {isLoadingGetTenant || isLoadingGetTenantTokenCount ? (
              <Skeleton animation="pulse" variant="text" width="100%" height={4} />
            ) : (
              <HorizontalStackBar data={tokenStackData} showTotal={true} />
            )}

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
                          return context.location === "tick" && value.length > chartTickMaxLength
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
                          return context.location === "tick" && value.length > chartTickMaxLength
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
                          return context.location === "tick" && value.length > chartTickMaxLength
                            ? `${value.slice(0, chartTickMaxLength)}...`
                            : value;
                        },
                      },
                    ]}
                  />
                )}
              </>
            )}
          </Stack>
        </Stack>
      </Paper>
    </>
  );
};
