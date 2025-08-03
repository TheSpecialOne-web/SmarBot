import StarIcon from "@mui/icons-material/Star";
import StarBorderIcon from "@mui/icons-material/StarBorder";
import { IconButton, Stack, Typography } from "@mui/material";

import { AssistantAvatar } from "@/components/icons/AssistantAvatar";
import { BotWithLikedStatus } from "@/modules/assistants/search-bots/type";
import { Bot } from "@/orval/models/backend-api";

type Props = {
  assistant: BotWithLikedStatus;
  onClickIcon?: ({ bot, isLiked }: { bot: Bot; isLiked: boolean }) => void;
  onClickCard: (assistant: Bot) => void;
};

export const AssistantsSearchCard = ({ assistant, onClickIcon, onClickCard }: Props) => {
  const onClickStarIcon = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onClickIcon) onClickIcon({ bot: assistant, isLiked: !assistant.isLiked });
  };

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
      onClick={() => onClickCard(assistant)}
    >
      <IconButton
        edge="end"
        onClick={onClickStarIcon}
        sx={{
          padding: 0.5,
          position: "absolute",
          top: 0,
          right: 14,
        }}
      >
        {assistant.isLiked ? (
          <StarIcon fontSize="medium" sx={{ color: "gold" }} />
        ) : (
          <StarBorderIcon fontSize="medium" />
        )}
      </IconButton>
      <Stack direction="row" spacing={2} alignItems="center">
        <AssistantAvatar size={60} iconUrl={assistant.icon_url} iconColor={assistant.icon_color} />
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
            {assistant.name}
          </Typography>
          <Typography
            variant="body2"
            color="textSecondary"
            sx={{
              overflow: "hidden",
              display: "-webkit-box",
              WebkitBoxOrient: "vertical",
              WebkitLineClamp: 3,
            }}
          >
            {assistant.description}
          </Typography>
        </Stack>
      </Stack>
    </Stack>
  );
};
