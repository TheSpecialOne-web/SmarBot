import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import { Stack, Typography } from "@mui/material";

import { Spacer } from "@/components/spacers/Spacer";
import { getPdfParserLabel } from "@/libs/bot";
import { Approach, Bot } from "@/orval/models/backend-api";

type Props = {
  bot: Bot;
};

export const AssistantsTableApproachColumn = ({ bot }: Props) => {
  return bot.approach == Approach.neollm ? (
    <Stack direction="row" alignItems="center">
      <CheckIcon color="success" />
      <Spacer px={8} horizontal />
      <Typography variant="body2">({getPdfParserLabel(bot.pdf_parser)})</Typography>
    </Stack>
  ) : (
    <CloseIcon color="error" />
  );
};
