import { Stack, Typography } from "@mui/material";

import { AssistantAvatar } from "@/components/icons/AssistantAvatar";
import { BotTemplate } from "@/orval/models/backend-api";

type Props = {
  botTemplate: BotTemplate;
  handleSelectBotTemplate: () => void;
};

export const AssistantTemplateCard = ({ botTemplate, handleSelectBotTemplate }: Props) => {
  return (
    <Stack
      sx={{
        height: 150,
        px: 2,
        cursor: "pointer",
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
          size={100}
          iconUrl={botTemplate.icon_url}
          iconColor={botTemplate.icon_color}
        />
        <Stack
          overflow="hidden"
          sx={{
            wordBreak: "break-word",
          }}
        >
          <Typography
            variant="h4"
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
            variant="body2"
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
