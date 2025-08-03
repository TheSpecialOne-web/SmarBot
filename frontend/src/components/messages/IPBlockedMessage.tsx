import { Box, Typography } from "@mui/material";

export const IPBlockedMessage = () => {
  return (
    <Box sx={{ textAlign: "center" }}>
      <Typography variant="h1">IPアドレスによりアクセスが制限されています</Typography>
      <Typography>
        ご利用中のIPアドレスはアクセス制限の対象となっています。
        <br />
        問題が解決しない場合は、組織管理者までお問い合わせください。
      </Typography>
    </Box>
  );
};
