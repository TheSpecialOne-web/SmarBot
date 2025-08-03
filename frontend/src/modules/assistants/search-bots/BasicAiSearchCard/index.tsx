import { Box, Rating, Stack, Typography } from "@mui/material";

import { BasicAiAvater } from "@/components/icons/BasicAiAvatar";
import { Text2ImageAvater } from "@/components/icons/Text2ImageAvater";
import { LEGACY_MODEL_FAMILIES, modelFamilyDetails } from "@/const/modelFamily";
import { getBaseModelColor } from "@/libs/bot";
import { Bot } from "@/orval/models/backend-api";

type Props = {
  bot: Bot;
  onClickCard: (assistant: Bot) => void;
};

export const BasicAiSearchCard = ({ bot, onClickCard }: Props) => {
  const AvatarComponent = bot.approach === "text_2_image" ? Text2ImageAvater : BasicAiAvater;
  const modelFamilyDetail = modelFamilyDetails
    .filter(mf => !(LEGACY_MODEL_FAMILIES as string[]).includes(mf.id))
    .find(mf => mf.id === bot.model_family);

  return (
    <Stack
      sx={{
        height: 120,
        px: 2,
        cursor: "pointer",
        justifyContent: "center",
        backgroundColor: "background.default",
        borderRadius: 2,
        "&:hover": {
          backgroundColor: "action.hover",
        },
        position: "relative",
      }}
      onClick={() => onClickCard(bot)}
    >
      <Stack direction="row" spacing={2} alignItems="center">
        <AvatarComponent size={60} bgColor={getBaseModelColor(bot.model_family)} />
        <Stack
          overflow="hidden"
          sx={{
            wordBreak: "break-word",
          }}
        >
          <Typography
            variant="h5"
            sx={{
              overflow: "hidden",
              display: "-webkit-box",
              WebkitBoxOrient: "vertical",
              WebkitLineClamp: 1,
              mb: 0.5,
            }}
          >
            {bot.name}
          </Typography>
          <Box pl={1}>
            {bot.approach === "text_2_image" ? (
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography variant="body2" color="textSecondary">
                  消費トークン :
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  {
                    modelFamilyDetails.find(mf => mf.id === bot.text2image_model_family)
                      ?.tokenConsumption
                  }
                </Typography>
              </Stack>
            ) : (
              <>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Typography variant="body2" color="textSecondary">
                    精度 :
                  </Typography>
                  <Rating
                    value={modelFamilyDetail?.accuracy}
                    precision={0.5}
                    max={3}
                    readOnly
                    size="small"
                  />
                </Stack>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Typography variant="body2" color="textSecondary">
                    速さ :
                  </Typography>
                  <Rating
                    value={modelFamilyDetail?.speed}
                    precision={0.5}
                    max={3}
                    readOnly
                    size="small"
                  />
                </Stack>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Typography variant="body2" color="textSecondary">
                    消費トークン :
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    {modelFamilyDetail?.tokenConsumption}
                  </Typography>
                </Stack>
              </>
            )}
          </Box>
        </Stack>
      </Stack>
    </Stack>
  );
};
