import { Box, Typography } from "@mui/material";

export const ServiceUnavailableMessage = () => {
  return (
    <Box sx={{ textAlign: "center" }}>
      <Typography variant="h1">当サービスは現在ご利用期間外です。</Typography>
      <Typography>ご不明点などありましたら、組織管理者までお問い合わせください。</Typography>
    </Box>
  );
};
