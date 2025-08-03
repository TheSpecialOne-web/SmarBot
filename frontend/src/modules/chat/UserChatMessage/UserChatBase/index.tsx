import PersonIcon from "@mui/icons-material/Person";
import { Avatar, Box, Paper, Stack, Typography } from "@mui/material";
import { ReactNode } from "react";

import { Spacer } from "@/components/spacers/Spacer";
import { USER_AVATAR_ICON_COLOR } from "@/theme";

type Props = {
  children: ReactNode;
};

export const UserChatBase = ({ children }: Props) => {
  return (
    <Stack direction="row" sx={{ width: "100%" }}>
      <Box>
        <Spacer px={8} />
        <Avatar
          sx={{
            bgcolor: USER_AVATAR_ICON_COLOR,
            mr: 1,
            width: 24,
            height: 24,
            fontSize: "0.875rem",
          }}
        >
          <PersonIcon />
        </Avatar>
      </Box>
      <Box
        flex={1}
        sx={{
          width: `calc(100% - 40px)`,
        }}
      >
        <Typography variant="h6">あなた</Typography>
        <Paper
          sx={{
            width: "100%",
            px: 2,
            py: 1.5,
          }}
        >
          <Box
            sx={{
              whiteSpace: "pre-wrap",
              overflowWrap: "break-word",
            }}
          >
            {children}
          </Box>
        </Paper>
      </Box>
    </Stack>
  );
};
