import { Box } from "@mui/material";
import { Outlet } from "react-router-dom";

import { LoginHeader } from "@/modules/layouts/headers/LoginHeader";

export const LoginLayout = () => {
  return (
    <Box
      sx={{
        display: "flex",
        height: 1,
      }}
    >
      <Box sx={{ width: 1 }}>
        <LoginHeader />
        <Box
          sx={{
            display: "flex", // Enables flexbox
            justifyContent: "center", // Centers horizontally
            alignItems: "center", // Centers vertically
            height: 1, // Full view height
            width: 1, // Full view width
          }}
        >
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
};
