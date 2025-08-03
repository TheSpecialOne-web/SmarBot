import { MenuItem, Skeleton, Stack, Typography } from "@mui/material";
import { useFormContext } from "react-hook-form";

import { CustomFormSelect } from "@/components/inputs/CustomFormSelect";
import { FIRST_YEAR } from "@/const";
import { Bot } from "@/orval/models/backend-api";

export type SelectDateAndBotFormParams = {
  year: number;
  month: number;
  botId: number | "all";
};

type Props = {
  isLoadingGetBots: boolean;
  disabled: boolean;
  bots: Bot[];
};

export const SelectDateAndBotForm = ({ isLoadingGetBots, disabled, bots }: Props) => {
  const { control } = useFormContext<SelectDateAndBotFormParams>();

  const currentYear = new Date().getFullYear();

  return (
    <Stack gap={2} direction="row" alignItems="center">
      <Stack gap={1} direction="row" alignItems="center">
        <CustomFormSelect
          name="year"
          control={control}
          disabled={disabled}
          sx={{
            minWidth: 90,
          }}
        >
          {Array.from({ length: currentYear - FIRST_YEAR + 1 }, (_, i) => (
            <MenuItem key={i} value={currentYear - i}>
              {currentYear - i}
            </MenuItem>
          ))}
        </CustomFormSelect>
        <Typography>年</Typography>
        <CustomFormSelect
          name="month"
          control={control}
          disabled={disabled}
          sx={{
            minWidth: 70,
          }}
        >
          {Array.from({ length: 12 }, (_, i) => (
            <MenuItem key={i} value={i + 1}>
              {i + 1}
            </MenuItem>
          ))}
        </CustomFormSelect>
        <Typography>月</Typography>
      </Stack>
      {isLoadingGetBots ? (
        <Skeleton animation="pulse" variant="text" width={290} height={40} />
      ) : (
        <CustomFormSelect
          name="botId"
          control={control}
          disabled={disabled}
          sx={{
            minWidth: 290,
          }}
        >
          <MenuItem value="all">全ての基盤モデルとアシスタント</MenuItem>
          {bots.map(bot => (
            <MenuItem key={bot.id} value={bot.id}>
              {bot.name}
            </MenuItem>
          ))}
        </CustomFormSelect>
      )}
    </Stack>
  );
};
