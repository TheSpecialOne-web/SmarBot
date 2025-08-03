import { Stack, Typography } from "@mui/material";

import { AssistantAvatar } from "@/components/icons/AssistantAvatar";
import { BotTemplate } from "@/orval/models/administrator-api";

type Props = {
  botTemplate: BotTemplate;
  handleSelectBotTemplate: () => void;
};

export const BotTemplateCard = ({ botTemplate, handleSelectBotTemplate }: Props) => {
  return (
    <Stack
      sx={{
        height: 100,
        px: 2,
        cursor: "pointer",
        border: "1px solid",
        borderColor: "divider",
        justifyContent: "center",
        backgroundColor: "background.default",
        borderRadius: 2,
        "&:hover": {
          backgroundColor: "action.hover",
        },
      }}
      onClick={handleSelectBotTemplate}
    >
      <Stack direction="row" spacing={2}>
        <AssistantAvatar
          size={80}
          iconUrl={botTemplate.icon_url}
          iconColor={botTemplate.icon_color}
        />
        <Stack>
          <Typography
            variant="h6"
            sx={{
              overflow: "hidden",
              display: "-webkit-box",
              WebkitBoxOrient: "vertical",
              WebkitLineClamp: 1,
            }}
          >
            {botTemplate.name}
          </Typography>
          <Typography
            variant="caption"
            color="secondary"
            sx={{
              overflow: "hidden",
              display: "-webkit-box",
              WebkitBoxOrient: "vertical",
              WebkitLineClamp: 3,
            }}
          >
            {botTemplate.description}
          </Typography>
        </Stack>
      </Stack>
    </Stack>
  );
};
