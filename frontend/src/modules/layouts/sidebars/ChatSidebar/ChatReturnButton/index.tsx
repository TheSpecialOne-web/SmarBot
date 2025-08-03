import ChevronLeftRoundedIcon from "@mui/icons-material/ChevronLeftRounded";
import { Button, ButtonProps, Link, styled } from "@mui/material";
import { useNavigate } from "react-router-dom";

import { Bot } from "@/orval/models/backend-api";
import { theme } from "@/theme";

import { SelectedBotDisplay } from "../SelectedBotDisplay";

const StyledButton = styled(Button)<ButtonProps>(() => ({
  fontWeight: "bold",
  fontSize: "16px",
  ":hover": {
    backgroundColor: theme.palette.onHover.main,
  },
  padding: "12px",
  height: "48px",
  justifyContent: "space-between",
}));

type Props = {
  bot: Bot;
};

export const ChatReturnButton = ({ bot }: Props) => {
  const navigate = useNavigate();
  return (
    <StyledButton
      onClick={() => navigate(-1)}
      component={Link}
      color="inherit"
      endIcon={
        <ChevronLeftRoundedIcon
          color="action"
          sx={{
            "&&": {
              fontSize: 25,
              marginLeft: -1,
            },
          }}
        />
      }
      fullWidth
    >
      <SelectedBotDisplay bot={bot} />
    </StyledButton>
  );
};
